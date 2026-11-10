#!/usr/bin/env python3
"""V26: inventaire des noms de categories Wikipedia, lecture seule source.

Le catalogue derive est autonome. Aucun XML, aucun texte d'article, aucune canonisation.
Incremente par titres grace a idx_wiki_lt_title et se reprend avec un curseur
transactionnel. FTS5 SQLite utilise sur la copie derivee pour la selection rapide.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import zipfile

SCHEMA = 'encyklopedia.wikipedia-category-inventory.v26/1'
EXPORT_SCHEMA = 'encyklopedia.category-selection-export.v26/1'
DEFAULT_SOURCE = Path(r'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite')
DEFAULT_INVENTORY = Path(r'D:\EncyKlopedia\80_search_indexes\EncyKlopedia\inventaire_categories_wikipedia_v26.sqlite')
DEFAULT_EXPORT = Path(r'D:\EncyKlopedia\30_working\inventaire_categories_wikipedia_v26')
STOP = {'and', 'or', 'in', 'by', 'the', 'of', 'for', 'to', 'a', 'an', 'on', 'at', 'from', 'with'}
BROAD = ['education', 'educational', 'school', 'schools', 'teaching', 'teacher', 'teachers',
         'curriculum', 'literacy', 'pedagogy', 'learning', 'university', 'universities',
         'student', 'students', 'academic', 'instruction', 'schooling', 'discrimination',
         'language', 'multilingual', 'bilingual', 'policy']
SKIP_PREFIX = ('wikipedia ', 'articles ', 'all wikipedia ', 'use ', 'cs1 ',
               'webarchive ', 'pages ', 'short description ', 'template ',
               'maintenance ', 'tracking ', 'births ', 'deaths ')

class Refus(RuntimeError): pass

def jd(x): return (json.dumps(x, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')
def sh(b): return hashlib.sha256(b).hexdigest()
def moment(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def tokens(s): return [w for w in re.findall(r'[a-z0-9]+',str(s).lower().replace('_',' ')) if w not in STOP and len(w)>1]
def norm(s): return ' '.join(str(s).casefold().replace('_',' ').split())
def source(path):
    if not path.is_file() or path.is_symlink(): raise Refus('Base SQLite Wikipedia absente ou lien symbolique: '+str(path))
    c=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=30)
    try:
        c.row_factory=sqlite3.Row
        c.execute('PRAGMA query_only=ON')
        tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        ix={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='index'")}
        if not {'wiki_linktargets','wiki_pages','wiki_categorylink_ids','ingest_state'}<=tables:
            raise Refus('Tables de l\'index source incompletes')
        if not {'idx_wiki_lt_title','idx_wiki_pages_title','idx_wiki_catid_target'}<=ix:
            raise Refus('Index SQL requis absents: pas de balayage non indexe')
        state={r['stage']: int(r['completed']) for r in c.execute('SELECT stage,completed FROM ingest_state')}
        if any(state.get(x)!=1 for x in ('page','linktarget','categorylinks')):
            raise Refus('Import SQL source non termine')
        plan=' '.join(str(r[3]) for r in c.execute('EXPLAIN QUERY PLAN SELECT target_id,title FROM wiki_linktargets INDEXED BY idx_wiki_lt_title WHERE ns=14 AND title>? ORDER BY title LIMIT 100',('',)))
        if 'idx_wiki_lt_title' not in plan or 'TEMP B-TREE' in plan.upper(): raise Refus('Pagination par titre non indexee: '+plan)
        stat=path.stat()
        desc={'path':str(path.resolve()),'size_bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns,'stages':state,'signature_scope':'FILE_METADATA_PLUS_INGEST_COMPLETION'}
    except BaseException:
        c.close()
        raise
    return c,desc,sh(jd(desc))

def inventory(path,sign,desc):
    if path.is_symlink(): raise Refus('Destination SQLite symbolique interdite: '+str(path))
    if path.exists():
        c=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
        try:
            r=c.execute("SELECT value FROM meta WHERE key='schema'").fetchone()
            if not r or r[0]!=SCHEMA: raise Refus('Index de destination preexistant incompatible')
        except sqlite3.DatabaseError as exc: raise Refus('Destination SQLite etrangere: '+str(exc)) from exc
        finally: c.close()
    else: path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=120)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA busy_timeout=120000')
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA synchronous=NORMAL')
    db.executescript('''
      CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS categories(target_id INTEGER PRIMARY KEY,title TEXT NOT NULL UNIQUE,origin TEXT NOT NULL DEFAULT 'LINKTARGET');
      CREATE VIRTUAL TABLE IF NOT EXISTS categories_fts USING fts5(title,content='categories',content_rowid='target_id',tokenize='unicode61');
    ''')
    db.commit()
    old=db.execute("SELECT value FROM meta WHERE key='source_signature'").fetchone()
    if old and old[0]!=sign:
        db.close()
        raise Refus('La source Wikipedia a change: refus de fusionner deux snapshots. Conserver un index versionne.')
    with db:
        initial={'schema':SCHEMA,'source_signature':sign,'source_description':json.dumps(desc,sort_keys=True),'cursor_title':'','phase':'linktarget',
                 'categories_scanned':'0','categories_unique':'0','done':'0','created_utc':moment()}
        for k,v in initial.items(): db.execute('INSERT OR IGNORE INTO meta VALUES (?,?)',(k,v))
    return db

def mv(db,k):
    r=db.execute('SELECT value FROM meta WHERE key=?',(k,)).fetchone()
    return r[0] if r else None

def ingest(src, db, batch, max_rows):
    if mv(db,'done')=='1': return {'status':'V26_ALREADY_COMPLETE','scanned_this_run':0,'total':int(mv(db,'categories_scanned')),'completed':True}
    done=0
    while done<max_rows:
        take=min(batch,max_rows-done)
        last=mv(db,'cursor_title')
        phase=mv(db,'phase')
        if phase=='linktarget':
            rows=src.execute('''SELECT target_id AS local_id,title FROM wiki_linktargets INDEXED BY idx_wiki_lt_title
                                WHERE ns=14 AND title>? ORDER BY title LIMIT ?''',(last,take)).fetchall()
        else:
            rows=src.execute('''SELECT -page_id AS local_id,title FROM wiki_pages INDEXED BY idx_wiki_pages_title
                                WHERE ns=14 AND title>? ORDER BY title LIMIT ?''',(last,take)).fetchall()
        if not rows:
            with db:
                if phase=='linktarget':
                    db.execute("UPDATE meta SET value='page' WHERE key='phase'")
                    db.execute("UPDATE meta SET value='' WHERE key='cursor_title'")
                else: db.execute("UPDATE meta SET value='1' WHERE key='done'")
            if phase=='page':break
            continue
        with db:
            added=0
            for row in rows:
                db.execute('INSERT OR IGNORE INTO categories(target_id,title,origin) VALUES (?,?,?)',
                           (row['local_id'],row['title'],'LINKTARGET' if phase=='linktarget' else 'CATEGORY_PAGE_ONLY'))
                if db.execute('SELECT changes()').fetchone()[0]:
                    added+=1
                    db.execute('INSERT INTO categories_fts(rowid,title) VALUES (?,?)',(row['local_id'],row['title']))
            db.execute("UPDATE meta SET value=? WHERE key='cursor_title'",(rows[-1]['title'],))
            db.execute("UPDATE meta SET value=CAST(value AS INTEGER)+? WHERE key='categories_scanned'",(len(rows),))
            db.execute("UPDATE meta SET value=CAST(value AS INTEGER)+? WHERE key='categories_unique'",(added,))
        done+=len(rows)
        if done%max(batch*10,1000)==0:
            print(json.dumps({'event':'V26_PROGRESS','rows_this_run':done,'rows_total':int(mv(db,'categories_scanned')),'phase':phase},ensure_ascii=False),flush=True)
    return {'status':'V26_INVENTORY_RUN_OK','scanned_this_run':done,
            'total':int(mv(db,'categories_scanned')),'completed':mv(db,'done')=='1',
            'phase':mv(db,'phase'),'cursor_title':mv(db,'cursor_title')}

def concepts_from(path):
    if not path.is_file(): raise Refus('Source UNESCO absente: '+str(path))
    raw=path.read_bytes()
    js=json.loads(raw.decode('utf-8-sig'))
    cc=js.get('concepts')
    if not isinstance(cc,list) or not cc: raise Refus('Liste de concepts UNESCO absente')
    res=[];seen=set()
    for c in cc:
        cid=c['unesco_id']
        if not re.fullmatch(r'concept[0-9]+',cid) or cid in seen: raise Refus('Identite UNESCO invalide/dupliquee')
        seen.add(cid)
        en=c.get('preferred_labels',{}).get('en',[])
        fr=c.get('preferred_labels',{}).get('fr',[])
        if not en: continue
        alt=c.get('alternate_labels',{}).get('en',[])
        res.append({'id':cid,'en':str(en[0]),'fr':str(fr[0]) if fr else '',
                    'names':list(dict.fromkeys([str(en[0])]+[str(a) for a in alt[:5]]))})
    return res,sh(raw)

def hits(db, query, limit):
    # Only generated FTS tokens/phrases; never interpolate user SQL.
    try:
        return db.execute('''SELECT c.target_id,c.title,c.origin FROM categories_fts f
                             JOIN categories c ON c.target_id=f.rowid
                             WHERE categories_fts MATCH ? LIMIT ?''',(query,limit)).fetchall()
    except sqlite3.OperationalError as e:
        raise Refus('Recherche FTS invalide: '+repr(query)+' '+str(e)) from e

def search_category(db, phrase, cap):
    tok=tokens(phrase)
    if not tok:return []
    all_rows={}
    for expr in ['"'+' '.join(tok[:5])+'"', ' AND '.join('"'+x+'"' for x in tok[:4])]:
        for r in hits(db,expr,cap):all_rows[r['target_id']]=r
    return list(all_rows.values())

def score(name,label):
    n=norm(name); l=norm(label)
    ts=set(tokens(label)); c=set(tokens(name)); matches=ts & c
    if n==l:return 100,'EXACT_TITLE'
    if n.startswith(l+' ') or n.endswith(' '+l):return 88,'TITLE_PHRASE'
    if l in n:return 79,'PHRASE'
    if ts and ts<=c:return 68,'ALL_TOKENS'
    if matches:return min(60,20+int(40*len(matches)/len(ts))),'TOKEN_OVERLAP'
    return 0,'NO_SIGNAL'

def members_sample(src,target,limit=14):
    if target<0:return [],[],0
    rows=src.execute('''SELECT p.ns,p.title,p.redirect,cl.type
                          FROM wiki_categorylink_ids cl INDEXED BY idx_wiki_catid_target
                          JOIN wiki_pages p ON p.page_id=cl.source_page_id
                          WHERE cl.target_id=? LIMIT ?''',(target,limit)).fetchall()
    pages=[];cats=[]
    for r in rows:
        if r['ns']==0 and r['redirect']==0 and len(pages)<6: pages.append(str(r['title']).replace('_',' '))
        if r['ns']==14 and len(cats)<4: cats.append(str(r['title']).replace('_',' '))
    return pages,cats,len(rows)

def csv_bytes(rows,fields):
    f=io.StringIO(newline='')
    w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore',lineterminator='\n')
    w.writeheader();w.writerows(rows)
    return f.getvalue().encode('utf-8-sig')

def export(src,db,concept_file,dest,max_per_name=90,max_candidates=6000,broad_per_term=50,sample_limit=14):
    concepts,concept_sha=concepts_from(concept_file)
    matches={};labels={}
    for con in concepts:
        for name in con['names']:
            for r in search_category(db,name,max_per_name):
                if norm(r['title']).startswith(SKIP_PREFIX):continue
                val,why=score(r['title'],name)
                if val<40:continue
                key=(con['id'],r['target_id'])
                if key not in matches or val>matches[key]['score']:
                    matches[key]={'concept_id':con['id'],'concept_en':con['en'],'concept_fr':con['fr'],
                                  'category_id':r['target_id'],'category_title':str(r['title']).replace('_',' '),'origin':r['origin'],
                                  'score':val,'evidence':why,'name_matched':name}
        labels[con['id']]=con
    sorted_hits=sorted(matches.values(),key=lambda x:(-x['score'],x['concept_id'],x['category_title']))[:max_candidates]
    broad_rows=[]
    broad_seen=set()
    for term in BROAD:
        for r in hits(db,'"'+term+'"',broad_per_term):
            if r['target_id'] in broad_seen or norm(r['title']).startswith(SKIP_PREFIX):continue
            broad_seen.add(r['target_id'])
            broad_rows.append({'category_id':r['target_id'],'category_title':str(r['title']).replace('_',' '),'origin':r['origin'],'seed':term})
    samples={}
    for item in sorted_hits+broad_rows:
        target=item['category_id']
        if target not in samples: samples[target]=members_sample(src,target,sample_limit)
    for item in sorted_hits:
        p,c,n=samples[item['category_id']]
        item.update({'example_articles':' | '.join(p),'example_subcategories':' | '.join(c),
                     'sampled_members':n,'decision':'TO_REVIEW','review_note':''})
    for item in broad_rows:
        p,c,n=samples[item['category_id']]
        item.update({'example_articles':' | '.join(p),'example_subcategories':' | '.join(c),'sampled_members':n})
    cov=[];cnt=defaultdict(int)
    for m in sorted_hits:cnt[m['concept_id']]+=1
    for c in concepts:cov.append({'concept_id':c['id'],'label_en':c['en'],'label_fr':c['fr'],'candidates':cnt[c['id']]})
    head={'schema':EXPORT_SCHEMA,'created_utc':moment(),'source_signature':mv(db,'source_signature'),
          'unesco_sha256':concept_sha,'inventory_categories_seen':int(mv(db,'categories_scanned')),'inventory_categories_unique':int(mv(db,'categories_unique')),
          'inventory_complete':mv(db,'done')=='1','inventory_phase':mv(db,'phase'),'concepts_analyzed':len(concepts),
          'candidate_pairs':len(sorted_hits),'broad_categories':len(broad_rows),
          'review_state':'CANDIDATES_UNREVIEWED','ranking':'LEXICAL_HEURISTIC_NOT_SEMANTIC_PROOF',
          'sampling':'UP_TO_14_DIRECT_MEMBERS_NOT_TRUE_CATEGORY_CARDINALITY',
          'claim':'LOCAL_INVENTORY_REVIEW_SLICE_NOT_FULL_CLASSIFICATION',
          'raw_wikipedia_articles_included':0,'canonical_admissions':0}
    files={'CANDIDATS_UNESCO_V26.csv':csv_bytes(sorted_hits,['concept_id','concept_en','concept_fr','category_id','category_title','origin','score','evidence','name_matched','example_articles','example_subcategories','sampled_members','decision','review_note']),
           'FAMILLES_GENERALES_V26.csv':csv_bytes(broad_rows,['category_id','category_title','origin','seed','example_articles','example_subcategories','sampled_members']),
           'COUVERTURE_CONCEPTS_V26.csv':csv_bytes(cov,['concept_id','label_en','label_fr','candidates']),
           'RAPPORT_INVENTAIRE_V26.json':jd(head)}
    manifest={'format':'encyklopedia.file-manifest.v26/1','sha256':{k:sh(v) for k,v in files.items()}}
    files['MANIFEST_SHA256.json']=jd(manifest)
    dest.mkdir(parents=True,exist_ok=True)
    path=dest/'EXPORT_INVENTAIRE_V26_POUR_CHATGPT.zip'
    if path.exists():
        # Preserve an earlier export; do not silently replace a previously reviewed object.
        if not zip_valid(path,files):
            i=1
            while (dest/f'EXPORT_INVENTAIRE_V26_POUR_CHATGPT_{i:03d}.zip').exists():i+=1
            path=dest/f'EXPORT_INVENTAIRE_V26_POUR_CHATGPT_{i:03d}.zip'
        else:return {'status':'V26_EXPORT_IDENTICAL','zip':str(path),**head}
    tmp=path.with_suffix('.zip.partial')
    try:
        with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for k,v in sorted(files.items()):z.writestr(k,v)
        tmp.replace(path)
    finally:
        if tmp.exists():tmp.unlink()
    return {'status':'V26_EXPORT_OK','zip':str(path),**head}

def zip_valid(path,files):
    try:
        with zipfile.ZipFile(path) as z:
            return set(z.namelist())==set(files) and all(z.read(k)==v for k,v in files.items())
    except (OSError,zipfile.BadZipFile):return False

def probe(src,db,request_file,dest):
    """Targeted local drill-down generated from an AI request, no full export."""
    request=json.loads(request_file.read_text(encoding='utf-8-sig'))
    if request.get('schema')!='encyklopedia.category-probe-request.v26/1':
        raise Refus('Schema de requete inconnu')
    queries=request.get('queries',[])
    ids=request.get('category_ids',[])
    if not isinstance(queries,list) or not isinstance(ids,list) or len(queries)>50 or len(ids)>200:
        raise Refus('Requete trop large')
    result={}
    for q in queries:
        if not isinstance(q,dict):raise Refus('Requete de categorie mal formee')
        term=q.get('term','')
        cap=int(q.get('max_results',100))
        if not isinstance(term,str) or not 1<=len(term)<=120 or not 1<=cap<=300:
            raise Refus('Terme ou plafond invalide')
        for r in search_category(db,term,cap):
            result[r['target_id']]={'category_id':r['target_id'],
                'category_title':str(r['title']).replace('_',' '), 'origin':r['origin'],
                'matching_queries':set([term])} if r['target_id'] not in result else result[r['target_id']]
            result[r['target_id']]['matching_queries'].add(term)
    for i in ids:
        if not isinstance(i,int) or i==0:raise Refus('Identifiant demande invalide')
        r=db.execute('SELECT target_id,title,origin FROM categories WHERE target_id=?',(i,)).fetchone()
        if r:
            result.setdefault(i,{'category_id':i,'category_title':str(r['title']).replace('_',' '),
                                 'origin':r['origin'],'matching_queries':set()})
    items=[]
    for d in sorted(result.values(),key=lambda x:x['category_title']):
        a,b,n=members_sample(src,d['category_id'])
        items.append({**d,'matching_queries':' | '.join(sorted(d['matching_queries'])),
                      'example_articles':' | '.join(a),'example_subcategories':' | '.join(b),'sampled_members':n})
    head={'schema':'encyklopedia.category-probe-export.v26/1',
          'inventory_complete':mv(db,'done')=='1','source_signature':mv(db,'source_signature'),
          'results':len(items),'raw_article_texts_included':0,'classification_reviewed':False}
    files={'RESULTATS_REQUETES_V26.csv':csv_bytes(items,['category_id','category_title','origin','matching_queries','example_articles','example_subcategories','sampled_members']),
           'RAPPORT_REQUETES_V26.json':jd(head)}
    files['MANIFEST_SHA256.json']=jd({'sha256':{k:sh(v) for k,v in files.items()}})
    dest.mkdir(parents=True,exist_ok=True)
    outfile=dest/('RESULTATS_REQUETES_V26_'+sh(request_file.read_bytes())[:12]+'_'+mv(db,'categories_scanned')+'.zip')
    if outfile.exists():
        if not zip_valid(outfile,files):raise Refus('Export de requete existant et different: ne pas ecraser')
    else:
        with zipfile.ZipFile(outfile,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for k,v in sorted(files.items()):z.writestr(k,v)
    return {'status':'V26_PROBE_OK','zip':str(outfile),**head}

def review_import(db,concept_file,decisions_path,dest):
    """Create bridge proposals only; does not mutate v25 or promote canon.

    JSON: {schema:'encyklopedia.category-review.v26/1', decisions:[...]}.
    """
    o=json.loads(decisions_path.read_text(encoding='utf-8-sig'))
    if o.get('schema')!='encyklopedia.category-review.v26/1':raise Refus('Schema de revue inconnu')
    if o.get('source_signature')!=mv(db,'source_signature'):raise Refus('Decision issue d\'un autre snapshot')
    concepts,sha_concepts=concepts_from(concept_file)
    if o.get('unesco_sha256')!=sha_concepts:raise Refus('Reference UNESCO differente')
    valid={c['id'] for c in concepts}
    records=[];seen=set()
    for d in o.get('decisions',[]):
        if not isinstance(d,dict):raise Refus('Decision mal formee')
        cid=str(d.get('concept_id',''));tid=int(d.get('category_id',0));decision=d.get('decision','')
        if cid not in valid or tid==0 or decision not in ('INCLUDE','EXCLUDE','HOLD'):raise Refus('Decision invalide')
        if (cid,tid) in seen:raise Refus('Decision en double')
        seen.add((cid,tid))
        row=db.execute('SELECT title FROM categories WHERE target_id=?',(tid,)).fetchone()
        if not row or norm(row[0])!=norm(d.get('category_title','')):raise Refus('Identite de categorie inconnue ou titre change')
        reason=str(d.get('justification','')).strip()
        depth=int(d.get('depth_limit',0))
        if decision=='INCLUDE' and (tid<0 or len(reason)<20 or not 0<=depth<=2): raise Refus('Inclusion sans categorie cible liee ni justification ou profondeur 0..2')
        records.append({'concept_id':cid,'category_title':str(row[0]).replace('_',' '),
                        'status':'ACTIVE_REVIEWED_AI' if decision=='INCLUDE' else 'PROPOSED_NOT_ACTIVE',
                        'justification':reason,'depth_limit':depth,'decision':decision})
    if not records:raise Refus('Aucune decision')
    output=csv_bytes(records,['concept_id','category_title','status','justification','depth_limit','decision'])
    dest.mkdir(parents=True,exist_ok=True)
    path=dest/('PONTS_REVUS_V26_'+sh(decisions_path.read_bytes())[:12]+'.csv')
    if path.exists() and path.read_bytes()!=output:raise Refus('Collision de destination')
    if not path.exists():path.write_bytes(output)
    return {'status':'V26_DECISIONS_PREPAREES','reviewed':len(records),'included':sum(r['decision']=='INCLUDE' for r in records),
            'out':str(path),'v25_catalogue_modified':False,'canonical_admissions':0}

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action',choices=['scan','export','scan-export','probe','import-decisions','status'])
    ap.add_argument('--source-db',type=Path,default=DEFAULT_SOURCE)
    ap.add_argument('--inventory-db',type=Path,default=DEFAULT_INVENTORY)
    ap.add_argument('--output-dir',type=Path,default=DEFAULT_EXPORT)
    ap.add_argument('--concepts',type=Path)
    ap.add_argument('--decisions',type=Path)
    ap.add_argument('--queries-file',type=Path)
    ap.add_argument('--max-rows',type=int,default=200000)
    ap.add_argument('--batch-size',type=int,default=5000)
    ap.add_argument('--max-candidates',type=int,default=6000)
    ap.add_argument('--max-per-name',type=int,default=90)
    ap.add_argument('--broad-per-term',type=int,default=50)
    a=ap.parse_args(argv)
    try:
        if not 0<a.batch_size<=20000 or not 0<a.max_rows<=5000000 or not 10<=a.max_candidates<=50000 or not 1<=a.max_per_name<=1000 or not 1<=a.broad_per_term<=300:
            raise Refus('Budget de lecture invalide')
        if a.action in ('export','scan-export','import-decisions') and (not a.concepts or not a.concepts.is_file()):
            raise Refus('--concepts JSON UNESCO requis')
        src,desc,sig=source(a.source_db)
        try:
            db=inventory(a.inventory_db,sig,desc)
            try:
                if a.action in ('scan','scan-export'):
                    print(json.dumps(ingest(src,db,a.batch_size,a.max_rows),ensure_ascii=False),flush=True)
                if a.action in ('export','scan-export'):
                    print(json.dumps(export(src,db,a.concepts,a.output_dir,a.max_per_name,a.max_candidates,a.broad_per_term),ensure_ascii=False),flush=True)
                if a.action=='probe':
                    if not a.queries_file or not a.queries_file.is_file():raise Refus('--queries-file JSON requis')
                    print(json.dumps(probe(src,db,a.queries_file,a.output_dir),ensure_ascii=False),flush=True)
                if a.action=='status':
                    print(json.dumps({'status':'V26_STATUS_OK','total':int(mv(db,'categories_scanned')),'complete':mv(db,'done')=='1',
                                     'source_signature':sig,'unique_categories':int(mv(db,'categories_unique')),'inventory_db':str(a.inventory_db)},ensure_ascii=False),flush=True)
                if a.action=='import-decisions':
                    if not a.decisions:raise Refus('--decisions JSON requis')
                    print(json.dumps(review_import(db,a.concepts,a.decisions,a.output_dir),ensure_ascii=False),flush=True)
            finally:db.close()
        finally:src.close()
        return 0
    except (Refus,sqlite3.Error,OSError,ValueError,KeyError,json.JSONDecodeError) as e:
        print(json.dumps({'status':'V26_REFUS','reason':str(e)},ensure_ascii=False),file=sys.stderr,flush=True)
        return 2

if __name__=='__main__':sys.exit(main())
