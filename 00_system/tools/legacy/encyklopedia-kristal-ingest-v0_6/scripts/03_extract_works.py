from __future__ import annotations
import argparse, json
from collections import defaultdict
from pathlib import Path
from harvestlib import *


def main():
    ap=argparse.ArgumentParser(description='Discover authored/notable works around resolved people.')
    ap.add_argument('--root',default=''); ap.add_argument('--run-dir',required=True); ap.add_argument('--config',default=''); ap.add_argument('--db',default=''); ap.add_argument('--qid-map',default=''); ap.add_argument('--allow-partial-db',action='store_true')
    a=ap.parse_args(); root=find_root(a.root or None); run=Path(a.run_dir); run.mkdir(parents=True,exist_ok=True)
    cfg=load_json(a.config or root/'00_system/tools/encyklopedia-kristal-ingest/config/harvest.default.json',{}); wc=cfg['works']
    db=Path(a.db) if a.db else root/'30_working/wikidata/wikidata.compact.sqlite'; qmp=Path(a.qid_map) if a.qid_map else root/'30_working/registry/qid-map.local.json'
    people=read_jsonl(run/'people.jsonl'); c=open_db(db); meta=assert_db_ready(c,a.allow_partial_db)
    direct=wc.get('discover_direct',{}); rev=dict(wc.get('discover_reverse',{}));
    if wc.get('include_optional_reverse'): rev.update(wc.get('optional_reverse',{}))
    discoveries=defaultdict(list); person_edges=[]; maxpp=int(wc.get('max_works_per_person') or 0)
    for i,p in enumerate(people,1):
        peid=encode_wid(p['qid']); candidates=[]
        for e in relation_edges(c,peid,direct):
            wid=e['target_wid']; candidates.append(wid); discoveries[wid].append({'person_key':p['seed_key'],'person_qid':p['qid'],'relation':e['property_id'],'role':e['role'],'direction':'outgoing'})
            person_edges.append({'person_key':p['seed_key'],'person_qid':p['qid'],'work_wid':wid,'relation':e['property_id'],'role':e['role'],'direction':'outgoing'})
        remaining=max(0,maxpp-len(set(candidates))) if maxpp else 0
        for e in reverse_edges(c,peid,rev,remaining if maxpp else 0):
            wid=e['source_wid']; candidates.append(wid); discoveries[wid].append({'person_key':p['seed_key'],'person_qid':p['qid'],'relation':e['property_id'],'role':e['role'],'direction':'incoming'})
            person_edges.append({'person_key':p['seed_key'],'person_qid':p['qid'],'work_wid':wid,'relation':e['property_id'],'role':e['role'],'direction':'incoming'})
        print(f"works {i}/{len(people)} {p['seed_display_name']} -> {len(set(candidates))} candidate(s)",flush=True)
    records=[]
    for j,wid in enumerate(sorted(discoveries),1):
        r=object_record(c,wid,wc.get('describe_relations',{}),True)
        r.update({'record_type':'work_or_document_candidate','discovered_via':discoveries[wid],'literal_relation_presence_expected':wc.get('literal_presence_only',[]),'source':{'system':'Wikidata local snapshot','entity':wid,'db_dump_file':meta.get('dump_file'),'db_dump_sha1':meta.get('dump_sha1')}})
        records.append(r)
        if j%500==0: print(f"work records {j}/{len(discoveries)}",flush=True)
    write_jsonl(run/'works.jsonl',records); write_jsonl(run/'person-work-edges.jsonl',person_edges)
    # simple type distribution via P31 labels already included
    dist=defaultdict(int)
    for r in records:
        for e in r.get('relations',[]):
            if e['property_id']=='P31': dist[(e.get('target_wid'),e.get('target_label_en') or e.get('target_label_fr'))]+=1
    rows=[{'type_wid':k[0],'type_label':k[1],'work_count':v} for k,v in dist.items()]; rows.sort(key=lambda x:-x['work_count'])
    write_csv(run/'works.type-distribution.csv',rows,['type_wid','type_label','work_count'])
    save_json(run/'works.summary.json',{'schema_version':'encyklopedia-works-working/v1','generated_at':utc_now(),'people_count':len(people),'work_candidates':len(records),'person_work_edges':len(person_edges),'discovery_direct':direct,'discovery_reverse':rev})
    c.close(); print(json.dumps({'works':len(records),'edges':len(person_edges),'out':str(run)},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
