from __future__ import annotations
import argparse, json, os, shutil, sqlite3, sys, time
from collections import defaultdict
from pathlib import Path

HERE=Path(__file__).resolve(); ROOT0=HERE.parents[4]
LIB=ROOT0/'00_system/lib'; SCOPES=ROOT0/'00_system/tools/scope-builder/scripts'
for p in (LIB,SCOPES):
    if str(p) not in sys.path:sys.path.insert(0,str(p))
import encyklopedia_fast as fastio
from scope_common import (find_root,find_dump,dump_descriptor,fast_access_dir,fast_access_status,
                          entity_edges_from_obj,raw_entity_id,utc_now,save_json,global_index_status)

RANK={'deprecated':0,'normal':1,'preferred':2}


def main():
    ap=argparse.ArgumentParser(description='Build the lossless random-access sidecars. v0.10 avoids duplicating reverse-edge SQL when the global discovery index exists.')
    ap.add_argument('--root',default=''); ap.add_argument('--dump',default=''); ap.add_argument('--threads',type=int,default=0)
    ap.add_argument('--reverse-properties',default='P50,P170'); ap.add_argument('--initial-qid-capacity',type=int,default=160_000_000)
    ap.add_argument('--force',action='store_true'); ap.add_argument('--allow-sequential-locator',action='store_true',help='Permit a full sequential dump scan even when the installed decompressor cannot random-seek. Usually not useful on the current .bz2.')
    ap.add_argument('--force-reverse-sidecar',action='store_true',help='Build the legacy reverse_edge SQLite even if the global discovery index already provides reverse lookup.')
    a=ap.parse_args(); root=find_root(a.root or None); dump=Path(a.dump) if a.dump else find_dump(root); desc=dump_descriptor(root,dump); out=fast_access_dir(root,dump)
    caps=fastio.backend_capabilities(dump,root); threads=a.threads or fastio.recommended_threads(root)
    already_ok,already=fast_access_status(root,dump)
    if already_ok and already.get('random_access_ready') and not a.force:
        print(json.dumps({'complete':True,'reused':True,'random_access_ready':True,'source':already.get('locator_source'),'path':already.get('path')},indent=2));return
    if not caps.get('random_access') and not a.allow_sequential_locator:
        raise SystemExit(
            'Fast-access non construit: le backend courant (%s) ne sait pas seek dans %s. '
            'Aucun scan de 121M entités ne sera lancé silencieusement. Installe indexed_bzip2 / utilise un dump .json.gz + rapidgzip, '
            'ou passe --allow-sequential-locator uniquement si tu acceptes explicitement un scan complet.' % (caps.get('backend'),dump.name)
        )
    if out.exists() and not a.force:
        man=out/'manifest.json'
        if man.exists() and (json.loads(man.read_text(encoding='utf-8')).get('complete')):
            print(json.dumps({'complete':True,'reused':True,'path':str(out)},indent=2));return
        raise SystemExit(f'Fast-access staging/partial directory exists: {out}. Use --force to rebuild.')
    tmp=out.with_name(out.name+'.tmp'); shutil.rmtree(tmp,ignore_errors=True); tmp.mkdir(parents=True,exist_ok=True)
    global_ok,_=global_index_status(root)
    build_reverse=bool(a.force_reverse_sidecar or not global_ok)
    reverse_props={x.strip() for x in a.reverse_properties.split(',') if x.strip()} if build_reverse else set()
    prop_needles={p:f'"{p}"'.encode() for p in reverse_props}
    db=None; batch=[]; reverse_rows=0
    if build_reverse:
        db=sqlite3.connect(tmp/'fast-index.sqlite'); db.execute('PRAGMA journal_mode=OFF'); db.execute('PRAGMA synchronous=OFF'); db.execute('PRAGMA temp_store=MEMORY'); db.execute('PRAGMA cache_size=-262144')
        db.executescript('CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL); CREATE TABLE reverse_edge(property_id INTEGER NOT NULL,target_id INTEGER NOT NULL,source_id INTEGER NOT NULL,statement_count INTEGER NOT NULL,best_rank INTEGER NOT NULL,PRIMARY KEY(property_id,target_id,source_id)) WITHOUT ROWID;')
    compression_idx=tmp/('compression.gzindex' if dump.name.lower().endswith('.gz') else 'compression.bz2blocks.pkl')
    locator=tmp/'qid-locator.bin'; scanned=qitems=parsed=0; started=time.time(); last=started; max_qid=0
    print(json.dumps({'mode':'build_fast_access_v010','dump':desc,'backend':caps,'threads':threads,'json_backend':fastio.json_backend(),'reverse_sidecar':build_reverse,'reverse_properties':sorted(reverse_props)},ensure_ascii=False,indent=2),flush=True)
    try:
      with fastio.DenseQidLocatorWriter(locator,a.initial_qid_capacity) as lw:
       with fastio.DumpStream(dump,threads=threads,index_path=None,root=root) as ds:
        while True:
          start=ds.tell(); rawline=ds.readline()
          if not rawline:break
          length=ds.tell()-start; raw=fastio.normalize_dump_line(rawline)
          if raw is None:continue
          scanned+=1; wid=raw_entity_id(raw)
          if not wid:continue
          if wid.startswith('Q') and wid[1:].isdigit():
            q=int(wid[1:]); lw.set(q,start,length); qitems+=1; max_qid=max(max_qid,q)
          if reverse_props and any(n in raw for n in prop_needles.values()):
            try: obj=fastio.loads(raw); parsed+=1
            except Exception: obj=None
            if isinstance(obj,dict) and wid.startswith('Q') and wid[1:].isdigit():
              src=int(wid[1:]); agg=defaultdict(lambda:[0,0])
              for e in entity_edges_from_obj(obj,reverse_props):
                tw=e.get('target_wid'); pid=e.get('property_id')
                if not (tw and tw.startswith('Q') and tw[1:].isdigit() and pid and pid.startswith('P') and pid[1:].isdigit()):continue
                k=(int(pid[1:]),int(tw[1:])); agg[k][0]+=1; agg[k][1]=max(agg[k][1],RANK.get(e.get('rank'),1))
              for (pid,tid),(cnt,best) in agg.items():batch.append((pid,tid,src,cnt,best))
          if db is not None and len(batch)>=100000:
            db.executemany('INSERT OR REPLACE INTO reverse_edge VALUES(?,?,?,?,?)',batch);reverse_rows+=len(batch);batch.clear();db.commit()
          now=time.time()
          if now-last>=60:
            print(f'[fast-index] scanned={scanned:,} qitems={qitems:,} parsed={parsed:,} reverse_rows≈{reverse_rows+len(batch):,} elapsed={(now-started)/3600:.2f}h',flush=True);last=now
        if db is not None and batch:db.executemany('INSERT OR REPLACE INTO reverse_edge VALUES(?,?,?,?,?)',batch);reverse_rows+=len(batch);batch.clear();db.commit()
        try: ds.export_index(compression_idx)
        except Exception as e: print(f'[fast-index] compression index export skipped: {e}',flush=True)
      if db is not None:
        db.execute('CREATE INDEX idx_reverse_target_property ON reverse_edge(target_id,property_id,source_id)'); db.execute('PRAGMA optimize')
        for k,v in [('schema_version','encyklopedia-wikidata-fast-access/v2'),('dump_id',desc['dump_id']),('dump_file',dump.name),('complete','1'),('reverse_properties',','.join(sorted(reverse_props))),('max_qid',str(max_qid)),('backend',caps['backend'])]:db.execute('INSERT OR REPLACE INTO meta VALUES(?,?)',(k,v))
        db.commit()
    finally:
      if db is not None:db.close()
    manifest={'schema_version':'encyklopedia-wikidata-fast-access/v2','complete':True,'created_at':utc_now(),'dump':desc,'backend':caps,'json_backend':fastio.json_backend(),'threads':threads,'entity_lines_scanned':scanned,'q_items':qitems,'max_qid':max_qid,'locator_file':'qid-locator.bin','locator_bytes':locator.stat().st_size,'reverse_index_file':'fast-index.sqlite' if build_reverse else None,'reverse_properties':sorted(reverse_props),'reverse_rows':reverse_rows,'compression_index_file':compression_idx.name if compression_idx.exists() else None,'random_access_capable_at_build':bool(caps.get('random_access')),'reverse_lookup_source':'sidecar' if build_reverse else 'global-discovery-index','role':'derived acceleration only; raw dump remains evidence source'}
    save_json(tmp/'manifest.json',manifest); out.parent.mkdir(parents=True,exist_ok=True); shutil.rmtree(out,ignore_errors=True); os.replace(tmp,out)
    print(json.dumps({'complete':True,'path':str(out),**manifest},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
