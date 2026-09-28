#!/usr/bin/env python3
"""Build/finalize the EncyKlopedia GLOBAL DISCOVERY INDEX from a Wikidata JSON dump.

v0.10 performance rules:
- one sequential dump pass for semantic discovery data;
- build the dense QID locator in that same pass when possible;
- no redundant subject-prefix indexes on WITHOUT ROWID primary keys;
- SQL finalization is independent/restartable (--finalize-only);
- large CREATE INDEX sorts use disk TEMP, SQLite workers and heartbeats;
- PRAGMA optimize replaces unconditional full ANALYZE.

This DB is intentionally lossy and is never the evidence source. Complete selected entities
are later extracted losslessly from the raw dump.
"""
from __future__ import annotations

import argparse, contextlib, json, os, sqlite3, sys, time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import encode_wid, normalize_name, save_json, sha1_file
LIB=Path(__file__).resolve().parents[3]/'lib'
if str(LIB) not in sys.path: sys.path.insert(0,str(LIB))
import encyklopedia_fast as fastio

CHRONO_PIDS = {569, 570, 1317}
RANK_CODE = {"deprecated": 0, "normal": 1, "preferred": 2}

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS entity(
  id INTEGER PRIMARY KEY,
  wid TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL,
  label_fr TEXT,
  label_en TEXT,
  label_mul TEXT,
  description_fr TEXT,
  description_en TEXT
);
CREATE TABLE IF NOT EXISTS name(
  entity_id INTEGER NOT NULL,
  lang TEXT NOT NULL,
  name_kind INTEGER NOT NULL,
  value TEXT NOT NULL,
  norm TEXT NOT NULL,
  PRIMARY KEY(entity_id, lang, name_kind, value)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS claim_presence(
  subject_id INTEGER NOT NULL,
  property_id INTEGER NOT NULL,
  datatype TEXT,
  statement_count INTEGER NOT NULL,
  preferred_count INTEGER NOT NULL,
  normal_count INTEGER NOT NULL,
  deprecated_count INTEGER NOT NULL,
  PRIMARY KEY(subject_id, property_id)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS entity_edge(
  subject_id INTEGER NOT NULL,
  property_id INTEGER NOT NULL,
  target_id INTEGER NOT NULL,
  statement_count INTEGER NOT NULL,
  best_rank INTEGER NOT NULL,
  PRIMARY KEY(subject_id, property_id, target_id)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS chronology(
  subject_id INTEGER NOT NULL,
  property_id INTEGER NOT NULL,
  year INTEGER,
  precision INTEGER,
  PRIMARY KEY(subject_id, property_id, year, precision)
) WITHOUT ROWID;
"""

FINAL_INDEXES = [
    ("idx_name_norm", "CREATE INDEX IF NOT EXISTS idx_name_norm ON name(norm)"),
    ("idx_presence_property", "CREATE INDEX IF NOT EXISTS idx_presence_property ON claim_presence(property_id, subject_id)"),
    ("idx_edge_target_property", "CREATE INDEX IF NOT EXISTS idx_edge_target_property ON entity_edge(target_id, property_id, subject_id)"),
]


def txt(d: dict[str,Any], lang: str) -> str | None:
    v=d.get(lang); return v.get('value') if isinstance(v,dict) else None


def parse_year(v: Any) -> tuple[int|None,int|None]:
    if not isinstance(v,dict): return None,None
    t=v.get('time'); precision=v.get('precision')
    if not isinstance(t,str): return None,precision
    import re
    m=re.match(r'^([+-])(\d+)-',t)
    if not m: return None,precision
    y=int(m.group(2)); return (-y if m.group(1)=='-' else y), precision


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA cache_size=-524288")
    try: conn.execute("PRAGMA mmap_size=2147483648")
    except sqlite3.DatabaseError: pass


def existing_progress(conn: sqlite3.Connection) -> int:
    row=conn.execute("SELECT value FROM meta WHERE key='processed_entities'").fetchone()
    return int(row[0]) if row else 0


def get_meta(conn:sqlite3.Connection,k:str,default:str='')->str:
    row=conn.execute("SELECT value FROM meta WHERE key=?",(k,)).fetchone()
    return row[0] if row else default


def set_meta(conn: sqlite3.Connection, k:str,v:Any) -> None:
    conn.execute("INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(k,str(v)))


def process_entity(e:dict[str,Any], langs:list[str]):
    wid=e.get('id'); eid=encode_wid(wid)
    if eid is None: return None
    labels=e.get('labels') or {}; desc=e.get('descriptions') or {}; aliases=e.get('aliases') or {}
    ent=(eid,wid,e.get('type') or 'unknown',txt(labels,'fr'),txt(labels,'en'),txt(labels,'mul'),txt(desc,'fr'),txt(desc,'en'))
    names=[]; seen=set()
    for lang in langs:
        lab=txt(labels,lang)
        if lab:
            key=(lang,0,lab)
            if key not in seen: names.append((eid,lang,0,lab,normalize_name(lab))); seen.add(key)
        for a in aliases.get(lang) or []:
            val=a.get('value') if isinstance(a,dict) else None
            if val:
                key=(lang,1,val)
                if key not in seen: names.append((eid,lang,1,val,normalize_name(val))); seen.add(key)
    presence=[]; edge_counts=defaultdict(lambda:[0,0]); chrono=[]
    for pid_s, statements in (e.get('claims') or {}).items():
        if not (pid_s.startswith('P') and pid_s[1:].isdigit()): continue
        pid=int(pid_s[1:]); ranks=Counter(); datatype=None
        for st in statements:
            rank=st.get('rank') or 'normal'; ranks[rank]+=1
            sn=(st.get('mainsnak') or {}); datatype=datatype or sn.get('datatype')
            if sn.get('snaktype')!='value': continue
            dv=sn.get('datavalue') or {}; value=dv.get('value')
            if dv.get('type')=='wikibase-entityid' and isinstance(value,dict):
                target=value.get('id')
                if not target and value.get('numeric-id') is not None:
                    et=value.get('entity-type','item'); prefix={'item':'Q','property':'P','lexeme':'L'}.get(et)
                    if prefix: target=f"{prefix}{value['numeric-id']}"
                tid=encode_wid(target)
                if tid is not None:
                    rec=edge_counts[(pid,tid)]; rec[0]+=1; rec[1]=max(rec[1],RANK_CODE.get(rank,1))
            if pid in CHRONO_PIDS and dv.get('type')=='time':
                year,precision=parse_year(value)
                if year is not None: chrono.append((eid,pid,year,precision))
        presence.append((eid,pid,datatype,len(statements),ranks['preferred'],ranks['normal'],ranks['deprecated']))
    edges=[(eid,pid,tid,c,best) for (pid,tid),(c,best) in edge_counts.items()]
    return ent,names,presence,edges,chrono


def finalize_db(conn:sqlite3.Connection,db:Path,threads:int,temp_dir:Path|None,skip_optimize:bool=False)->None:
    if temp_dir:
        temp_dir.mkdir(parents=True,exist_ok=True)
        os.environ['TEMP']=str(temp_dir); os.environ['TMP']=str(temp_dir)
    workers=threads or min(max(1,fastio.recommended_threads(None)),12)
    try:
        print('[finalize] checkpoint WAL...',flush=True)
        print('[finalize] checkpoint =',conn.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone(),flush=True)
    except sqlite3.DatabaseError as exc:
        print(f'[finalize] checkpoint note: {exc}',flush=True)
    try: print('[finalize] journal_mode =',conn.execute('PRAGMA journal_mode=DELETE').fetchone()[0],flush=True)
    except sqlite3.DatabaseError: pass
    conn.execute('PRAGMA synchronous=NORMAL')
    conn.execute('PRAGMA temp_store=FILE')
    conn.execute('PRAGMA cache_size=-2097152')
    try: conn.execute('PRAGMA mmap_size=4294967296')
    except sqlite3.DatabaseError: pass
    try: conn.execute(f'PRAGMA threads={workers}')
    except sqlite3.DatabaseError: pass
    existing={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    for name,sql in FINAL_INDEXES:
        if name in existing:
            print(f'[finalize] {name}: déjà présent -> skip',flush=True); continue
        print(f'[finalize] {name}: début',flush=True)
        started=time.time(); last=[0.0]
        def heartbeat():
            elapsed=time.time()-started
            if elapsed-last[0]>=20:
                last[0]=elapsed
                print(f'[finalize] {name} | {elapsed/60:.1f} min | db={db.stat().st_size/1024**3:.2f} GiB',flush=True)
            return 0
        conn.set_progress_handler(heartbeat,500000)
        conn.execute(sql); conn.commit(); conn.set_progress_handler(None,0)
        set_meta(conn,f'index.{name}.complete','1'); set_meta(conn,f'index.{name}.completed_at',datetime.now(timezone.utc).isoformat()); conn.commit()
        print(f'[finalize] {name}: terminé en {(time.time()-started)/60:.1f} min',flush=True)
    if not skip_optimize:
        print('[finalize] PRAGMA optimize (pas de full ANALYZE)...',flush=True)
        try:
            conn.execute('PRAGMA analysis_limit=1000')
            conn.execute('PRAGMA optimize')
            conn.commit()
        except sqlite3.DatabaseError as exc:
            print(f'[finalize] optimize note: {exc}',flush=True)
    set_meta(conn,'index_strategy','global-discovery-v4-optimized')
    set_meta(conn,'complete','1'); set_meta(conn,'completed_at',datetime.now(timezone.utc).isoformat()); conn.commit()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--dump',default=''); ap.add_argument('--db',required=True)
    ap.add_argument('--languages',default='fr,en,mul'); ap.add_argument('--commit-every',type=int,default=5000)
    ap.add_argument('--state',default=''); ap.add_argument('--fresh',action='store_true'); ap.add_argument('--skip-sha1',action='store_true')
    ap.add_argument('--threads',type=int,default=0); ap.add_argument('--root',default=''); ap.add_argument('--temp-dir',default='')
    ap.add_argument('--finalize-only',action='store_true'); ap.add_argument('--skip-optimize',action='store_true'); ap.add_argument('--no-locator',action='store_true')
    ap.add_argument('--initial-qid-capacity',type=int,default=160_000_000)
    a=ap.parse_args(); db=Path(a.db); state=Path(a.state) if a.state else db.with_suffix('.state.json'); root=Path(a.root) if a.root else None
    temp_dir=Path(a.temp_dir) if a.temp_dir else None
    if a.finalize_only:
        if not db.exists(): raise FileNotFoundError(db)
        conn=sqlite3.connect(db,timeout=600); conn.execute('PRAGMA busy_timeout=600000')
        try: finalize_db(conn,db,a.threads,temp_dir,a.skip_optimize)
        finally: conn.close()
        print(json.dumps({'complete':True,'finalize_only':True,'db':str(db),'db_bytes':db.stat().st_size},indent=2)); return
    if not a.dump: raise SystemExit('--dump requis sauf avec --finalize-only')
    dump=Path(a.dump)
    if a.fresh:
        for p in (db,db.with_name('qid-locator.bin'),db.with_name('compression.gzindex'),db.with_name('compression.bz2blocks.pkl'),db.with_name('fast-sidecars.json')):
            try:p.unlink()
            except FileNotFoundError:pass
    db.parent.mkdir(parents=True,exist_ok=True); langs=[x.strip() for x in a.languages.split(',') if x.strip()]
    conn=sqlite3.connect(db,timeout=600); init_db(conn); skip=existing_progress(conn)
    have_indexes={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    if get_meta(conn,'complete') in {'1','true','True'} and all(name in have_indexes for name,_ in FINAL_INDEXES):
        print(json.dumps({'complete':True,'reused':True,'entities':skip,'db':str(db),'db_bytes':db.stat().st_size},indent=2),flush=True); conn.close(); return
    caps=fastio.backend_capabilities(dump,root)
    set_meta(conn,'performance_backend',json.dumps(caps)); set_meta(conn,'json_backend',fastio.json_backend()); set_meta(conn,'schema_version','encyklopedia-wikidata-compact-index/v1')
    set_meta(conn,'dump_file',dump.name); set_meta(conn,'languages',','.join(langs)); set_meta(conn,'index_role','global_discovery_map'); set_meta(conn,'lossless','0'); set_meta(conn,'evidence_source','raw_wikidata_dump'); conn.commit()
    print(f"[index] reprise: {skip} entités déjà validées",flush=True)
    locator=db.parent/'qid-locator.bin'; compression=db.parent/('compression.gzindex' if dump.name.lower().endswith('.gz') else 'compression.bz2blocks.pkl')
    locator_enabled=not a.no_locator
    if skip and locator_enabled and not locator.exists():
        print('[index] locator désactivé pour cette reprise: DB partielle existante mais aucun locator antérieur. Le prochain build frais le créera en one-pass.',flush=True)
        locator_enabled=False
    locator_max=int(get_meta(conn,'locator_max_qid','0') or 0)
    writer_cm=fastio.DenseQidLocatorWriter(locator,a.initial_qid_capacity,resume=bool(skip and locator.exists()),max_seen=locator_max) if locator_enabled else contextlib.nullcontext(None)
    batch_e=[];batch_n=[];batch_p=[];batch_edge=[];batch_c=[]; processed=0; inserted=skip; started=time.time(); locator_writer=None
    def flush():
        nonlocal batch_e,batch_n,batch_p,batch_edge,batch_c,inserted
        conn.executemany("INSERT OR REPLACE INTO entity VALUES(?,?,?,?,?,?,?,?)",batch_e)
        conn.executemany("INSERT OR IGNORE INTO name VALUES(?,?,?,?,?)",batch_n)
        conn.executemany("INSERT OR REPLACE INTO claim_presence VALUES(?,?,?,?,?,?,?)",batch_p)
        conn.executemany("INSERT OR REPLACE INTO entity_edge VALUES(?,?,?,?,?)",batch_edge)
        conn.executemany("INSERT OR IGNORE INTO chronology VALUES(?,?,?,?)",batch_c)
        set_meta(conn,'processed_entities',inserted); set_meta(conn,'updated_at',datetime.now(timezone.utc).isoformat())
        if locator_writer is not None:set_meta(conn,'locator_max_qid',locator_writer.max_seen)
        conn.commit(); save_json(state,{'processed_entities':inserted,'db':str(db),'dump':str(dump),'complete':False,'updated_at':datetime.now(timezone.utc).isoformat()})
        print(f"[index] committed {inserted:,} entities | db={db.stat().st_size/1024**3:.2f} GiB",flush=True)
        batch_e=[];batch_n=[];batch_p=[];batch_edge=[];batch_c=[]
    try:
        with writer_cm as lw:
            locator_writer=lw
            for raw,offset,length,backend in fastio.iter_dump_raw(dump,threads=a.threads,index_path=compression if compression.exists() else None,root=root,with_offsets=True,export_index_path=compression):
                processed+=1
                if processed<=skip: continue
                try:e=fastio.loads(raw)
                except Exception as exc:
                    print(f'[warn] JSON ignoré: {exc}',file=sys.stderr,flush=True); inserted=processed; continue
                wid=e.get('id')
                if lw is not None and isinstance(wid,str) and wid.startswith('Q') and wid[1:].isdigit(): lw.set(int(wid[1:]),offset,length)
                rec=process_entity(e,langs); inserted=processed
                if rec:
                    ent,n,p,ed,c=rec; batch_e.append(ent);batch_n.extend(n);batch_p.extend(p);batch_edge.extend(ed);batch_c.extend(c)
                if inserted % a.commit_every==0: flush()
            if batch_e or batch_p: flush()
        if locator_enabled and locator.exists():
            save_json(db.parent/'fast-sidecars.json',{'schema_version':'encyklopedia-global-fast-sidecars/v1','complete':True,'dump_file':dump.name,'locator_file':locator.name,'locator_bytes':locator.stat().st_size,'compression_index_file':compression.name if compression.exists() else None,'backend':caps,'created_at':datetime.now(timezone.utc).isoformat()})
        print('[index] finalisation SQL optimisée...',flush=True); finalize_db(conn,db,a.threads,temp_dir,a.skip_optimize)
        if not a.skip_sha1:
            print('[index] calcul SHA1 source...',flush=True); set_meta(conn,'dump_sha1',sha1_file(dump)); conn.commit()
        save_json(state,{'processed_entities':inserted,'db':str(db),'dump':str(dump),'complete':True,'completed_at':datetime.now(timezone.utc).isoformat()})
        print(json.dumps({'complete':True,'entities':inserted,'db':str(db),'db_bytes':db.stat().st_size,'locator':str(locator) if locator_enabled else None,'elapsed_seconds':round(time.time()-started,1)},indent=2),flush=True)
    finally: conn.close()

if __name__=='__main__': main()
