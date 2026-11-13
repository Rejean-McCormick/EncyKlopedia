#!/usr/bin/env python3
"""Inventaire et qualification multibranche V31, sur les index Wikipedia existants.

Le moteur lit wiki_pages et wiki_categorylinks (jamais le dump XML au hasard).
Il conserve TOUS les articles ns=0, même les redirections et les non classés.
Les associations proposées NE SONT NI des affectations v25 NI des décisions v28.
Traitement par plages de page_id, mémoire bornée et reprise sur curseur.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib
import json
import re
import sqlite3
import unicodedata
from pathlib import Path

SCHEMA='encyklopedia.global-multibranch-v31/2'
DEFAULT_SOURCE=Path(r'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite')
DEFAULT_OUT=Path(r'D:\EncyKlopedia\30_working\qualification_multibranche_v31\qualification_multibranche_v31.sqlite')
DEFAULT_BRANCH_DIR=Path(__file__).resolve().parent/'v25_data'
STOP={'of','the','and','in','on','at','by','to','from','for','a','an','or','with','about','et','des','les','une','de','du','la','le','en','un','sur','au','aux','pour','dans'}
NOISE=('wikipedia ','articles ','pages ','cs1 ','use ','commons ','all articles ','wikidata ','short description','maintenance ','template ','citation ')
KIND_KEYS={
 'LIEU':('cities','towns','municipalities','villages','settlements','geography','counties','city','county','province','territories'),
 'PERSONNE':('births','deaths','people','scientists','politicians','writers','educators','philosophers','biographies'),
 'INSTITUTION':('universities','colleges','schools','institutes','ministries','organizations','organisations','departments'),
 'EVENEMENT':('wars','events','revolutions','elections','conflicts','movements'),
 'METHODE':('methods','pedagogy','instruction','learning','techniques','approaches'),
 'OEUVRE':('novels','films','books','poetry','literature','albums'),
 'SCIENCE':('physics','chemistry','biology','mathematics','medicine','astronomy'),
}

def normal(text):
    x=unicodedata.normalize('NFKD',str(text or '')).encode('ascii','ignore').decode('ascii').lower()
    return re.sub(r'[^a-z0-9]+',' ',x).strip()

def root(term):
    """Normalisation morphologique conservative, indépendante de tout modèle externe."""
    if term.startswith('educat'): return 'educat'
    if term.startswith('universit'): return 'universit'
    if term.startswith('school'): return 'school'
    if term.endswith('ies') and len(term)>5: return term[:-3]+'y'
    if term.endswith('s') and len(term)>5 and not term.endswith(('ss','us','is')): return term[:-1]
    return term

def tokens(text):return {root(t) for t in normal(text).split() if len(t)>2 and t not in STOP}

def signature(path):
    s=path.stat()
    return hashlib.sha256(json.dumps({'path':str(path.resolve()),'size':s.st_size,'mtime_ns':s.st_mtime_ns},sort_keys=True).encode()).hexdigest()

def now():return datetime.now(timezone.utc).isoformat(timespec='seconds')

def definitions(directory):
    """Lire les manifestes natifs, jamais inventer une branche absente."""
    paths=sorted(directory.rglob('branche_*.json')) if directory.is_dir() else []
    if not paths:raise ValueError('Aucun manifeste branche_*.json présent : '+str(directory))
    result={}
    for p in paths:
        m=json.loads(p.read_text(encoding='utf-8-sig'))
        if m.get('schema')!='encyklopedia.branch-manifest.v25/1':continue
        bid=m.get('branch_id');rel=m.get('concepts_file')
        if not isinstance(bid,str) or not bid or not isinstance(rel,str) or not rel or '..' in Path(rel).parts or Path(rel).is_absolute():
            raise ValueError('Manifeste non conforme : '+str(p))
        source=p.parent/rel
        data=json.loads(source.read_text(encoding='utf-8-sig'))
        if not isinstance(data.get('concepts'),list):raise ValueError('Concepts absents : '+str(source))
        if bid in result:raise ValueError('Branche doublonnée : '+bid)
        terms=set(tokens(m.get('title_fr','')))
        concept_terms={}
        for c in data['concepts']:
            cid=c.get('unesco_id')
            if not isinstance(cid,str):raise ValueError('Identifiant concept absent')
            labels=[]
            for k in ('preferred_labels','prefLabel','label_en','label_fr','titre_en','titre_fr'):
                v=c.get(k)
                if isinstance(v,str):labels.append(v)
                if isinstance(v,list):labels.extend(str(x) for x in v if isinstance(x,str))
                if isinstance(v,dict):
                    for item in v.values():
                        if isinstance(item,str):labels.append(item)
                        elif isinstance(item,list):labels.extend(str(x) for x in item if isinstance(x,str))
            # Standard v25 keeps multilingual labels in the `pref_label` field.
            v=c.get('pref_label') or c.get('pref_labels') or c.get('labels')
            if isinstance(v,dict):labels.extend(str(x) for x in v.values() if isinstance(x,str))
            concept_terms[cid]=tokens(' '.join(labels))
            terms.update(concept_terms[cid])
        # Les QID du crosswalk restent des indices PROVISOIRES, jamais des APPROVE.
        qids={}
        crosswalk_bytes=b''
        cross_rel=m.get('crosswalk_file')
        if isinstance(cross_rel,str) and cross_rel and not Path(cross_rel).is_absolute() and '..' not in Path(cross_rel).parts:
            cross_path=p.parent/cross_rel
            if cross_path.is_file():
                crosswalk_bytes=cross_path.read_bytes()
                cross=json.loads(crosswalk_bytes.decode('utf-8-sig'))
                import re as _re
                for item in cross.get('mappings',[]):
                    ext=item.get('external_ref') or {}
                    mat=_re.fullmatch(r'wd-p3916-(concept\d+)',str(item.get('mapping_id','')))
                    if (mat and mat.group(1) in concept_terms and item.get('status')=='candidate'
                            and ext.get('system')=='wikidata' and _re.fullmatch(r'Q[1-9]\d*',str(ext.get('id','')))):
                        qids.setdefault(ext['id'],set()).add(mat.group(1))
        result[bid]={'qids':qids,'manifest':str(p),'branch_signature':hashlib.sha256(p.read_bytes()+source.read_bytes()+crosswalk_bytes).hexdigest(),
                     'vocabulary':m.get('vocabulary','unesco'),'title':m.get('title_fr',bid),
                     'concepts':concept_terms,'terms':terms}
    if not result:raise ValueError('Aucun manifeste branche v25 valide')
    return result

def classify(title,categories,branches,links=(),qid=None):
    title_words=tokens(title)
    categories_clean=[normal(x) for x in categories if not normal(x).startswith(NOISE)]
    category_words=tokens(' '.join(categories_clean))
    link_words=tokens(' '.join(links))
    kind_counts=Counter({kind:sum(any(k in c for k in keys) for c in categories_clean) for kind,keys in KIND_KEYS.items()})
    kind=kind_counts.most_common(1)[0][0] if kind_counts and kind_counts.most_common(1)[0][1] else 'INDETERMINE'
    results=[]
    for bid,branch in branches.items():
        top=[]
        for cid,cterms in branch['concepts'].items():
            if not cterms:continue
            match_title=len(cterms & title_words)
            match_cat=len(cterms & category_words)
            match_link=len(cterms & link_words)
            linked_qid=bool(qid and cid in branch.get('qids',{}).get(qid,set()))
            if not match_title and not match_cat and match_link<2 and not linked_qid:continue
            # Le lien QID est une correspondance lexicale supervisable, pas une preuve de contenu.
            # Les liens sortants seuls n'induisent qu'un score faible.
            score=min(95, 18*match_title+7*min(5,match_cat)+2*min(4,match_link)
                      +7*bool(match_title and match_cat)+75*linked_qid)
            # Réduire l'ambiguïté lorsque le texte du titre est exclusivement géographique.
            if kind=='LIEU' and not match_title and not linked_qid:score=min(score,22)
            top.append((score,cid,match_title,match_cat,match_link,linked_qid))
        if not top:continue
        top.sort(reverse=True)
        sc,cid,tm,cm,lm,linked_qid=top[0]
        results.append({'branch_id':bid,'score':sc,'concept_id_suggested':cid,
                        'reason':f'titre_termes={tm};categories_termes={cm};liens_termes={lm};qid_associe={int(linked_qid)};classification_non_validee'})
    results.sort(key=lambda x:(-x['score'],x['branch_id']))
    return kind,results

def connect_ro(path):
    if not path.is_file():raise ValueError('Index Wikipédia absent : '+str(path))
    c=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=30)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA query_only=ON')
    names={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not {'wiki_pages','wiki_categorylinks'}<=names:
        c.close();raise ValueError('Index sans wiki_pages / wiki_categorylinks')
    return c

def open_cache(path, source_sig, branch_sig):
    path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=30)
    db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA busy_timeout=30000')
    db.executescript('''
    CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS article_profiles(
      page_id INTEGER PRIMARY KEY,title TEXT NOT NULL,revision_id INTEGER,
      redirect INTEGER NOT NULL,kind TEXT NOT NULL,branch_candidates INTEGER NOT NULL,
      processed_utc TEXT NOT NULL,qid TEXT,categories_vues INTEGER NOT NULL DEFAULT 0,
      liens_vus INTEGER NOT NULL DEFAULT 0,indices_json TEXT NOT NULL DEFAULT '{}');
    CREATE TABLE IF NOT EXISTS branch_suggestions(
      page_id INTEGER NOT NULL,branch_id TEXT NOT NULL,score INTEGER NOT NULL,
      concept_id_suggested TEXT,reason TEXT NOT NULL,
      PRIMARY KEY(page_id,branch_id));
    CREATE INDEX IF NOT EXISTS idx_v31_branch_score ON branch_suggestions(branch_id,score DESC,page_id);
    ''')
    # Migration additive du cache V31, sans recopier l'inventaire.
    cols={r[1] for r in db.execute('PRAGMA table_info(article_profiles)')}
    for name,kind in [('qid','TEXT'),('categories_vues','INTEGER NOT NULL DEFAULT 0'),
                      ('liens_vus','INTEGER NOT NULL DEFAULT 0'),('indices_json',"TEXT NOT NULL DEFAULT '{}'")]:
        if name not in cols:db.execute(f'ALTER TABLE article_profiles ADD COLUMN {name} {kind}')
    for key,val in [('schema',SCHEMA),('source_signature',source_sig),('branch_signature',branch_sig)]:
        old=db.execute('SELECT value FROM meta WHERE key=?',(key,)).fetchone()
        if old and old[0]!=val and key=='source_signature':
            db.close();raise ValueError('Source Wikipédia modifiée : ouvrir un nouveau cache V31 pour cet instantané')
        if old and old[0]!=val and key=='schema' and old[0]!='encyklopedia.global-multibranch-v31/1':
            db.close();raise ValueError('Schema du cache V31 non reconnu')
        db.execute('INSERT OR IGNORE INTO meta VALUES(?,?)',(key,val))
    # Migration V31 -> V31.1 : les suggestions sont recalculées au prochain passage.
    old_schema=db.execute("SELECT value FROM meta WHERE key='schema'").fetchone()
    if old_schema and old_schema[0]!=SCHEMA:
        db.execute("UPDATE meta SET value=? WHERE key='schema'",(SCHEMA,))
        db.execute("INSERT OR REPLACE INTO meta VALUES('branch_signature','MIGRATION_V311_PENDING')")
    db.commit()
    return db

def reclassify_existing(db, branches, sig, chunk=1000):
    """Nouvelles branches: reclasser les profils conservés, sans relire l'index Wikipédia.

    Cette opération ne change que les hypothèses du cache V31. Elle n'atteint
    jamais les affectations vérifiées du catalogue ni les revues déjà figées.
    """
    old=db.execute("SELECT value FROM meta WHERE key='branch_signature'").fetchone()
    if old and old[0]==sig:return 0
    cursor=0;updated=0
    while True:
        rows=db.execute('SELECT page_id,title,qid,indices_json FROM article_profiles WHERE page_id>? '
                        'ORDER BY page_id LIMIT ?',(cursor,chunk)).fetchall()
        if not rows:break
        with db:
            for pid,title,qid,raw in rows:
                indices=json.loads(raw)
                if not isinstance(indices,dict) or 'cats' not in indices or 'links' not in indices:
                    raise ValueError('Profil sans indices conservés : requalification automatique impossible')
                kind,suggestions=classify(title,indices['cats'],branches,indices['links'],indices.get('qid') or qid)
                db.execute('UPDATE article_profiles SET kind=?,branch_candidates=? WHERE page_id=?',
                           (kind,len(suggestions),pid))
                db.execute('DELETE FROM branch_suggestions WHERE page_id=?',(pid,))
                for a in suggestions:
                    db.execute('INSERT INTO branch_suggestions VALUES(?,?,?,?,?)',
                               (pid,a['branch_id'],a['score'],a['concept_id_suggested'],a['reason']))
                updated+=1
            cursor=rows[-1][0]
    with db:db.execute('INSERT OR REPLACE INTO meta VALUES(?,?)',('branch_signature',sig))
    return updated

def execute(source,output,branches_dir,*,batch_size=2000,max_articles=2000,categories_limit=18):
    if batch_size<1 or batch_size>100000 or max_articles<1 or categories_limit<0 or categories_limit>50:
        raise ValueError('Paramètres hors bornes')
    branch=definitions(branches_dir)
    sig=hashlib.sha256(json.dumps({k:v['branch_signature'] for k,v in branch.items()},sort_keys=True).encode()).hexdigest()
    src=connect_ro(source)
    tables={x[0] for x in src.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    has_links={'wiki_pagelinks','wiki_linktargets'}<=tables
    has_qid='wiki_qid' in tables
    db=open_cache(output,signature(source),sig)
    counts=Counter()
    counts['reclassified_profiles']=reclassify_existing(db,branch,sig)
    last_id=int(db.execute("SELECT value FROM meta WHERE key='cursor_page_id'").fetchone()[0]) if db.execute("SELECT value FROM meta WHERE key='cursor_page_id'").fetchone() else 0
    try:
        while counts['pages_processed']<max_articles:
            take=min(batch_size,max_articles-counts['pages_processed'])
            qid_join='LEFT JOIN wiki_qid q ON q.page_id=p.page_id' if has_qid else ''
            qid_field='q.qid' if has_qid else 'NULL AS qid'
            pages=list(src.execute('SELECT p.page_id,p.title,p.ns,p.redirect,p.latest_revision,'+qid_field+
                        ' FROM wiki_pages p '+qid_join+' WHERE p.page_id>? AND p.ns=0 ORDER BY p.page_id LIMIT ?', (last_id,take)))
            if not pages:counts['source_exhausted']=1;break
            # Préchargement des catégories indexées pour tout le lot, en UNE requête
            # plutôt que plusieurs milliers de seeks individuels.
            cats_by_page=defaultdict(list)
            lo=int(pages[0]['page_id']);hi=int(pages[-1]['page_id'])
            if categories_limit:
                for pid,category in src.execute('SELECT source_page_id,category FROM wiki_categorylinks '
                                                'WHERE source_page_id BETWEEN ? AND ? ORDER BY source_page_id',(lo,hi)):
                    if len(cats_by_page[pid])<categories_limit:cats_by_page[pid].append(category)
            links_by_page=defaultdict(list)
            if has_links:
                for pid,link_title in src.execute('SELECT l.source_page_id,t.title '
                        'FROM wiki_pagelinks l JOIN wiki_linktargets t ON t.target_id=l.target_id '
                        'WHERE l.source_page_id BETWEEN ? AND ? AND t.ns=0 ORDER BY l.source_page_id',
                        (lo,hi)):
                    if len(links_by_page[pid])<30:links_by_page[pid].append(link_title)
            with db:
                for r in pages:
                    pid=int(r['page_id']);last_id=pid
                    cats=cats_by_page.get(pid,[])
                    links=links_by_page.get(pid,[])
                    kind,proposals=classify(r['title'],cats,branch,links,r['qid'])
                    db.execute('INSERT OR REPLACE INTO article_profiles VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                               (pid,r['title'],r['latest_revision'],int(r['redirect']),kind,len(proposals),now(),
                                r['qid'],len(cats),len(links),json.dumps({'cats':cats,'links':links,'qid':r['qid']},ensure_ascii=False)))
                    db.execute('DELETE FROM branch_suggestions WHERE page_id=?',(pid,))
                    for p in proposals:
                        db.execute('INSERT INTO branch_suggestions VALUES(?,?,?,?,?)',
                                   (pid,p['branch_id'],p['score'],p['concept_id_suggested'],p['reason']))
                    counts['pages_processed']+=1
                    counts['branch_suggestions']+=len(proposals)
                    counts['redirects']+=bool(r['redirect'])
                    counts['without_suggestion']+=not bool(proposals)
                db.execute('INSERT OR REPLACE INTO meta VALUES(?,?)',('cursor_page_id',str(last_id)))
            if len(pages)<take:counts['source_exhausted']=1;break
        totals={'profiles':db.execute('SELECT COUNT(*) FROM article_profiles').fetchone()[0],
                'suggestions':db.execute('SELECT COUNT(*) FROM branch_suggestions').fetchone()[0],
                'without_suggestion':db.execute('SELECT COUNT(*) FROM article_profiles WHERE branch_candidates=0').fetchone()[0],
                'branch_count':len(branch)}
        return {'status':'QUALIFICATION_V31_OK','source':str(source),'output':str(output),'batch':dict(counts),
                'cursor_page_id':last_id,'totals':totals,'source_exhausted':bool(counts['source_exhausted']),
                'note':'Qualification indicative, non canonique ; aucun article exclu et aucune affectation v25 modifiée.'}
    finally:db.close();src.close()

def main(argv=None):
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--source',type=Path,default=DEFAULT_SOURCE)
    a.add_argument('--output',type=Path,default=DEFAULT_OUT)
    a.add_argument('--branches',type=Path,default=DEFAULT_BRANCH_DIR)
    a.add_argument('--batch-size',type=int,default=2000)
    a.add_argument('--max-articles',type=int,default=100000)
    a.add_argument('--categories-per-article',type=int,default=18)
    args=a.parse_args(argv)
    try:
        print(json.dumps(execute(args.source,args.output,args.branches,batch_size=args.batch_size,
                 max_articles=args.max_articles,categories_limit=args.categories_per_article),ensure_ascii=False,indent=2))
    except (OSError,ValueError,sqlite3.Error,json.JSONDecodeError) as exc:
        print(json.dumps({'status':'QUALIFICATION_V31_REFUS','error':str(exc)},ensure_ascii=False));return 2
    return 0

if __name__=='__main__':raise SystemExit(main())
