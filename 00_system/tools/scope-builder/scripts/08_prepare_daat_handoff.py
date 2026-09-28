from __future__ import annotations
import argparse, json
from pathlib import Path
from scope_common import *


def entry(root:Path,p:Path,role:str):
    return {'role':role,'path':str(p.relative_to(root)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':'sha256:'+sha256_file(p)}


def main():
    ap=argparse.ArgumentParser(description="Prepare a content-addressed Da'at handoff directly from frozen scope + lossless Wikidata evidence. A project DB is optional.")
    ap.add_argument('--root',default=''); ap.add_argument('--scope',required=True); ap.add_argument('--kristal-root',default=''); ap.add_argument('--ik-root',default='')
    a=ap.parse_args(); root=find_root(a.root or None); cfgp,cfg=load_scope_config(root,a.scope); key=cfg['scope_key']; wd=scope_workdir(root,key)
    latest=load_json(wd/'evidence.latest.json',{}) or {}; sid=latest.get('snapshot_id')
    if not sid:raise SystemExit('Evidence snapshot absent.')
    snap=scope_snapshot_dir(root,key,sid); freeze=wd/'scope.freeze.json'; evman=snap/'snapshot-manifest.json'; evidence=snap/'entities.wikidata.jsonl.gz'; eman=snap/'entities.manifest.jsonl'
    for p in [freeze,evman,evidence,eman]:
        if not p.exists():raise FileNotFoundError(p)
    files=[entry(root,freeze,'frozen_scope'),entry(root,evman,'evidence_manifest'),entry(root,evidence,'lossless_wikidata_evidence'),entry(root,eman,'entity_content_manifest')]
    # Optional derived conveniences. Neither is required for Da'at mapping.
    idx=wd/'index'/f'{key}.sqlite'; idxm=wd/'index/index-manifest.json'
    if idx.exists() and idxm.exists():files += [entry(root,idx,'optional_project_query_index'),entry(root,idxm,'optional_project_index_manifest')]
    medi_latest=load_json(root/'50_mediatheque/catalog/candidates/wikidata'/key/'latest.json',{}) or {}
    if medi_latest.get('file'):
        mp=root/medi_latest['file']
        if mp.exists():files.append(entry(root,mp,'mediatheque_candidates'))
    kristal_check={'configured':False,'status':'not_probed'}
    if a.kristal_root:
        kr=Path(a.kristal_root); kristal_check={'configured':True,'root':str(kr),'exists':kr.exists(),'status':'present_requires_installed_contract_validation' if kr.exists() else 'missing','note':"This tool does not invent or bypass Kristal schemas, validation, recognition, reader-policy or activation mechanics."}
    bundled_ik=root/'00_system/integrations/Interaction-Kernel'
    ik=Path(a.ik_root) if a.ik_root else bundled_ik
    ik_check={'configured':False,'status':'missing','profile_candidate':'kristal.build.request/1.0.0','message_emitted':False}
    if ik.exists():
        version=(ik/'VERSION').read_text(encoding='utf-8-sig').strip() if (ik/'VERSION').exists() else None
        profile=ik/'contracts/profiles/kristal/kristal.build.request/1.0.0/profile.json'; schema=ik/'contracts/profiles/kristal/kristal.build.request/1.0.0/payload.schema.json'; runtime=ik/'runtime/python/src/interaction_kernel'; adapter=ik/'adapters/daat/build_mapping.py'
        ik_check.update({'configured':True,'root':str(ik),'source':'explicit' if a.ik_root else 'bundled_snapshot','version':version,'profile_exists':profile.exists(),'payload_schema_exists':schema.exists(),'python_runtime_exists':runtime.exists(),'daat_adapter_exists':adapter.exists(),'status':'contracts_present' if all(x.exists() for x in [profile,schema,runtime,adapter]) else 'incomplete_snapshot','note':"The bundled IK snapshot is used for contract validation/reference only. EncyKlopedia does not emit kristal.build.request directly because that profile declares Konnaxion/Orgo source systems; Da'at remains the mapping boundary."})
    payload={'schema_version':'encyklopedia-daat-handoff/v3','scope_key':key,'snapshot_id':sid,'created_at':utc_now(),'source_semantics':'The handoff is rooted directly in complete selected Wikidata entity JSON. Any SQLite indexes are optional derived accelerators and non-authoritative.','mapping_boundary':"Da'at",'target':'Kristal Structured Epistemic State through the installed Kristal v5 contract','files':files,'scope_config':entry(root,cfgp,'scope_config'),'kristal_environment':kristal_check,'interaction_kernel':ik_check,'invariants':['Do not treat Wikidata claims as automatically validated Kristal assertions.','Preserve statement IDs, ranks, literal values, qualifiers and references during Da\'at mapping.','Source evidence remains source-owned and immutable.','Do not require or treat a project SQLite as epistemic source.','Do not write directly into 40_kristal without the real Kristal/Da\'at lifecycle.','Do not claim Interaction Kernel conformance until the exact Profile/version contracts and runtime are supplied and validated.']}
    handoff_hash=sha256_bytes(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')); hid='handoff-'+handoff_hash[:20]; payload['handoff_id']=hid
    outdir=root/'20_ingest/daat-handoff'/key; outdir.mkdir(parents=True,exist_ok=True); out=outdir/f'{hid}.json'; save_json(out,payload); save_json(outdir/'latest.json',{'handoff_id':hid,'path':str(out.relative_to(root)).replace('\\','/'),'snapshot_id':sid,'updated_at':utc_now()})
    print(json.dumps({'handoff_id':hid,'scope_key':key,'snapshot_id':sid,'path':str(out),'project_index_required':False,'interaction_kernel_message_emitted':False},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
