from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
from scope_common import *


def fingerprint(root:Path,scope_arg:str)->str:
    cfgp,cfg=load_scope_config(root,scope_arg); src=cfg.get('root_source') or {}; reg=root/src.get('path',''); h=hashlib.sha256(); h.update(cfgp.read_bytes())
    if reg.exists():h.update(reg.read_bytes())
    try:
        d=find_dump(root); dd=dump_descriptor(root,d); h.update(json.dumps({'dump_id':dd['dump_id'],'bytes':dd['bytes']},sort_keys=True).encode())
    except Exception:pass
    return h.hexdigest()


def main():
    ap=argparse.ArgumentParser(description='Run scope pipeline only when inputs changed. Direct/raw mode does not wait for the global index.')
    ap.add_argument('--root',default=''); ap.add_argument('--scope',action='append',required=True); ap.add_argument('--through',default='handoff'); ap.add_argument('--discovery-backend',choices=['auto','index','fast','raw'],default='auto'); ap.add_argument('--prefer-index',action='store_true'); ap.add_argument('--poll-seconds',type=int,default=60); ap.add_argument('--kristal-root',default=''); ap.add_argument('--ik-root',default=''); ap.add_argument('--force',action='store_true'); ap.add_argument('--build-query-index',action='store_true'); ap.add_argument('--cache-vault',action='store_true'); ap.add_argument('--allow-full-scan',action='store_true'); ap.add_argument('--threads',type=int,default=0)
    a=ap.parse_args(); root=find_root(a.root or None); script=Path(__file__).resolve().parent/'run_scope_pipeline.py'; state_dir=root/'90_runtime/automation'; state_dir.mkdir(parents=True,exist_ok=True); fps={s:fingerprint(root,s) for s in a.scope}
    if not a.force:
        current=True
        for s in a.scope:
            _,cfg=load_scope_config(root,s); key=cfg['scope_key']; st=load_json(state_dir/f'{key}.json',{}) or {}; handoff=load_json(root/'20_ingest/daat-handoff'/key/'latest.json',{}) or {}
            if st.get('input_fingerprint')!=fps[s] or not handoff.get('handoff_id'):current=False;break
        if current:print('[auto] all selected scopes are current; nothing to do.');return
    cmd=[sys.executable,script,'--root',root,'--through',a.through,'--discovery-backend',('index' if a.prefer_index else a.discovery_backend)]
    if a.prefer_index:cmd += ['--wait-for-index','--poll-seconds',str(a.poll_seconds)]
    if a.build_query_index:cmd.append('--build-query-index')
    if a.cache_vault:cmd.append('--cache-vault')
    if a.allow_full_scan:cmd.append('--allow-full-scan')
    if a.threads:cmd += ['--threads',str(a.threads)]
    for s in a.scope:cmd += ['--scope',s]
    if a.kristal_root:cmd += ['--kristal-root',a.kristal_root]
    if a.ik_root:cmd += ['--ik-root',a.ik_root]
    rc=subprocess.call([str(x) for x in cmd])
    if rc:raise SystemExit(rc)
    for s in a.scope:
        _,cfg=load_scope_config(root,s); key=cfg['scope_key']; handoff=load_json(root/'20_ingest/daat-handoff'/key/'latest.json',{}) or {}; save_json(state_dir/f'{key}.json',{'scope_key':key,'input_fingerprint':fps[s],'handoff_id':handoff.get('handoff_id'),'updated_at':utc_now()})

if __name__=='__main__':main()
