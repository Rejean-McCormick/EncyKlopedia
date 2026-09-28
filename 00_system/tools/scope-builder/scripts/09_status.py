from __future__ import annotations
import argparse, json
from scope_common import *


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default=''); a=ap.parse_args(); root=find_root(a.root or None); db=default_global_db(root); ok,idx=global_index_status(root,db)
    try:dump=dump_descriptor(root,find_dump(root))
    except Exception as e:dump={'error':str(e)}
    
    try:
        dp=find_dump(root); fok,fidx=fast_access_status(root,dp)
    except Exception as e:fok=False;fidx={'complete':False,'error':str(e)}
    default_backend='index' if ok else ('fast' if fok and fidx.get('random_access_ready') else 'raw')
    rep={'schema_version':'encyklopedia-status/v4','root':str(root),'disk_free_gib':round(free_gib(root),2),'raw_dump':dump,'performance':performance_status(root),'global_index':idx,'global_index_role':'optional discovery accelerator','fast_access':fidx,'fast_access_role':'optional QID random-access + selected reverse-edge accelerator','default_discovery_backend':default_backend,'project_index_required':False,'scopes':[],'generated_at':utc_now()}

    cfgdir=root/'00_system/tools/scope-builder/config/scopes'
    for p in sorted(cfgdir.glob('*.scope.json')):
        cfg=load_json(p,{}); key=cfg.get('scope_key'); wd=scope_workdir(root,key); row={'scope_key':key,'title':cfg.get('title'),'config':str(p.relative_to(root)).replace('\\','/')}
        row['root_semantics']=scope_root_semantics(cfg); row['roots_resolved']=(wd/'roots.resolved.json').exists(); row['discovered']=(wd/'discovery/entities.jsonl').exists(); row['discovery_stats']=load_json(wd/'discovery/stats.json',None); row['frozen']=(wd/'scope.freeze.json').exists(); row['evidence']=load_json(wd/'evidence.latest.json',None); row['optional_project_index']=(wd/'index'/f'{key}.sqlite').exists(); row['referent_registry']=load_json(root/'20_ingest/referent-registries'/key/'latest.json',None); row['mediatheque_candidates']=load_json(root/'50_mediatheque/catalog/candidates/wikidata'/key/'latest.json',None); row['daat_handoff']=load_json(root/'20_ingest/daat-handoff'/key/'latest.json',None); rep['scopes'].append(row)
    print(json.dumps(rep,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
