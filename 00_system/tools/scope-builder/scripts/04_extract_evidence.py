from __future__ import annotations
import argparse, gzip, json, os, shutil, time, zlib
from pathlib import Path
from scope_common import *


def gzip_writer(path:Path,level:int):
    raw=path.open('wb'); gz=gzip.GzipFile(filename='',mode='wb',compresslevel=level,fileobj=raw,mtime=0); return raw,gz


def reusable_snapshot(root:Path,key:str,scope_hash:str,dump_id:str)->dict[str,Any]|None:
    wd=scope_workdir(root,key); latest=load_json(wd/'evidence.latest.json',{}) or {}; sid=latest.get('snapshot_id')
    if not sid:return None
    snap=scope_snapshot_dir(root,key,sid); man=load_json(snap/'snapshot-manifest.json',{}) or {}
    if man.get('scope_hash')==scope_hash and man.get('dump_id')==dump_id and (snap/'entities.wikidata.jsonl.gz').exists():
        return {'snapshot_id':sid,'path':str(snap),'reused':True}
    return None


def main():
    ap=argparse.ArgumentParser(description='Extract complete selected Wikidata entities into immutable scope evidence. 0.12 refuses accidental 121M-entity scans unless --allow-full-scan is explicit.')
    ap.add_argument('--root',default=''); ap.add_argument('--scope',action='append',required=True); ap.add_argument('--dump',default=''); ap.add_argument('--compression',type=int,default=6)
    ap.add_argument('--cache-vault',action='store_true'); ap.add_argument('--threads',type=int,default=0); ap.add_argument('--no-fast-access',action='store_true')
    ap.add_argument('--allow-full-scan',action='store_true',help='Explicitly allow a sequential scan of the entire raw dump when random access/cache cannot satisfy the scope.')
    ap.add_argument('--max-auto-scan-gib',type=float,default=2.0,help='Small dumps at or below this compressed size may scan automatically; large production dumps require explicit opt-in.')
    a=ap.parse_args(); root=find_root(a.root or None); dump=Path(a.dump) if a.dump else find_dump(root); desc=dump_descriptor(root,dump); dump_id=desc['dump_id']
    states=[]; reusable=[]
    for s in a.scope:
        _,cfg=load_scope_config(root,s); key=cfg['scope_key']; wd=scope_workdir(root,key); freeze=load_json(wd/'scope.freeze.json',{}) or {}; ids=set(freeze.get('entity_ids') or [])
        if not ids:raise RuntimeError(f'Scope {key} non gelé. Exécute 03_freeze_scope.py.')
        reuse=reusable_snapshot(root,key,freeze.get('scope_hash'),dump_id)
        if reuse:reusable.append({'scope_key':key,**reuse}); continue
        staging=root/'20_evidence/staging'/f'{key}-direct-evidence.tmp'
        states.append({'scope_arg':s,'scope_key':key,'wd':wd,'freeze':freeze,'wanted':ids,'missing':set(ids),'records':{},'staging':staging,'rawfh':None,'gz':None,'written':0})
    if not states:
        print(json.dumps({'dump':desc,'reused':reusable,'scanned':False},ensure_ascii=False,indent=2)); return
    union=set().union(*(st['wanted'] for st in states)); vp=vault_path(root,dump_id)
    cached=vault_fetch_raw(vp,dump_id,union)
    fast_ok,fastmeta=fast_access_status(root,dump)
    random_ready=bool(fast_ok and fastmeta.get('random_access_ready') and not a.no_fast_access)
    precovered=set(cached); small_dump=(dump.stat().st_size <= a.max_auto_scan_gib*1024**3)
    missing_before_scan=union-precovered
    if missing_before_scan and not random_ready and not a.allow_full_scan and not small_dump:
        raise SystemExit(
            f'Extraction evidence arrêtée avant scan: {len(missing_before_scan):,}/{len(union):,} QID ne sont ni dans le vault ni accessibles en random access. '
            f'Backend={performance_status(root)}. EncyK 0.12 ne relit plus silencieusement les 121M entités. '
            'Prépare un backend random-access (indexed_bzip2 pour ce .bz2, ou futur .json.gz + rapidgzip), '
            'ou relance explicitement avec --allow-full-scan si tu acceptes le coût.'
        )
    # Only create staging outputs after we know extraction can proceed.
    for st in states:
        shutil.rmtree(st['staging'],ignore_errors=True); st['staging'].mkdir(parents=True,exist_ok=True)
        st['rawfh'],st['gz']=gzip_writer(st['staging']/'entities.wikidata.jsonl.gz',a.compression)
    vault=ensure_vault(vp,dump_id) if a.cache_vault else None
    scanned=0; found_union=set(); started=time.time(); last=started
    if random_ready and not cached: mode='fast_random_access'
    elif random_ready: mode='cache+random'
    elif small_dump and not a.allow_full_scan: mode='small_dump_scan'
    else: mode='explicit_full_scan'
    extraction_backend={'mode':mode,'fast_access':fastmeta if fast_ok else None,'vault_hits':len(cached),'allow_full_scan':a.allow_full_scan,'small_dump_auto_scan':small_dump}
    def accept_raw(wid,raw):
        nonlocal found_union
        if wid in found_union:return
        sha=sha256_bytes(raw); found_union.add(wid)
        if vault is not None:
            vault.execute('INSERT OR REPLACE INTO entity_raw(wid,raw_zlib,raw_bytes,sha256,captured_at) VALUES(?,?,?,?,?)',(wid,zlib.compress(raw,a.compression),len(raw),sha,utc_now()))
        for st in states:
            if wid in st['missing']:
                st['gz'].write(raw+b'\n'); st['records'][wid]={'wid':wid,'raw_bytes':len(raw),'sha256':sha}; st['missing'].remove(wid); st['written']+=1
    print(json.dumps({'mode':'direct_lossless_extract_v012','dump':desc,'scopes':[s['scope_key'] for s in states],'union_qids':len(union),'vault_hits':len(cached),'random_access_ready':random_ready,'allow_full_scan':a.allow_full_scan,'cache_vault':bool(vault),'performance':performance_status(root)},ensure_ascii=False,indent=2),flush=True)
    try:
        for wid,raw in cached.items():accept_raw(wid,raw)
        if cached:print(f'[evidence/vault] found_union={len(found_union):,}/{len(union):,}',flush=True)
        missing_now=union-found_union
        if missing_now and random_ready:
            ordered=sorted(missing_now,key=lambda x:(x[0],int(x[1:]) if x[1:].isdigit() else 0))
            for batch in chunks(ordered,2000):
                rawmap=fast_fetch_raw(root,dump,batch,threads=a.threads)
                for wid,raw in rawmap.items():accept_raw(wid,raw)
                print(f'[evidence/fast] found_union={len(found_union):,}/{len(union):,}',flush=True)
                if vault is not None:vault.commit()
        missing_now=union-found_union
        if missing_now:
            if not a.allow_full_scan and not small_dump:
                raise SystemExit(f'Random access n\'a pas retourné {len(missing_now):,} QID. Aucun fallback full-scan automatique en 0.12. Exemples: {sorted(missing_now)[:20]}')
            extraction_backend['fallback_scan']=True
            print(f'[evidence/scan] FULL SCAN EXPLICITE pour {len(missing_now):,} QID manquants.',flush=True)
            for raw in iter_dump_raw(dump,root=root,threads=a.threads):
                scanned+=1; wid=raw_entity_id(raw)
                if wid not in missing_now:continue
                accept_raw(wid,raw); missing_now.discard(wid)
                if len(found_union)%100==0:
                    if vault is not None:vault.commit()
                    print(f'[evidence/scan] found_union={len(found_union):,}/{len(union):,} scanned={scanned:,}',flush=True)
                if not missing_now:break
                now=time.time()
                if now-last>60:
                    print(f'[evidence/scan] scanned={scanned:,} found_union={len(found_union):,}/{len(union):,} elapsed={(now-started)/3600:.2f}h',flush=True); last=now
    finally:
        for st in states:
            if st['gz'] is not None:
                try:st['gz'].close()
                finally:st['rawfh'].close()
        if vault is not None:vault.commit(); vault.close()
    missing_union=union-found_union
    if missing_union:
        for st in states:shutil.rmtree(st['staging'],ignore_errors=True)
        raise SystemExit(f'{len(missing_union)} QID(s) sélectionnés non trouvés dans le dump. Exemples: {sorted(missing_union)[:20]}')
    results=[]
    for st in states:
        key=st['scope_key']; freeze=st['freeze']; records=[st['records'][q] for q in sorted(st['records'])]
        manifest_jsonl=st['staging']/'entities.manifest.jsonl'; write_jsonl(manifest_jsonl,records)
        seed={'scope_key':key,'scope_hash':freeze.get('scope_hash'),'dump_id':dump_id,'entities':[(r['wid'],r['sha256']) for r in records]}; snapshot_id='wikidata-'+sha256_bytes(json.dumps(seed,sort_keys=True,separators=(',',':')).encode())[:20]
        final=scope_snapshot_dir(root,key,snapshot_id); evidence=st['staging']/'entities.wikidata.jsonl.gz'
        manifest={'schema_version':'encyklopedia-wikidata-scope-evidence/v3','snapshot_id':snapshot_id,'scope_key':key,'scope_hash':freeze.get('scope_hash'),'dump_id':dump_id,'dump':desc,'entity_count':len(records),'evidence_file':'entities.wikidata.jsonl.gz','evidence_sha256':sha256_file(evidence),'entity_manifest_file':'entities.manifest.jsonl','entity_manifest_sha256':sha256_file(manifest_jsonl),'created_at':utc_now(),'extraction_mode':extraction_backend.get('mode'),'performance_backend':extraction_backend,'project_database_required':False,'semantics':'Complete selected Wikidata entity JSON objects are retained, including all claims, literal values, qualifiers, references, ranks, aliases, descriptions, external identifiers and sitelinks present in the source entity. Only top-level dump array punctuation is omitted.'}
        save_json(st['staging']/'snapshot-manifest.json',manifest); final.parent.mkdir(parents=True,exist_ok=True)
        if final.exists():shutil.rmtree(st['staging'],ignore_errors=True)
        else:os.replace(st['staging'],final)
        save_json(st['wd']/'evidence.latest.json',{'snapshot_id':snapshot_id,'path':str(final.relative_to(root)).replace('\\','/'),'updated_at':utc_now(),'extraction_mode':extraction_backend.get('mode')})
        results.append({'scope_key':key,'snapshot_id':snapshot_id,'entity_count':len(records),'path':str(final)})
    report={'dump':desc,'performance_backend':extraction_backend,'scanned_entities':scanned,'elapsed_seconds':round(time.time()-started,2),'results':results,'reused':reusable,'optional_vault':str(vp) if vp.exists() else None}; print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
