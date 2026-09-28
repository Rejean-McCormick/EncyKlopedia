from __future__ import annotations
import argparse, json, shutil
from pathlib import Path
from harvestlib import *


def main():
    ap=argparse.ArgumentParser(description='Publish discovered works as UCKK Mediatheque candidate records, not authoritative catalogue entries.')
    ap.add_argument('--root',default=''); ap.add_argument('--run-dir',required=True); ap.add_argument('--config',default=''); ap.add_argument('--snapshot-name',default='')
    a=ap.parse_args(); root=find_root(a.root or None); run=Path(a.run_dir)
    cfg=load_json(a.config or root/'00_system/tools/encyklopedia-kristal-ingest/config/harvest.default.json',{}); mc=cfg.get('mediatheque',{})
    if not mc.get('emit_work_candidates',True): print('{"skipped":true}'); return
    works=read_jsonl(run/'works.jsonl'); name=a.snapshot_name or run.name
    out=root/'50_mediatheque/catalog/candidates/wikidata'/name; out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for w in works:
        rows.append({
            'record_type':'mediatheque_work_candidate', 'status':mc.get('status','candidate_from_wikidata_local'), 'wikidata_wid':w.get('wid'),
            'labels':w.get('labels'), 'descriptions':w.get('descriptions'), 'discovered_via':w.get('discovered_via'),
            'relations':w.get('relations'), 'available_relations':w.get('available_relations'),
            'provider_resolution_status':'not_started', 'rights_resolution_status':'not_started', 'edition_resolution_status':'not_started'
        })
    write_jsonl(out/'works.candidates.jsonl',rows)
    save_json(out/'manifest.json',{'schema_version':'uckk-mediatheque-candidate-feed/v1','generated_at':utc_now(),'source_run':relpath(run,root),'candidate_count':len(rows),'authority':'candidate_only','note':mc.get('note')})
    print(json.dumps({'candidates':len(rows),'out':str(out)},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
