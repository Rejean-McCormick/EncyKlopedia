from __future__ import annotations
import argparse, gzip, json, os, sqlite3, time
from pathlib import Path
from scope_common import *

SCHEMA='''
CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE entity(
  wid TEXT PRIMARY KEY,
  entity_type TEXT,
  labels_json TEXT NOT NULL,
  descriptions_json TEXT NOT NULL,
  aliases_json TEXT NOT NULL,
  sitelinks_json TEXT NOT NULL,
  raw_sha256 TEXT NOT NULL
);
CREATE TABLE name(
  wid TEXT NOT NULL, lang TEXT NOT NULL, name_kind TEXT NOT NULL, value TEXT NOT NULL, norm TEXT NOT NULL,
  PRIMARY KEY(wid,lang,name_kind,value)
) WITHOUT ROWID;
CREATE TABLE statement(
  statement_key TEXT PRIMARY KEY,
  statement_id TEXT,
  subject_wid TEXT NOT NULL,
  property_id TEXT NOT NULL,
  rank TEXT,
  snaktype TEXT,
  datatype TEXT,
  value_type TEXT,
  value_entity_wid TEXT,
  value_json TEXT,
  qualifiers_json TEXT NOT NULL,
  references_json TEXT NOT NULL,
  raw_json TEXT NOT NULL
);
CREATE TABLE edge(
  subject_wid TEXT NOT NULL, property_id TEXT NOT NULL, target_wid TEXT NOT NULL, statement_key TEXT NOT NULL,
  PRIMARY KEY(subject_wid,property_id,target_wid,statement_key)
) WITHOUT ROWID;
CREATE TABLE literal_value(
  subject_wid TEXT NOT NULL, property_id TEXT NOT NULL, statement_key TEXT NOT NULL, datatype TEXT, value_type TEXT, value_json TEXT,
  PRIMARY KEY(subject_wid,property_id,statement_key)
) WITHOUT ROWID;
CREATE TABLE scope_role(
  wid TEXT NOT NULL, role TEXT NOT NULL, first_depth INTEGER NOT NULL,
  PRIMARY KEY(wid,role)
) WITHOUT ROWID;
'''
INDEXES=[
 ('idx_name_norm','CREATE INDEX idx_name_norm ON name(norm)'),
 ('idx_statement_subject','CREATE INDEX idx_statement_subject ON statement(subject_wid,property_id)'),
 ('idx_statement_property','CREATE INDEX idx_statement_property ON statement(property_id,subject_wid)'),
 ('idx_statement_target','CREATE INDEX idx_statement_target ON statement(value_entity_wid,property_id,subject_wid) WHERE value_entity_wid IS NOT NULL'),
 ('idx_literal_property','CREATE INDEX idx_literal_property ON literal_value(property_id,subject_wid)'),
 ('idx_scope_role_role','CREATE INDEX idx_scope_role_role ON scope_role(role,wid)'),
]
VIEWS='''
CREATE VIEW v_people AS SELECT e.*,r.role,r.first_depth FROM entity e JOIN scope_role r ON r.wid=e.wid WHERE r.role IN ('person_root','person_or_influence');
CREATE VIEW v_works AS SELECT e.*,r.role,r.first_depth FROM entity e JOIN scope_role r ON r.wid=e.wid WHERE r.role='work';
CREATE VIEW v_intellectual_context AS SELECT e.*,r.role,r.first_depth FROM entity e JOIN scope_role r ON r.wid=e.wid WHERE r.role IN ('movement','field','occupation','worldview','intellectual_context');
CREATE VIEW v_places_institutions AS SELECT e.*,r.role,r.first_depth FROM entity e JOIN scope_role r ON r.wid=e.wid WHERE r.role IN ('place','country','institution','institution_or_group','place_or_institution_context');
'''


def entity_target(value):
    if not isinstance(value,dict): return None
    if isinstance(value.get('id'),str): return value['id']
    if value.get('numeric-id') is not None:
        prefix={'item':'Q','property':'P','lexeme':'L','form':'L','sense':'L'}.get(value.get('entity-type'))
        if prefix: return f"{prefix}{value['numeric-id']}"
    return None


def main():
    ap=argparse.ArgumentParser(description='Build an optional query-friendly project SQLite from lossless evidence. v0.10 batches writes and atomically publishes the derived DB.')
    ap.add_argument('--root',default=''); ap.add_argument('--scope',required=True); ap.add_argument('--snapshot-id',default=''); ap.add_argument('--fresh',action='store_true')
    ap.add_argument('--batch-entities',type=int,default=500); ap.add_argument('--threads',type=int,default=0)
    a=ap.parse_args(); root=find_root(a.root or None); _,cfg=load_scope_config(root,a.scope); key=cfg['scope_key']; wd=scope_workdir(root,key)
    latest=load_json(wd/'evidence.latest.json',{}) or {}; sid=a.snapshot_id or latest.get('snapshot_id')
    if not sid: raise SystemExit('Aucun evidence snapshot. Exécute 04_extract_evidence.py.')
    snap=scope_snapshot_dir(root,key,sid); manifest=load_json(snap/'snapshot-manifest.json',{}) or {}; ev=snap/'entities.wikidata.jsonl.gz'
    if not ev.exists(): raise FileNotFoundError(ev)
    outdir=wd/'index'; outdir.mkdir(parents=True,exist_ok=True); db=outdir/f'{key}.sqlite'; tmp=db.with_suffix('.sqlite.tmp')
    try: tmp.unlink()
    except FileNotFoundError: pass
    workers=a.threads or performance_status(root).get('recommended_threads') or 4
    c=sqlite3.connect(tmp,timeout=120); c.row_factory=sqlite3.Row
    try:
        # Safe because tmp is a fully derived/reproducible artifact; publish happens only after success.
        c.execute('PRAGMA journal_mode=OFF'); c.execute('PRAGMA synchronous=OFF'); c.execute('PRAGMA temp_store=MEMORY'); c.execute('PRAGMA cache_size=-1048576')
        try:c.execute('PRAGMA mmap_size=2147483648'); c.execute(f'PRAGMA threads={int(workers)}')
        except sqlite3.DatabaseError:pass
        c.executescript(SCHEMA)
        c.executemany('INSERT INTO meta VALUES(?,?)',[
            ('schema_version','encyklopedia-project-index/v2'),('scope_key',key),('snapshot_id',sid),('evidence_sha256',manifest.get('evidence_sha256','')),('complete','0')])
        roles=[]
        for rr in read_jsonl(wd/'discovery/entities.jsonl'):
            for role in rr.get('roles') or []:roles.append((rr.get('wid'),role,int(rr.get('first_depth') or 0)))
        c.executemany('INSERT OR IGNORE INTO scope_role VALUES(?,?,?)',roles)
        entities=statements=edges=literals=0; started=time.time()
        ent_b=[]; name_b=[]; st_b=[]; edge_b=[]; lit_b=[]
        def flush():
            nonlocal ent_b,name_b,st_b,edge_b,lit_b
            if ent_b:c.executemany('INSERT INTO entity VALUES(?,?,?,?,?,?,?)',ent_b)
            if name_b:c.executemany('INSERT OR IGNORE INTO name VALUES(?,?,?,?,?)',name_b)
            if st_b:c.executemany('INSERT INTO statement VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',st_b)
            if edge_b:c.executemany('INSERT OR IGNORE INTO edge VALUES(?,?,?,?)',edge_b)
            if lit_b:c.executemany('INSERT OR REPLACE INTO literal_value VALUES(?,?,?,?,?,?)',lit_b)
            ent_b=[];name_b=[];st_b=[];edge_b=[];lit_b=[]
        with gzip.open(ev,'rt',encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                e=json_loads(line); wid=e.get('id'); raw_sha=sha256_bytes(line.strip().encode('utf-8'))
                labels=e.get('labels') or {}; desc=e.get('descriptions') or {}; aliases=e.get('aliases') or {}; sitelinks=e.get('sitelinks') or {}
                ent_b.append((wid,e.get('type'),json.dumps(labels,ensure_ascii=False,sort_keys=True,separators=(',',':')),json.dumps(desc,ensure_ascii=False,sort_keys=True,separators=(',',':')),json.dumps(aliases,ensure_ascii=False,sort_keys=True,separators=(',',':')),json.dumps(sitelinks,ensure_ascii=False,sort_keys=True,separators=(',',':')),raw_sha)); entities+=1
                for lang,v in labels.items():
                    if isinstance(v,dict) and v.get('value'):name_b.append((wid,lang,'label',v['value'],normalize_name(v['value'])))
                for lang,vals in aliases.items():
                    for v in vals or []:
                        if isinstance(v,dict) and v.get('value'):name_b.append((wid,lang,'alias',v['value'],normalize_name(v['value'])))
                for pid,sts in (e.get('claims') or {}).items():
                    for ordinal,st in enumerate(sts or []):
                        sn=st.get('mainsnak') or {}; dv=sn.get('datavalue') or {}; value=dv.get('value'); target=entity_target(value) if dv.get('type')=='wikibase-entityid' else None
                        stid=st.get('id'); skey=stid or f'{wid}|{pid}|{ordinal}'; vjson=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')) if 'value' in dv else None
                        st_b.append((skey,stid,wid,pid,st.get('rank'),sn.get('snaktype'),sn.get('datatype'),dv.get('type'),target,vjson,json.dumps(st.get('qualifiers') or {},ensure_ascii=False,sort_keys=True,separators=(',',':')),json.dumps(st.get('references') or [],ensure_ascii=False,sort_keys=True,separators=(',',':')),json.dumps(st,ensure_ascii=False,sort_keys=True,separators=(',',':')))); statements+=1
                        if target:edge_b.append((wid,pid,target,skey)); edges+=1
                        elif sn.get('snaktype')=='value':lit_b.append((wid,pid,skey,sn.get('datatype'),dv.get('type'),vjson)); literals+=1
                if entities%max(1,a.batch_entities)==0:
                    flush(); print(f'[scope-index] entities={entities:,} statements={statements:,} edges={edges:,} literals={literals:,} elapsed={(time.time()-started)/60:.1f}m',flush=True)
        flush()
        print('[scope-index] création des indexes dérivés...',flush=True)
        for name,sql in INDEXES:
            t=time.time(); c.execute(sql); print(f'[scope-index] {name}: {(time.time()-t):.1f}s',flush=True)
        c.executescript(VIEWS)
        try:c.execute('PRAGMA optimize')
        except sqlite3.DatabaseError:pass
        c.execute("UPDATE meta SET value='1' WHERE key='complete'"); c.execute('INSERT INTO meta VALUES(?,?)',('completed_at',utc_now())); c.commit(); c.close(); c=None
        os.replace(tmp,db)
    except Exception:
        if c is not None:c.close()
        try:tmp.unlink()
        except FileNotFoundError:pass
        raise
    report={'schema_version':'encyklopedia-project-index-report/v2','scope_key':key,'snapshot_id':sid,'db':str(db.relative_to(root)).replace('\\','/'),'db_bytes':db.stat().st_size,'entities':entities,'statements':statements,'edges':edges,'literal_values':literals,'workers':workers,'complete':True,'completed_at':utc_now()}; save_json(outdir/'index-manifest.json',report); print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
