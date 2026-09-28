from __future__ import annotations
import argparse, json
from scope_common import *


def main():
    ap=argparse.ArgumentParser(description='Freeze discovered QIDs + roles into an immutable scope definition before lossless extraction.')
    ap.add_argument('--root',default=''); ap.add_argument('--scope',required=True)
    a=ap.parse_args(); root=find_root(a.root or None); cfg_path,cfg=load_scope_config(root,a.scope); key=cfg['scope_key']; wd=scope_workdir(root,key)
    rows=read_jsonl(wd/'discovery/entities.jsonl'); edges=read_jsonl(wd/'discovery/edges.jsonl'); stats=load_json(wd/'discovery/stats.json',{}) or {}
    if not rows:raise SystemExit('Aucune découverte. Exécute 02_discover_scope.py.')
    rows=sorted(rows,key=lambda r:r['wid']); qids=sorted({r['wid'] for r in rows if isinstance(r.get('wid'),str)})
    roles={r['wid']:{'roles':sorted(r.get('roles') or []),'first_depth':int(r.get('first_depth') or 0)} for r in rows}
    payload={'schema_version':'encyklopedia-frozen-scope/v2','scope_key':key,'scope_config_sha256':sha256_file(cfg_path),'entity_count':len(qids),'entity_ids':qids,'entity_roles':roles,'discovery_backend':stats.get('discovery_backend'),'discovery_entities_sha256':sha256_file(wd/'discovery/entities.jsonl'),'discovery_edges_sha256':sha256_file(wd/'discovery/edges.jsonl'),'frozen_at':utc_now()}
    canonical=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'); payload['scope_hash']='sha256:'+sha256_bytes(canonical)
    save_json(wd/'scope.freeze.json',payload); (wd/'entity-ids.txt').write_text('\n'.join(qids)+'\n',encoding='utf-8')
    print(json.dumps({'scope_key':key,'entity_count':len(qids),'scope_hash':payload['scope_hash'],'out':str(wd/'scope.freeze.json')},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
