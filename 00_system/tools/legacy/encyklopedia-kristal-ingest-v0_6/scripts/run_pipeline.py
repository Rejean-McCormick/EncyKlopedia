from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
from harvestlib import find_root, new_run_id, save_json, utc_now, relpath


def call(cmd:list[str]):
    print('\n$ '+' '.join(map(str,cmd)),flush=True)
    rc=subprocess.call([str(x) for x in cmd])
    if rc: raise SystemExit(rc)


def main():
    ap=argparse.ArgumentParser(description='People-first EncyKlopedia → Da\'at/Kristal handoff pipeline.')
    ap.add_argument('--root',default=''); ap.add_argument('--run-id',default=''); ap.add_argument('--kristal-root',default=''); ap.add_argument('--allow-partial-db',action='store_true'); ap.add_argument('--skip-resolve',action='store_true'); ap.add_argument('--skip-mediatheque',action='store_true')
    a=ap.parse_args(); root=find_root(a.root or None); scripts=Path(__file__).resolve().parent
    run_id=a.run_id or new_run_id(); run=root/'30_working/encyklopedia-harvest/runs'/run_id; run.mkdir(parents=True,exist_ok=True)
    save_json(run/'run-manifest.json',{'schema_version':'encyklopedia-harvest-run/v1','run_id':run_id,'started_at':utc_now(),'root':str(root),'working_dir':relpath(run,root)})
    common=['--root',str(root),'--run-dir',str(run)]
    if not a.skip_resolve: call([sys.executable,scripts/'01_resolve_people.py','--root',root])
    partial=['--allow-partial-db'] if a.allow_partial_db else []
    call([sys.executable,scripts/'02_extract_people.py',*common,*partial])
    call([sys.executable,scripts/'03_extract_works.py',*common,*partial])
    call([sys.executable,scripts/'04_extract_intellectual_context.py',*common,*partial])
    if not a.skip_mediatheque: call([sys.executable,scripts/'05_publish_mediatheque_candidates.py',*common,'--snapshot-name',run_id])
    call([sys.executable,scripts/'06_build_source_snapshot.py',*common])
    latest=json.loads((root/'20_ingest/snapshots/encyklopedia/latest.json').read_text(encoding='utf-8'))
    cmd=[sys.executable,scripts/'07_prepare_daat_handoff.py','--root',root,'--snapshot-id',latest['snapshot_id']]
    if a.kristal_root: cmd += ['--kristal-root',a.kristal_root]
    call(cmd)
    man=json.loads((run/'run-manifest.json').read_text(encoding='utf-8')); man.update({'completed_at':utc_now(),'snapshot_id':latest['snapshot_id'],'status':'complete'}); save_json(run/'run-manifest.json',man)
    save_json(root/'30_working/encyklopedia-harvest/latest.json',{'run_id':run_id,'path':relpath(run,root),'snapshot_id':latest['snapshot_id'],'updated_at':utc_now()})
    print(json.dumps({'complete':True,'run_id':run_id,'run_dir':str(run),'snapshot_id':latest['snapshot_id']},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
