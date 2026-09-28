from __future__ import annotations
import argparse, json, re
from pathlib import Path
from scope_common import *


def entry(root:Path,p:Path,role:str):
    return {'role':role,'path':str(p.relative_to(root)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':'sha256:'+sha256_file(p)}


def semver_key(value:str)->tuple[int,...]:
    nums=re.findall(r'\d+',value or '')
    return tuple(int(x) for x in nums[:3]) if nums else (0,)


def detect_ik_build_profile(ik:Path)->dict[str,Any]:
    base={'configured':False,'status':'missing','profile_candidate':None,'message_emitted':False}
    if not ik.exists():return base
    version=(ik/'VERSION').read_text(encoding='utf-8-sig').strip() if (ik/'VERSION').exists() else None
    idx=load_json(ik/'contracts/profiles/index.json',{}) or {}
    candidates=[p for p in idx.get('profiles',[]) if p.get('id')=='kristal.build.request']
    candidates=sorted(candidates,key=lambda p:semver_key(str(p.get('version') or '')),reverse=True)
    chosen=candidates[0] if candidates else None
    if not chosen:
        return {**base,'configured':True,'version':version,'status':'contracts_present_no_kristal_build_profile'}
    pv=str(chosen['version']); rel=Path('contracts/profiles/kristal/kristal.build.request')/pv
    profile=ik/rel/'profile.json'; schema=ik/rel/'payload.schema.json'
    pobj=load_json(profile,{}) or {}; admitted='encyklopedia' in (pobj.get('source_systems') or [])
    runtime=ik/'runtime/python/src/interaction_kernel'; adapter=ik/'adapters/daat/build_mapping.py'
    complete=all(x.exists() for x in [profile,schema,runtime,adapter])
    return {
        'configured':True,
        'version':version,
        'status':'contracts_present' if complete else 'incomplete_snapshot',
        'profile_candidate':f'kristal.build.request/{pv}',
        'profile_exists':profile.exists(),
        'payload_schema_exists':schema.exists(),
        'python_runtime_exists':runtime.exists(),
        'daat_adapter_exists':adapter.exists(),
        'encyklopedia_source_admitted':admitted,
        'message_emitted':False,
        'note':'IK readiness only. EncyKlopedia prepares immutable source-owned handoffs; Da’at remains the mapping boundary and IK transport is used only when an explicitly adopted profile admits this source.',
    }


def main():
    ap=argparse.ArgumentParser(description="Prepare a frozen EncyKlopedia corpus-harvest handoff for Da'at from scope + lossless evidence.")
    ap.add_argument('--root',default=''); ap.add_argument('--scope',required=True); ap.add_argument('--kristal-root',default=''); ap.add_argument('--ik-root',default='')
    a=ap.parse_args(); root=find_root(a.root or None); cfgp,cfg=load_scope_config(root,a.scope); key=cfg['scope_key']; wd=scope_workdir(root,key)

    baseline=load_json(root/'00_system/contracts/knowledge-baseline.json',{}) or {}
    if baseline.get('encyklopedia_handoff')!='encyklopedia.corpus-harvest-handoff/1.0.0':
        raise SystemExit('Knowledge contract baseline absent or incompatible.')

    latest=load_json(wd/'evidence.latest.json',{}) or {}; sid=latest.get('snapshot_id')
    if not sid:raise SystemExit('Evidence snapshot absent.')
    snap=scope_snapshot_dir(root,key,sid); freeze=wd/'scope.freeze.json'; evman=snap/'snapshot-manifest.json'; evidence=snap/'entities.wikidata.jsonl.gz'; eman=snap/'entities.manifest.jsonl'
    for p in [freeze,evman,evidence,eman]:
        if not p.exists():raise FileNotFoundError(p)

    files=[
        entry(root,freeze,'frozen_scope'),
        entry(root,evman,'evidence_manifest'),
        entry(root,evidence,'lossless_wikidata_evidence'),
        entry(root,eman,'entity_content_manifest'),
    ]

    idx=wd/'index'/f'{key}.sqlite'; idxm=wd/'index/index-manifest.json'
    if idx.exists() and idxm.exists():
        files += [entry(root,idx,'optional_project_query_index'),entry(root,idxm,'optional_project_index_manifest')]

    refer_latest=load_json(root/'20_ingest/referent-registries'/key/'latest.json',{}) or {}
    if refer_latest.get('path'):
        rp=root/refer_latest['path']
        if rp.exists():files.append(entry(root,rp,'referent_registry_candidate'))

    medi_latest=load_json(root/'50_mediatheque/catalog/candidates/wikidata'/key/'latest.json',{}) or {}
    if medi_latest.get('file'):
        mp=root/medi_latest['file']
        if mp.exists():files.append(entry(root,mp,'mediatheque_candidates'))

    kristal_check={'configured':False,'status':'not_probed'}
    if a.kristal_root:
        kr=Path(a.kristal_root)
        schema_candidates=list(kr.glob('**/referent-registry.schema.json')) if kr.exists() else []
        release_files=list(kr.glob('**/kristal-release.json')) if kr.exists() else []
        release=None
        for rf in release_files[:5]:
            robj=load_json(rf,{}) or {}
            release=robj.get('version') or robj.get('release') or release
            if release:break
        kristal_check={
            'configured':True,
            'root':str(kr),
            'exists':kr.exists(),
            'detected_release':release,
            'expected_release':baseline.get('kristal_release'),
            'referent_schema_found':bool(schema_candidates),
            'status':'present_requires_contract_validation' if kr.exists() else 'missing',
            'note':'Presence is not epistemic acceptance. Da’at/Kristal still validates and owns the resulting artifacts.',
        }

    bundled_ik=root/'00_system/integrations/Interaction-Kernel'
    ik=Path(a.ik_root) if a.ik_root else bundled_ik
    ik_check=detect_ik_build_profile(ik)
    ik_check['source']='explicit' if a.ik_root else 'bundled_snapshot'

    payload={
        'schema_version':'encyklopedia-daat-handoff/v4',
        'contract':baseline['encyklopedia_handoff'],
        'kristal_contract_set':baseline['kristal_release'],
        'referent_profile':baseline['kristal_referent_profile'],
        'kristal_contract_bundle_sha256':baseline.get('kristal_contract_bundle_sha256'),
        'scope_key':key,
        'snapshot_id':sid,
        'created_at':utc_now(),
        'source_semantics':'The handoff is rooted in complete selected source evidence. Derived SQLite indexes are optional accelerators and never epistemic authority.',
        'mapping_boundary':"Da'at",
        'target':'Kristal Structured Epistemic State through the installed pinned contract',
        'files':files,
        'scope_config':entry(root,cfgp,'scope_config'),
        'kristal_environment':kristal_check,
        'interaction_kernel':ik_check,
        'invariants':[
            'Scope root roles are domain policy; EncyKlopedia is not universally people-first.',
            'Referent registry entries are source-qualified identity/discovery candidates, not validated claims.',
            'External identifiers do not become canonical Kristal identity or epistemic authority by ingestion.',
            'Do not collapse work, edition and manifestation/file during documentary acquisition.',
            'Do not treat Wikidata claims as automatically validated Kristal assertions.',
            'Preserve statement IDs, ranks, literal values, qualifiers and references during Da’at mapping.',
            'Source evidence remains source-owned and immutable.',
            'Do not require or treat a project SQLite as epistemic source.',
            'Do not write directly into 40_kristal without the real Kristal/Da’at lifecycle.',
        ],
    }
    # Keep absent optional pin absent rather than serializing null into the frozen handoff.
    if not payload.get('kristal_contract_bundle_sha256'):payload.pop('kristal_contract_bundle_sha256',None)

    handoff_hash=sha256_bytes(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))
    hid='handoff-'+handoff_hash[:20]; payload['handoff_id']=hid

    outdir=root/'20_ingest/daat-handoff'/key; outdir.mkdir(parents=True,exist_ok=True)
    out=outdir/f'{hid}.json'; save_json(out,payload)
    save_json(outdir/'latest.json',{'handoff_id':hid,'path':str(out.relative_to(root)).replace('\\','/'),'snapshot_id':sid,'contract':payload['contract'],'updated_at':utc_now()})
    print(json.dumps({'handoff_id':hid,'contract':payload['contract'],'scope_key':key,'snapshot_id':sid,'path':str(out),'project_index_required':False,'interaction_kernel_message_emitted':False},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
