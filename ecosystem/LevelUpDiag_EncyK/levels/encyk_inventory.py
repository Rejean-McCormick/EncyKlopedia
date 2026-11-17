"""Inspect bounded metadata and inventory sizes; never read the 16k QID file in full."""
import json
from ._encyk_common import data_root,add,safe_children,bounded_json

def run(cfg,report):
    root=data_root(cfg)
    base=root/'30_working/skope-large-scopes'
    jobs=safe_children(base,10)
    if not base.is_dir():
        add(report,'encyk.skope.inventory.area','WARN','No local large-scope inventory area is available.');return
    add(report,'encyk.skope.inventory.area','PASS','Inventory area exists; only most recent 10 job directories inspected.',{'recent_jobs':len(jobs)})
    previews=[]
    for j in jobs:
        qids=j/'selected-qids.jsonl'
        if not qids.is_file():continue
        info={'job':j.name,'qid_file_bytes':qids.stat().st_size}
        for candidate in ('state.json','status.json','summary.json'):
            try:
                obj=bounded_json(j/candidate,120_000)
                if isinstance(obj,dict):
                    info['status_file']=candidate
                    info['state']=obj.get('state')
                    info['selected']=obj.get('selected') or obj.get('selected_count')
                    break
            except (OSError,ValueError):pass
        previews.append(info)
    add(report,'encyk.skope.inventory.recent','PASS' if previews else 'WARN','Read existing QID inventories without rewriting or enumerating every QID.',{'jobs':previews[:6]})
    folder=root/'20_evidence/scope-snapshots'
    if folder.is_dir():
        snapshots=safe_children(folder,8)
        add(report,'encyk.evidence.snapshots','PASS','Existing evidence snapshot directories found.',{'recent':len(snapshots),'names':[p.name for p in snapshots]})
    else:add(report,'encyk.evidence.snapshots','WARN','No full-evidence snapshot directory found yet; extraction may not have started.')
