from __future__ import annotations
import argparse, json
from pathlib import Path
from scope_common import *


def main():
    ap=argparse.ArgumentParser(description='Estimate direct scope evidence extraction cost. No global/project DB is required.')
    ap.add_argument('--root',default=''); ap.add_argument('--scope',required=True); ap.add_argument('--dump',default='')
    a=ap.parse_args(); root=find_root(a.root or None); _,cfg=load_scope_config(root,a.scope); key=cfg['scope_key']; wd=scope_workdir(root,key); freeze=load_json(wd/'scope.freeze.json',{}) or {}; qids=set(freeze.get('entity_ids') or [])
    if not qids:qids={r['wid'] for r in read_jsonl(wd/'discovery/entities.jsonl')}
    dump=Path(a.dump) if a.dump else find_dump(root); desc=dump_descriptor(root,dump); latest=load_json(wd/'evidence.latest.json',{}) or {}; reusable=False
    if latest.get('snapshot_id'):
        man=load_json(scope_snapshot_dir(root,key,latest['snapshot_id'])/'snapshot-manifest.json',{}) or {}; reusable=man.get('scope_hash')==freeze.get('scope_hash') and man.get('dump_id')==desc['dump_id']
    vp=vault_path(root,desc['dump_id']); existing=0; raw_bytes=0; zbytes=0
    if vp.exists() and qids:
        vc=open_db(vp,True)
        for batch in chunks(sorted(qids),700):
            qs=','.join('?'*len(batch))
            for r in vc.execute(f'SELECT raw_bytes,length(raw_zlib) AS zbytes FROM entity_raw WHERE wid IN ({qs})',batch):existing+=1; raw_bytes+=int(r['raw_bytes']); zbytes+=int(r['zbytes'])
        vc.close()
    rep={'scope_key':key,'entity_count':len(qids),'dump':desc,'evidence_already_reusable':reusable,'direct_mode_requires_full_sequential_dump_pass':bool(qids and not reusable),'optional_vault_cache':{'path':str(vp),'exists':vp.exists(),'selected_entities_cached':existing,'average_raw_bytes':round(raw_bytes/existing,1) if existing else None,'average_zlib_bytes':round(zbytes/existing,1) if existing else None},'global_index_required':False,'project_index_required':False,'note':'In direct mode the cost is one sequential dump scan for the union of frozen scopes. Selected entities are written complete; field count does not affect evidence fidelity.'}
    print(json.dumps(rep,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
