"""Lecteurs UNESCO, Wikipédia et graphe Wikidata; aucune modification de la source."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from collections import Counter
from contextlib import contextmanager
import hashlib
import json
import re
import sqlite3
from .sql import read_source, has_table
from .locking import serialized

QID_RE=re.compile(r'^Q[1-9][0-9]*$')
CID_RE=re.compile(r'^concept[1-9][0-9]*$')

def utc():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def label(c,lang):
    labels=c.get('preferred_labels',{}).get(lang,[])
    return str(labels[0]) if labels else ''

@serialized
def import_unesco(db,root,limit_branches=None):
    """Import incrémental des 88 sources de référence; pas des états Kristal modifiés."""
    root=Path(root)
    if not root.is_dir():raise FileNotFoundError('Répertoire UNESCO absent : '+str(root))
    counts=Counter()
    branches=sorted(root.glob('branches/unesco-mt*'))
    if limit_branches is not None:branches=branches[:limit_branches]
    if not branches:raise ValueError('Aucun espace UNESCO préparé trouvé')
    for b in branches:
        source=b/'canon/domain/unesco-source.json'
        mappings=b/'derived/wikidata-p3916-candidates.json'
        if not source.is_file():continue
        data=json.loads(source.read_text(encoding='utf-8-sig'))
        mid=data.get('unesco_microthesaurus')
        if isinstance(mid,dict):mid=mid.get('id') or mid.get('code')
        if not isinstance(mid,str) or not re.fullmatch(r'mt\d+\.\d+',mid):
            # Filename is a secondary validated locator, not an invented branch id.
            mt=re.fullmatch(r'unesco-mt(\d+)-(\d+)',b.name)
            if not mt:continue
            mid=f'mt{int(mt[1])}.{int(mt[2]):02d}'
        bid='unesco.'+mid
        concepts=data.get('concepts',[])
        with db:
            db.execute('INSERT INTO branches(branch_id,title,source_path,source_version) VALUES (?,?,?,?) '
                       'ON CONFLICT(branch_id) DO UPDATE SET source_path=excluded.source_path,source_version=excluded.source_version',
                       (bid,bid,str(source),str(data.get('source_scheme_modified',''))))
            for c in concepts:
                cid=c.get('unesco_id','')
                if not CID_RE.fullmatch(cid):continue
                desc=c.get('scope_notes',{}).get('en',[])
                db.execute('''INSERT INTO concepts VALUES(?,?,?,?,?,?,?)
                    ON CONFLICT(concept_id) DO UPDATE SET label_fr=excluded.label_fr,
                    label_en=excluded.label_en,description=excluded.description,
                    broader_json=excluded.broader_json,related_json=excluded.related_json,
                    source_uri=excluded.source_uri''',
                    (cid,label(c,'fr'),label(c,'en'),desc[0] if desc else '',
                     json.dumps(c.get('broader',[]),ensure_ascii=False),
                     json.dumps(c.get('related',[]),ensure_ascii=False),c.get('source_uri','')))
                db.execute('INSERT OR IGNORE INTO branch_concepts VALUES (?,?)',(bid,cid))
                for txt in set(c.get('preferred_labels',{}).get('en',[])+c.get('alternate_labels',{}).get('en',[])):
                    if isinstance(txt,str) and 1<=len(txt)<=150:
                        db.execute('INSERT OR IGNORE INTO concept_aliases VALUES(?,?,?)',(cid,txt,'en'))
                counts['concept_memberships']+=1
            if mappings.is_file():
                records=json.loads(mappings.read_text(encoding='utf-8-sig')).get('mappings',[])
                for m in records:
                    cid,qid=m.get('unesco_id',''),m.get('qid_candidate','')
                    if not CID_RE.fullmatch(cid) or not QID_RE.fullmatch(qid):
                        if m.get('status')=='REVIEW_AMBIGUOUS_P3916':counts['ambiguous']+=1
                        elif m.get('status')=='NO_P3916_MAPPING':counts['unmapped']+=1
                        continue
                    db.execute('INSERT OR IGNORE INTO mappings VALUES(?,?,?,?,?)',
                               (cid,qid,m.get('status','CANDIDATE'),'P3916_UNESCO_KRISTALS',bid))
                    db.execute('INSERT OR IGNORE INTO subjects(subject_key,qid,preferred_label) VALUES(?,?,?)',
                               ('wd:'+qid,qid,label(next((c for c in concepts if c.get('unesco_id')==cid),{}),'en')))
                    counts['qid_mappings']+=1
            counts['branches']+=1
    counts['distinct_concepts']=db.execute('SELECT COUNT(*) FROM concepts').fetchone()[0]
    return dict(counts)

class WikipediaIndex:
    def __init__(self,path):self.path=Path(path);self._context=None;self.db=None
    def __enter__(self):
        self._context=read_source(self.path);self.db=self._context.__enter__()
        if not has_table(self.db,'wiki_qid') or not has_table(self.db,'wiki_pages'):
            self.__exit__(None,None,None);raise ValueError('Index Wikipédia sans wiki_qid/wiki_pages')
        return self
    def __exit__(self,*args):
        if self._context:self._context.__exit__(*args)
        self.db=None
    def by_qid(self,qid):
        if not QID_RE.fullmatch(qid):return []
        rows=self.db.execute('''SELECT p.page_id,p.ns,p.title,p.redirect,p.latest_revision,p.content_bytes
          FROM wiki_qid AS q JOIN wiki_pages AS p ON p.page_id=q.page_id
          WHERE q.qid=? AND p.ns=0 LIMIT 25''',(qid,))
        return [dict(r) for r in rows if not r['redirect']]
    def by_page_id(self,page_id):
        row=self.db.execute('''SELECT p.page_id,p.ns,p.title,p.redirect,p.latest_revision,p.content_bytes,q.qid
            FROM wiki_pages p LEFT JOIN wiki_qid q ON q.page_id=p.page_id WHERE p.page_id=?''',(page_id,)).fetchone()
        return dict(row) if row else None

class WikidataGraph:
    """Découverte par arêtes agrégées; jamais preuve de statement original."""
    PID_OFF=1_000_000_000
    def __init__(self,path):self.path=Path(path);self._context=None;self.db=None
    def __enter__(self):
        self._context=read_source(self.path);self.db=self._context.__enter__()
        if not {'entity','name','entity_edge','meta'}.issubset({x[0] for x in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}):
            self.__exit__(None,None,None);raise ValueError('Schéma Wikidata compact incompatible')
        meta=dict(self.db.execute('SELECT key,value FROM meta'))
        if str(meta.get('complete','')).lower() not in ('true','1'):
            self.__exit__(None,None,None);raise ValueError('Index compact incomplet')
        return self
    def __exit__(self,*args):
        if self._context:self._context.__exit__(*args)
        self.db=None
    def page(self,anchor_qid,pid,direction,cursor=0,limit=1000):
        if not QID_RE.fullmatch(anchor_qid) or not re.fullmatch(r'P[1-9]\d*',pid):return []
        if direction not in ('in','out'):raise ValueError('Direction invalide')
        aid=int(anchor_qid[1:]); prop=int(pid[1:])  # Skope compact: property_id raw P-number, e.g. P31 -> 31
        # Keyset with predicates that match Skope's edge indexes.
        if direction=='in':
            sql='''SELECT subject_id AS neighbor,statement_count,best_rank FROM entity_edge
                   WHERE target_id=? AND property_id=? AND subject_id>?
                   ORDER BY subject_id LIMIT ?'''
        else:
            sql='''SELECT target_id AS neighbor,statement_count,best_rank FROM entity_edge
                   WHERE subject_id=? AND property_id=? AND target_id>?
                   ORDER BY target_id LIMIT ?'''
        return [dict(row) for row in self.db.execute(sql,(aid,prop,int(cursor),int(limit)))]


def candidate_id(branch,concept,page_id):
    return 'V32_C_'+hashlib.sha256(f'{branch}|{concept}|{page_id}'.encode()).hexdigest()[:26]

def upsert_candidate(db,branch,concept,qid,page,origin,anchor_qid,path,priority):
    """Aucune promotion automatique; toutes les routes sont préservées."""
    cid=candidate_id(branch,concept,int(page['page_id']))
    old=db.execute('SELECT subject_key,revision_id,state FROM candidates WHERE candidate_id=?',(cid,)).fetchone()
    new_subject='wd:'+qid if qid else 'enwiki:'+str(page['page_id'])
    new_revision=str(page.get('latest_revision') or '')
    if old and (old['subject_key']!=new_subject or old['revision_id']!=new_revision):
        if db.execute('SELECT 1 FROM active_items WHERE candidate_id=?',(cid,)).fetchone():
            raise ValueError('Source changée pendant une tâche active : annuler ou terminer '+cid)
        db.execute("UPDATE candidates SET subject_key=?,revision_id=?,state='PENDING',title=? WHERE candidate_id=?",
                   (new_subject,new_revision,str(page['title']).replace('_',' '),cid))
        db.execute('INSERT INTO events(created_utc,kind,details) VALUES(?,?,?)',
                   (utc(),'SOURCE_CHANGED',json.dumps({'candidate_id':cid,'old':dict(old),'new_revision':new_revision})))
    title=str(page['title']).replace('_',' ')
    db.execute('''INSERT INTO candidates(candidate_id,branch_id,concept_id,subject_key,page_id,title,revision_id,priority,created_utc)
      VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(candidate_id) DO UPDATE SET priority=MAX(priority,excluded.priority)''',
      (cid,branch,concept,'wd:'+qid if qid else 'enwiki:'+str(page['page_id']),int(page['page_id']),title,str(page.get('latest_revision') or ''),int(priority),utc()))
    rid='V32_R_'+hashlib.sha256(f'{cid}|{origin}|{anchor_qid}|{path}'.encode()).hexdigest()[:26]
    db.execute('INSERT OR IGNORE INTO candidate_routes VALUES(?,?,?,?,?,?,?)',
               (rid,cid,origin,anchor_qid,qid,path,'Index agrégé; pertinence à confirmer par source documentaire'))
    db.execute('INSERT OR IGNORE INTO subjects(subject_key,qid,preferred_label) VALUES(?,?,?)',
               ('wd:'+qid if qid else 'enwiki:'+str(page['page_id']),qid or None,title))
    return cid


@serialized
def discover(db,settings,branch=None,graph_enabled=True,max_pairs=10000,graph_properties=None):
    """Passe 0: QID/P3916 direct, voisins par clés et curseurs; aucun XML scanné."""
    graph_properties=graph_properties or [('P31','in',75),('P279','in',70),('P921','in',63),('P361','in',54)]
    params=(branch,) if branch else ()
    where='AND m.branch_id=?' if branch else ''
    mappings=[dict(r) for r in db.execute(f'''SELECT m.branch_id,m.concept_id,m.qid
                  FROM mappings m WHERE m.status='SINGLE_P3916_CANDIDATE' {where}
                  ORDER BY m.branch_id,m.concept_id,m.qid''',params)]
    _source_epoch(db,settings)
    stats=Counter();pending_budget=max_pairs
    # Discovery can be repeated; settled candidate decisions are never reset.
    with WikipediaIndex(settings.wikipedia_sql) as wiki:
        with db:
            for m in mappings:
                for page in wiki.by_qid(m['qid']):
                    cid=upsert_candidate(db,m['branch_id'],m['concept_id'],m['qid'],page,
                                         'DIRECT_P3916',m['qid'],'P3916 -> wiki_qid',100)
                    stats['direct_routes']+=1
                stats['anchors_examined']+=1
        if graph_enabled and pending_budget>0 and Path(settings.wikidata_sql).is_file():
            with WikidataGraph(settings.wikidata_sql) as graph:
                for m in mappings:
                    if pending_budget<=0:break
                    for pid,direction,priority in graph_properties:
                        if pending_budget<=0:break
                        row=db.execute('''SELECT last_id,completed FROM graph_cursors
                            WHERE branch_id=? AND concept_id=? AND anchor_qid=? AND property_id=? AND direction=?''',
                            (m['branch_id'],m['concept_id'],m['qid'],pid,direction)).fetchone()
                        if row is not None and row['completed']:continue
                        last=int(row['last_id']) if row else 0
                        # Each cycle bounded, scanned nodes counted even without an article EN.
                        limit=min(pending_budget,settings.graph_per_anchor_limit,1000)
                        matches=graph.page(m['qid'],pid,direction,last,limit)
                        with db:
                            for edge in matches:
                                neighbor=int(edge['neighbor'])
                                if neighbor<=0 or neighbor>=1_000_000_000:continue
                                nq='Q'+str(neighbor)
                                for page in wiki.by_qid(nq):
                                    cid=upsert_candidate(db,m['branch_id'],m['concept_id'],nq,page,
                                           'WIKIDATA_GRAPH',m['qid'],f'{pid}:{direction}',priority)
                                    stats['graph_routes']+=1
                                stats['graph_neighbors_scanned']+=1
                            if matches:last=int(matches[-1]['neighbor'])
                            complete=int(len(matches)<limit)
                            db.execute('''INSERT INTO graph_cursors VALUES(?,?,?,?,?,?,?,?)
                                ON CONFLICT(branch_id,concept_id,anchor_qid,property_id,direction)
                                DO UPDATE SET last_id=excluded.last_id,completed=excluded.completed,
                                              updated_utc=excluded.updated_utc''',
                                       (m['branch_id'],m['concept_id'],m['qid'],pid,direction,last,complete,utc()))
                        pending_budget-=len(matches)
                    if pending_budget<=0:break
    stats['remaining_graph_budget']=pending_budget
    stats['pending_candidates']=db.execute("SELECT count(*) FROM candidates WHERE state='PENDING'").fetchone()[0]
    stats['total_candidates']=db.execute('SELECT count(*) FROM candidates').fetchone()[0]
    stats['unfinished_paths']=db.execute('SELECT count(*) FROM graph_cursors WHERE completed=0').fetchone()[0]
    return dict(stats)


@serialized
def discover_fallback(db,settings,branch=None,max_pages=2500,per_alias=200):
    """Rappel lexical borné pour concepts sans QID P3916 unique.

    Pas de full-scan du dump; uniquement des plages sur idx_wiki_pages_title.
    Ne retire jamais des candidats; keyset persistant pour les vagues suivantes.
    """
    _source_epoch(db,settings)
    where='AND bc.branch_id=?' if branch else ''
    params=(branch,) if branch else ()
    q=f'''SELECT DISTINCT bc.branch_id,bc.concept_id,a.alias FROM branch_concepts bc
           JOIN concept_aliases a ON a.concept_id=bc.concept_id
           WHERE 1=1  -- V6: recherche lexicale pour tous les concepts
           {where} ORDER BY bc.branch_id,bc.concept_id,a.alias'''
    remaining=max(0,int(max_pages));c=Counter()
    with read_source(settings.wikipedia_sql) as wiki:
        if not has_table(wiki,'wiki_qid') or not has_table(wiki,'wiki_pages'):
            raise ValueError('Source sans wiki_qid/wiki_pages')
        for item in db.execute(q,params).fetchall():
            if remaining<=0:break
            bid,cid,alias=item
            prefix='_'.join(alias.split())
            if not prefix:continue
            state=db.execute('SELECT last_title,completed FROM fallback_cursors WHERE branch_id=? AND concept_id=? AND alias=?',
                             (bid,cid,alias)).fetchone()
            if state and state['completed']:continue
            last=state['last_title'] if state else ''
            limit=min(remaining,per_alias)
            # Le titre indexé est le critère, pas une analyse brute du texte de tout Wikipédia.
            rows=wiki.execute('''SELECT p.page_id,p.title,p.latest_revision,p.content_bytes,q.qid
                 FROM wiki_pages p LEFT JOIN wiki_qid q ON q.page_id=p.page_id
                 WHERE p.ns=0 AND p.redirect=0 AND p.title>=? AND p.title<? AND p.title>?
                 ORDER BY p.title LIMIT ?''',(prefix,prefix+'\uffff',last,limit)).fetchall()
            with db:
                for r in rows:
                    d=dict(r)
                    upsert_candidate(db,bid,cid,d.get('qid'),d,
                                     'SQL_TITLE_PREFIX',None,'title-prefix:'+prefix,42)
                    c['candidate_routes']+=1
                    c['pages_examined']+=1
                finished=int(len(rows)<limit)
                db.execute('''INSERT INTO fallback_cursors VALUES(?,?,?,?,?,?)
                      ON CONFLICT(branch_id,concept_id,alias) DO UPDATE SET
                      last_title=excluded.last_title,completed=excluded.completed,updated_utc=excluded.updated_utc''',
                      (bid,cid,alias,rows[-1]['title'] if rows else last,finished,utc()))
            remaining-=len(rows)
            c['aliases_examined']+=1
    c['budget_remaining']=remaining
    c['unfinished_aliases']=db.execute('SELECT COUNT(*) FROM fallback_cursors WHERE completed=0').fetchone()[0]
    return dict(c)


def _source_epoch(db,settings):
    """Cheap source change detector, not an integrity checksum of huge corpora.

    Explicit source_epoch must change for in-place updates retaining size/mtime.
    """
    parts={'declared':settings.source_epoch}
    for name in ('wikipedia_sql','wikidata_sql'):
        path=Path(getattr(settings,name))
        parts[name]={'path':str(path.resolve())}
        for suffix in ('','-wal'):
            item=Path(str(path)+suffix)
            if item.exists():
                stat=item.stat();parts[name][suffix or 'main']=[stat.st_size,stat.st_mtime_ns]
    epoch=hashlib.sha256(json.dumps(parts,sort_keys=True).encode()).hexdigest()
    row=db.execute("SELECT value FROM meta WHERE key='source_epoch'").fetchone()
    if row and row[0]==epoch:return
    if db.execute("SELECT 1 FROM jobs WHERE status IN ('READY','SENT') LIMIT 1").fetchone():
        raise ValueError('Version des sources changée : terminer ou annuler les tâches actives avant redécouverte.')
    with db:
        db.execute('DELETE FROM graph_cursors')
        db.execute('DELETE FROM fallback_cursors')
        db.execute("INSERT OR REPLACE INTO meta VALUES('source_epoch',?)",(epoch,))
        db.execute('INSERT INTO events(created_utc,kind,details) VALUES(?,?,?)',
                   (utc(),'SOURCE_EPOCH',json.dumps(parts)))
