"""Adaptateur *lecture seule* à l'index GLOBAL EncyK ; aucune seconde ingestion.

Le schéma EncyK est un index de découverte avec des arêtes agrégées :
ni statement_id, ni JSON original. Ne pas utiliser cet adaptateur comme preuve.
"""
from __future__ import annotations
import re
import sqlite3
import unicodedata
from pathlib import Path

QID = re.compile(r'^[QPL][0-9]+$')
OFFSETS = {'Q':0, 'P':1_000_000_000, 'L':2_000_000_000}
RANKS = {0:'deprecated', 1:'normal', 2:'preferred'}


def _eid(wid):
    if not isinstance(wid,str) or not QID.fullmatch(wid): return None
    return OFFSETS[wid[0]] + int(wid[1:])


def _wid(eid):
    n=int(eid)
    return ('L'+str(n-2_000_000_000) if n>=2_000_000_000 else
            'P'+str(n-1_000_000_000) if n>=1_000_000_000 else 'Q'+str(n))


def connect(path, readonly=True):
    """L'outil ne crée et ne modifie jamais un index EncyK."""
    if not readonly: raise ValueError('Skope intégré exige un index EncyK en lecture seule')
    p=Path(path).resolve(strict=True)
    if not p.is_file(): raise ValueError('Index attendu: fichier SQLite')
    conn=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True)
    conn.row_factory=sqlite3.Row
    try:
        tables={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'entity','name','entity_edge','meta'}.issubset(tables):
            raise ValueError('Index incompatible : schéma compact global EncyK attendu')
        m={r[0]:r[1] for r in conn.execute('SELECT key,value FROM meta')}
        if m.get('complete') not in ('1','true','True'):
            raise ValueError('Index EncyK incomplet : finalisation requise avant exploration')
        if m.get('lossless') not in (None, '0'):
            raise ValueError('Index de découverte EncyK attendu, pas dépôt de preuves')
        return conn
    except Exception:
        conn.close()
        raise


def meta(conn):
    d={r[0]:r[1] for r in conn.execute('SELECT key,value FROM meta ORDER BY key')}
    d['adapter']='skope-encyk-readonly/1.0'
    d['entity_count']=d.get('processed_entities','0')
    d['evidence_available']='false'
    d['edge_granularity']='aggregated'
    if d.get('dump_sha1'):
        d['source_snapshot_digest']='sha1:'+d['dump_sha1']
        d['source_identity_strength']='digest_from_index_metadata_not_revalidated'
    else:
        d['source_snapshot_digest']='unverified:'+str(d.get('dump_file') or 'unknown')
        d['source_identity_strength']='unverified'
    return d


def node(conn,qid,lang='fr'):
    eid=_eid(qid)
    if eid is None:return None
    r=conn.execute('SELECT wid,label_fr,label_en,label_mul,description_fr,description_en FROM entity WHERE id=?',(eid,)).fetchone()
    if r is None:return None
    aliases={}
    for a in conn.execute('SELECT lang,value FROM name WHERE entity_id=? AND name_kind=1 ORDER BY lang,value LIMIT 60',(eid,)):
        aliases.setdefault(a['lang'],[]).append(a['value'])
    label=(r['label_fr'] if lang=='fr' else r['label_en'] if lang=='en' else None) or r['label_fr'] or r['label_en'] or r['label_mul'] or qid
    desc=(r['description_fr'] if lang=='fr' else r['description_en']) or r['description_fr'] or r['description_en'] or ''
    return {'id':qid,'label':label,'description':desc,'aliases':aliases,'lastrevid':None}


def _norm(s):
    v=unicodedata.normalize('NFKD',str(s).strip()[:120]); v=''.join(c for c in v if not unicodedata.combining(c))
    return ' '.join(re.sub(r'[^\w]+',' ',v.casefold()).split())


def find(conn,text,limit=15):
    """Recherche bornée sur l'index GLOBAL (jusqu'à 121 M d'entités).

    Un QID/PID/LID doit passer directement par entity.id. Pour les noms,
    forcer idx_name_norm et NE JAMAIS trier/joindre l'ensemble des correspondances :
    `DISTINCT e.wid ORDER BY e.wid` provoquait des scans/sorts gigantesques.
    Toutes les lectures sont faites via la connexion SQLite mode=ro.
    """
    query=str(text).strip()
    if not query:return []
    limit=max(1,min(50,int(limit)))
    direct=query.upper()
    if _eid(direct) is not None:
        match=node(conn,direct)
        return [match] if match else []
    key=_norm(query)
    if not key:return []
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='index' AND name='idx_name_norm'").fetchone():
        raise ValueError('Index de noms idx_name_norm absent : vérifier la finalisation de l’index EncyK (ne pas le recréer dans Skope).')
    # Exploite l'index des noms directement, sans ORDER BY ni jointure/sort.
    # L'égalité est prioritaire ; les préfixes sont servis seulement si besoin.
    # La borne supérieure évite les caractères joker LIKE et garantit l'index.
    seen=set()
    ids=[]
    cap=max(100,limit*12)
    def collect(rows):
        for row in rows:
            eid=int(row[0])
            if eid not in seen:
                seen.add(eid);ids.append(eid)
                if len(ids)>=limit:break
    collect(conn.execute('SELECT entity_id FROM name INDEXED BY idx_name_norm WHERE norm = ? LIMIT ?', (key,cap)))
    if len(ids)<limit:
        collect(conn.execute('SELECT entity_id FROM name INDEXED BY idx_name_norm WHERE norm >= ? AND norm < ? LIMIT ?', (key,key+'\uffff',cap)))
    results=[]
    for eid in ids:
        match=node(conn,_wid(eid))
        if match is not None:results.append(match)
    return results


def _edge(r,direction):
    s,t=_wid(r['subject_id']),_wid(r['target_id'])
    return {'source':s,'target':t,'pid':f"P{r['property_id']}",
        'statement_id':None,'rank':RANKS.get(r['best_rank'],'normal'),
        'statement_count':r['statement_count'],
        'evidence_detail':'aggregated_index_not_statement_evidence',
        'direction':direction,'neighbor':t if direction=='out' else s}


def neighbors(conn,qid,direction='both',pids=None):
    if direction not in ('in','out','both'):raise ValueError('invalid direction')
    eid=_eid(qid)
    if eid is None:return []
    allowed=set(pids) if pids is not None else None
    result=[]
    if direction in ('out','both'):
        for r in conn.execute('SELECT * FROM entity_edge WHERE subject_id=? ORDER BY property_id,target_id',(eid,)):
            e=_edge(r,'out')
            if allowed is None or e['pid'] in allowed:result.append(e)
    if direction in ('in','both'):
        for r in conn.execute('SELECT * FROM entity_edge WHERE target_id=? ORDER BY property_id,subject_id',(eid,)):
            e=_edge(r,'in')
            if allowed is None or e['pid'] in allowed:result.append(e)
    return sorted(result,key=lambda r:(r['direction'],r['pid'],r['neighbor']))


def induced_edges(conn,selected):
    if not selected:return []
    out={}
    ids=sorted(v for v in (_eid(q) for q in selected) if v is not None)
    for offset in range(0,len(ids),400):
        chunk=ids[offset:offset+400]; marks=','.join(['?']*len(chunk))
        for r in conn.execute(f'SELECT * FROM entity_edge WHERE subject_id IN ({marks}) ORDER BY subject_id,property_id,target_id',chunk):
            edge=_edge(r,'out')
            if edge['target'] in selected:
                edge.pop('neighbor');edge.pop('direction');out[(edge['source'],edge['pid'],edge['target'])]=edge
    return list(out.values())
