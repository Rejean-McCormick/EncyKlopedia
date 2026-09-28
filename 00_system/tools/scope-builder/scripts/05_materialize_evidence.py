from __future__ import annotations
import argparse, gzip, hashlib, json, os, shutil, zlib
from pathlib import Path
from scope_common import *


def main():
    ap=argparse.ArgumentParser(description='Materialize a frozen scope from the reusable entity vault into an immutable lossless evidence snapshot.')
    ap.add_argument('--root',default=''); ap.add_argument('--scope',required=True); ap.add_argument('--db',default=''); ap.add_argument('--dump',default='')
    a=ap.parse_args(); root=find_root(a.root or None); _,cfg=load_scope_config(root,a.scope); key=cfg['scope_key']; wd=scope_workdir(root,key)
    freeze=load_json(wd/'scope.freeze.json',{}) or {}; qids=list(freeze.get('entity_ids') or [])
    if not qids: raise SystemExit('Scope non gelé.')
    dump=Path(a.dump) if a.dump else find_dump(root); desc=dump_descriptor(root,dump); dump_id=desc['dump_id']
    vp=vault_path(root,dump_id); vc=ensure_vault(vp,dump_id)
    missing=[]; records=[]
    # Build deterministic manifest rows in QID order.
    for q in qids:
        r=vc.execute('SELECT raw_bytes,sha256 FROM entity_raw WHERE wid=?',(q,)).fetchone()
        if not r: missing.append(q)
        else: records.append({'wid':q,'raw_bytes':int(r['raw_bytes']),'sha256':r['sha256']})
    if missing: vc.close(); raise SystemExit(f'{len(missing)} entités absentes du vault. Exécute 04_fill_entity_vault.py. Exemples: {missing[:10]}')
    seed={'scope_key':key,'scope_hash':freeze.get('scope_hash'),'dump_id':dump_id,'entities':[(r['wid'],r['sha256']) for r in records]}
    snap_hash=sha256_bytes(json.dumps(seed,sort_keys=True,separators=(',',':')).encode('utf-8')); snapshot_id='wikidata-'+snap_hash[:20]
    final=scope_snapshot_dir(root,key,snapshot_id); latest=wd/'evidence.latest.json'
    if final.exists():
        save_json(latest,{'snapshot_id':snapshot_id,'path':str(final.relative_to(root)).replace('\\','/'),'updated_at':utc_now()}); vc.close(); print(json.dumps({'reused':True,'snapshot_id':snapshot_id,'path':str(final)},indent=2)); return
    staging=root/'20_ingest/staging'/f'{key}-{snapshot_id}.tmp'; shutil.rmtree(staging,ignore_errors=True); staging.mkdir(parents=True,exist_ok=True)
    evidence=staging/'entities.wikidata.jsonl.gz'; manifest_jsonl=staging/'entities.manifest.jsonl'
    with gzip.open(evidence,'wb',compresslevel=6) as gz, manifest_jsonl.open('w',encoding='utf-8') as mf:
        for i,rec in enumerate(records,1):
            rr=vc.execute('SELECT raw_zlib FROM entity_raw WHERE wid=?',(rec['wid'],)).fetchone(); raw=zlib.decompress(rr['raw_zlib'])
            gz.write(raw+b'\n'); mf.write(json.dumps(rec,sort_keys=True)+'\n')
            if i%1000==0: print(f'[evidence] {i:,}/{len(records):,}',flush=True)
    vc.close()
    snapshot_manifest={
      'schema_version':'encyklopedia-wikidata-scope-evidence/v1','snapshot_id':snapshot_id,'scope_key':key,'scope_hash':freeze.get('scope_hash'),'dump_id':dump_id,
      'dump_file':dump.name,'entity_count':len(records),'evidence_file':'entities.wikidata.jsonl.gz','evidence_sha256':sha256_file(evidence),
      'entity_manifest_file':'entities.manifest.jsonl','entity_manifest_sha256':sha256_file(manifest_jsonl),'created_at':utc_now(),
      'semantics':'Lossless at Wikidata entity JSON content level: complete selected entity objects including claims, literal values, qualifiers, references, ranks and sitelinks. JSON array separators from the source dump are not retained.'}
    save_json(staging/'snapshot-manifest.json',snapshot_manifest); final.parent.mkdir(parents=True,exist_ok=True); os.replace(staging,final)
    save_json(latest,{'snapshot_id':snapshot_id,'path':str(final.relative_to(root)).replace('\\','/'),'updated_at':utc_now()})
    print(json.dumps({'snapshot_id':snapshot_id,'entity_count':len(records),'path':str(final),'evidence':str(final/'entities.wikidata.jsonl.gz')},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
