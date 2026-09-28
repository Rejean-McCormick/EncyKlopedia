from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
from harvestlib import *

FILES=[
 'people.jsonl','people.unresolved.jsonl','people.relation-coverage.csv','people.summary.json',
 'works.jsonl','person-work-edges.jsonl','works.type-distribution.csv','works.summary.json',
 'currents.jsonl','domains.jsonl','influence-edges.jsonl','intellectual-context.summary.json','run-manifest.json'
]

def main():
    ap=argparse.ArgumentParser(description='Freeze a content-addressed immutable source snapshot for Da\'at/Kristal ingestion.')
    ap.add_argument('--root',default=''); ap.add_argument('--run-dir',required=True); ap.add_argument('--config',default=''); ap.add_argument('--registry',default=''); ap.add_argument('--qid-map',default=''); ap.add_argument('--db',default='')
    a=ap.parse_args(); root=find_root(a.root or None); run=Path(a.run_dir)
    cfgp=Path(a.config) if a.config else root/'00_system/tools/encyklopedia-kristal-ingest/config/harvest.default.json'; reg=Path(a.registry) if a.registry else root/'10_sources/seeds/active/intellectual-registry/intellectuals.seed.json'; qmp=Path(a.qid_map) if a.qid_map else root/'30_working/registry/qid-map.local.json'; db=Path(a.db) if a.db else root/'30_working/wikidata/wikidata.compact.sqlite'
    c=open_db(db); meta=assert_db_ready(c,False); c.close()
    inputs={'registry':{'path':relpath(reg,root),'sha256':sha256_file(reg)},'qid_map':{'path':relpath(qmp,root),'sha256':sha256_file(qmp)},'harvest_config':{'path':relpath(cfgp,root),'sha256':sha256_file(cfgp)},'wikidata_index':{'path':relpath(db,root),'schema_version':meta.get('schema_version'),'dump_file':meta.get('dump_file'),'dump_sha1':meta.get('dump_sha1'),'processed_entities':meta.get('processed_entities')}}
    build_files=files_manifest(run,FILES); seed=json.dumps({'inputs':inputs,'files':build_files},sort_keys=True,separators=(',',':')).encode(); digest=hashlib.sha256(seed).hexdigest(); snap_id=f"encyklopedia_{digest[:16]}"
    out=root/'20_ingest/snapshots/encyklopedia'/snap_id
    if out.exists():
        print(json.dumps({'snapshot_id':snap_id,'out':str(out),'reused':True},indent=2)); return
    copy_snapshot(run,out,[x['path'] for x in build_files])
    manifest={'schema_version':'encyklopedia-source-snapshot/v1','snapshot_id':snap_id,'created_at':utc_now(),'source_run':relpath(run,root),'authority':'immutable_source_export_for_daat_mapping','inputs':inputs,'files':files_manifest(out,[x['path'] for x in build_files]),'constraints':['Wikidata-derived statements remain source-bound claims.','This snapshot is not a Kristal Working or Reference Exchange.','Da\'at performs mapping into Kristal-native epistemic structures.']}
    save_json(out/'snapshot-manifest.json',manifest); save_json(root/'20_ingest/snapshots/encyklopedia/latest.json',{'snapshot_id':snap_id,'path':relpath(out,root),'manifest_sha256':sha256_file(out/'snapshot-manifest.json'),'updated_at':utc_now()})
    print(json.dumps({'snapshot_id':snap_id,'out':str(out),'manifest':str(out/'snapshot-manifest.json')},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
