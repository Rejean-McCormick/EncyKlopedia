from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path
from harvestlib import *

PINNED='af703bf02ee04a69a5f2ad6694fa8b8e56ae2b19'
SCHEMA_REL='docs/Technical-Reference/kristal-docs-v5/02-schemas/structured-epistemic-state.schema.json'


def probe_kristal(path: str) -> dict:
    if not path:
        return {'configured':False,'status':'not_configured'}
    p=Path(path)
    out={'configured':True,'path':str(p),'exists':p.exists(),'pinned_commit_expected':PINNED}
    if not p.exists(): out['status']='missing'; return out
    schema=p/SCHEMA_REL; out['structured_epistemic_state_schema']=str(schema); out['schema_exists']=schema.exists()
    git=p/'.git'
    if git.exists():
        try:
            head=subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True,stderr=subprocess.STDOUT).strip(); out['git_head']=head; out['pin_matches']=head==PINNED
        except Exception as e: out['git_error']=str(e)
    out['status']='ready' if out.get('schema_exists') and (out.get('pin_matches',True)) else 'needs_attention'
    return out


def main():
    ap=argparse.ArgumentParser(description='Prepare a Da\'at handoff bundle. Does not invent Kristal schemas or recognition.')
    ap.add_argument('--root',default=''); ap.add_argument('--snapshot-id',default=''); ap.add_argument('--kristal-root',default='')
    a=ap.parse_args(); root=find_root(a.root or None); latest=load_json(root/'20_ingest/snapshots/encyklopedia/latest.json',{})
    sid=a.snapshot_id or latest.get('snapshot_id')
    if not sid: raise SystemExit('Aucun snapshot EncyKlopedia. Lance 06_build_source_snapshot.py.')
    snap=root/'20_ingest/snapshots/encyklopedia'/sid; man=snap/'snapshot-manifest.json'
    if not man.exists(): raise SystemExit(f'Manifest absent: {man}')
    cfg=load_json(root/'00_system/tools/encyklopedia-kristal-ingest/config/harvest.default.json',{}); kc=cfg.get('kristal',{})
    out=root/'20_ingest/handoffs/kristal'/sid; out.mkdir(parents=True,exist_ok=True)
    probe=probe_kristal(a.kristal_root)
    mapping=[
      {'source':'people.jsonl','semantic_role':'source-bound person identity/context assertions','notes':'Seed key remains the EncyKlopedia anchor; Wikidata QID is external identity/provenance.'},
      {'source':'works.jsonl','semantic_role':'source-bound work/document entity assertions','notes':'Discovery via P50/P800 is preserved; no claim that every candidate is a book.'},
      {'source':'person-work-edges.jsonl','semantic_role':'authorship/notable-work relationships','notes':'Direction and Wikidata property are preserved.'},
      {'source':'currents.jsonl','semantic_role':'movement/ideology associations','notes':'P135 and P1142 stay distinct.'},
      {'source':'domains.jsonl','semantic_role':'field-of-work associations','notes':'P101 is not collapsed into movement.'},
      {'source':'influence-edges.jsonl','semantic_role':'influence graph','notes':'P737 direction is preserved; absence is not interpreted as no influence.'}
    ]
    handoff={
      'schema_version':'koa-daat-source-handoff/v1','handoff_id':sid,'created_at':utc_now(),'status':'ready_for_daat_mapping',
      'source_snapshot':relpath(snap,root),'source_manifest':relpath(man,root),'source_manifest_sha256':sha256_file(man),
      'target':{'system':'Kristal','version':kc.get('pinned_version'),'commit':kc.get('pinned_commit'),'canonicalization_profile':kc.get('canonicalization_profile'),'mapping_boundary':kc.get('mapping_boundary','Da\'at'),'target_input':kc.get('target_input','Structured Epistemic State')},
      'mapping_plan':mapping,'kristal_probe':probe,
      'invariants':['No direct write to Kristal Reference Exchange.','Compilation, validation, recognition, publication and activation remain separate.','Wikidata data is external-source material with provenance, not authority recognition.','40_kristal remains untouched until the real pinned Kristal/Da\'at path produces Kristal-owned artifacts.']
    }
    save_json(out/'daat-handoff.json',handoff)
    (out/'README.md').write_text(f"""# Da'at handoff — {sid}\n\nThis bundle points to the immutable EncyKlopedia source snapshot at `{relpath(snap,root)}`.\n\nIt is **not** a Kristal artifact. Da'at must map it into the pinned Kristal v5 Structured Epistemic State.\nNo Reference status, validation or authority recognition is implied.\n""",encoding='utf-8')
    save_json(root/'20_ingest/handoffs/kristal/latest.json',{'handoff_id':sid,'path':relpath(out,root),'handoff_sha256':sha256_file(out/'daat-handoff.json'),'updated_at':utc_now()})
    print(json.dumps({'handoff':str(out/'daat-handoff.json'),'kristal_probe':probe,'status':'ready_for_daat_mapping'},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
