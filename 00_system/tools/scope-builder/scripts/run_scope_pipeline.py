from __future__ import annotations
import argparse, json, subprocess, sys, time
from pathlib import Path
from scope_common import *

STAGES=['resolve','discover','freeze','evidence','index','referents','mediatheque','handoff']


def call(cmd:list[str]):
    print('\n$ '+' '.join(map(str,cmd)),flush=True); rc=subprocess.call([str(x) for x in cmd])
    if rc:raise SystemExit(rc)


def wait_index(root:Path,poll:int):
    while True:
        ok,m=global_index_status(root)
        if ok:print('[auto] global discovery index complete.',flush=True);return
        print(f"[auto] waiting for optional global index | processed={m.get('processed_entities','?')} | complete={m.get('complete',False)}",flush=True); time.sleep(poll)


def main():
    ap=argparse.ArgumentParser(description="Orchestrate scope-rooted discovery → direct lossless Wikidata evidence → referent/media candidates → Da'at handoff. Global/project SQLite indexes are optional accelerators.")
    ap.add_argument('--root',default=''); ap.add_argument('--scope',action='append',required=True,help='Repeat to union scopes in one evidence dump scan.')
    ap.add_argument('--through',choices=STAGES,default='handoff'); ap.add_argument('--from-stage',choices=STAGES,default='resolve')
    ap.add_argument('--discovery-backend',choices=['auto','index','fast','raw'],default='auto',help='auto: use complete global index if available, otherwise scan raw dump directly.')
    ap.add_argument('--wait-for-index',action='store_true',help='Only useful when you specifically want the index backend.'); ap.add_argument('--poll-seconds',type=int,default=60)
    ap.add_argument('--build-query-index',action='store_true',help='Optional derived per-project SQLite. Not required for Da\'at/Kristal.')
    ap.add_argument('--cache-vault',action='store_true',help='Optionally cache selected raw entities in the reusable entity-vault SQLite while extracting evidence.')
    ap.add_argument('--min-free-gib',type=float,default=20.0); ap.add_argument('--threads',type=int,default=0); ap.add_argument('--prepare-fast-access',action='store_true'); ap.add_argument('--allow-full-scan',action='store_true',help='Explicit opt-in to a sequential raw dump evidence scan when random access/cache is unavailable.'); ap.add_argument('--kristal-root',default=''); ap.add_argument('--ik-root',default='')
    a=ap.parse_args(); root=find_root(a.root or None); scripts=Path(__file__).resolve().parent
    if a.prepare_fast_access:
        perf=root/'00_system/tools/performance/scripts/build_fast_access.py'; call([sys.executable,perf,'--root',root,*(['--threads',str(a.threads)] if a.threads else [])])
    if a.wait_for_index:
        wait_index(root,a.poll_seconds); a.discovery_backend='index'
    scope_cfgs=[]
    for s in a.scope:
        _,cfg=load_scope_config(root,s); scope_cfgs.append((s,cfg['scope_key']))
    start=STAGES.index(a.from_stage); end=STAGES.index(a.through)
    if start>end:raise SystemExit('--from-stage doit précéder --through')
    def active(stage):return start<=STAGES.index(stage)<=end
    # Scope definition stages are independent; no complete global index is required in auto/raw modes.
    for s,key in scope_cfgs:
        if active('resolve'):call([sys.executable,scripts/'01_resolve_roots.py','--root',root,'--scope',s,'--backend',a.discovery_backend])
        if active('discover'):call([sys.executable,scripts/'02_discover_scope.py','--root',root,'--scope',s,'--backend',a.discovery_backend])
        if active('freeze'):call([sys.executable,scripts/'03_freeze_scope.py','--root',root,'--scope',s])
    # Direct evidence extraction scans the raw dump once for the union of requested frozen scopes.
    if active('evidence'):
        if free_gib(root)<a.min_free_gib:raise SystemExit(f'Espace libre sous le seuil {a.min_free_gib:.1f} GiB; arrêt avant extraction evidence.')
        cmd=[sys.executable,scripts/'04_extract_evidence.py','--root',root]
        for s,_ in scope_cfgs:cmd += ['--scope',s]
        if a.cache_vault:cmd.append('--cache-vault')
        if a.allow_full_scan:cmd.append('--allow-full-scan')
        if a.threads:cmd += ['--threads',str(a.threads)]
        call(cmd)
    for s,key in scope_cfgs:
        if active('index') and a.build_query_index:call([sys.executable,scripts/'06_build_scope_index.py','--root',root,'--scope',s])
        if active('referents'):call([sys.executable,scripts/'07_publish_referents.py','--root',root,'--scope',s])
        if active('mediatheque'):call([sys.executable,scripts/'07_publish_mediatheque.py','--root',root,'--scope',s])
        if active('handoff'):
            cmd=[sys.executable,scripts/'08_prepare_daat_handoff.py','--root',root,'--scope',s]
            if a.kristal_root:cmd += ['--kristal-root',a.kristal_root]
            if a.ik_root:cmd += ['--ik-root',a.ik_root]
            call(cmd)
    report={'complete':True,'scopes':[k for _,k in scope_cfgs],'from_stage':a.from_stage,'through':a.through,'discovery_backend_requested':a.discovery_backend,'direct_evidence':True,'project_query_index_built':bool(a.build_query_index and active('index')),'vault_cache_enabled':a.cache_vault,'threads':a.threads or performance_status(root).get('recommended_threads'),'fast_access_prepared':a.prepare_fast_access,'allow_full_scan':a.allow_full_scan,'finished_at':utc_now()}; print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
