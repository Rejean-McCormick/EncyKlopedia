from __future__ import annotations
import argparse, json, time, zlib
from pathlib import Path
from scope_common import *


def main():
    ap=argparse.ArgumentParser(description='Scan the raw Wikidata dump once and preserve full JSON for missing QIDs in a reusable selected-entity vault.')
    ap.add_argument('--root',default=''); ap.add_argument('--scope',action='append',required=True,help='Repeat to union several scopes in one dump scan.'); ap.add_argument('--dump',default=''); ap.add_argument('--db',default=''); ap.add_argument('--compression',type=int,default=6)
    a=ap.parse_args(); root=find_root(a.root or None); dump=Path(a.dump) if a.dump else find_dump(root); desc=dump_descriptor(root,dump); dump_id=desc['dump_id']
    wanted=set(); scopes=[]
    for s in a.scope:
        _,cfg=load_scope_config(root,s); key=cfg['scope_key']; freeze=load_json(scope_workdir(root,key)/'scope.freeze.json',{}) or {}
        ids=set(freeze.get('entity_ids') or [])
        if not ids: raise RuntimeError(f'Scope {key} non gelé. Exécute 03_freeze_scope.py.')
        wanted |= ids; scopes.append(key)
    vp=vault_path(root,dump_id); vc=ensure_vault(vp,dump_id)
    have=set()
    for batch in chunks(sorted(wanted),700):
        qs=','.join('?'*len(batch))
        have.update(r[0] for r in vc.execute(f'SELECT wid FROM entity_raw WHERE wid IN ({qs})', batch))
    missing=wanted-have
    print(json.dumps({'dump':str(dump),'dump_id':dump_id,'vault':str(vp),'scopes':scopes,'wanted':len(wanted),'already_in_vault':len(have),'missing':len(missing)},ensure_ascii=False,indent=2),flush=True)
    if not missing:
        save_json(vp.with_suffix('.last-run.json'),{'completed_at':utc_now(),'scopes':scopes,'wanted':len(wanted),'missing_before':0,'found':0,'vault':str(vp)}); vc.close(); return
    found=0; scanned=0; started=time.time(); last=time.time()
    for raw in iter_dump_raw(dump):
        scanned+=1; wid=raw_entity_id(raw)
        if wid in missing:
            sha=sha256_bytes(raw); blob=zlib.compress(raw,a.compression)
            vc.execute('INSERT OR REPLACE INTO entity_raw(wid,raw_zlib,raw_bytes,sha256,captured_at) VALUES(?,?,?,?,?)',(wid,blob,len(raw),sha,utc_now())); found+=1; missing.remove(wid)
            if found % 100 == 0: vc.commit()
            print(f'[vault] found {found:,} | remaining {len(missing):,} | scanned {scanned:,} | {wid}',flush=True)
            if not missing: break
        if time.time()-last>60:
            print(f'[vault] scanned {scanned:,} | found {found:,} | remaining {len(missing):,} | elapsed {(time.time()-started)/3600:.2f}h',flush=True); last=time.time()
    vc.commit(); report={'completed_at':utc_now(),'scopes':scopes,'wanted':len(wanted),'missing_before':len(wanted-have),'found':found,'still_missing':sorted(missing),'scanned_entities':scanned,'elapsed_seconds':round(time.time()-started,1),'vault':str(vp),'dump':str(dump),'dump_id':dump_id}
    save_json(vp.with_suffix('.last-run.json'),report); vc.close()
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if missing: raise SystemExit(f'{len(missing)} QID(s) non trouvés dans le dump; voir report.')

if __name__=='__main__': main()
