from __future__ import annotations
import argparse, json
from collections import defaultdict
from pathlib import Path
from harvestlib import *


def main():
    ap=argparse.ArgumentParser(description='Extract movements, ideologies, fields and influence network around people.')
    ap.add_argument('--root',default=''); ap.add_argument('--run-dir',required=True); ap.add_argument('--config',default=''); ap.add_argument('--db',default=''); ap.add_argument('--allow-partial-db',action='store_true')
    a=ap.parse_args(); root=find_root(a.root or None); run=Path(a.run_dir); run.mkdir(parents=True,exist_ok=True)
    cfg=load_json(a.config or root/'00_system/tools/encyklopedia-kristal-ingest/config/harvest.default.json',{}); ic=cfg['intellectual_context']
    db=Path(a.db) if a.db else root/'30_working/wikidata/wikidata.compact.sqlite'; people=read_jsonl(run/'people.jsonl'); c=open_db(db); meta=assert_db_ready(c,a.allow_partial_db)
    current_refs=defaultdict(list); domain_refs=defaultdict(list); influence_edges=[]
    current_rels=dict(ic.get('currents',{})); domain_rels=dict(ic.get('domains',{})); infl_rels=dict(ic.get('influence',{}))
    for i,p in enumerate(people,1):
        eid=encode_wid(p['qid'])
        for e in relation_edges(c,eid,current_rels):
            current_refs[e['target_wid']].append({'person_key':p['seed_key'],'person_qid':p['qid'],'property_id':e['property_id'],'role':e['role']})
        for e in relation_edges(c,eid,domain_rels):
            domain_refs[e['target_wid']].append({'person_key':p['seed_key'],'person_qid':p['qid'],'property_id':e['property_id'],'role':e['role']})
        for e in relation_edges(c,eid,infl_rels):
            influence_edges.append({'source_person_key':p['seed_key'],'source_qid':p['qid'],'property_id':e['property_id'],'role':'influenced_by','target_wid':e['target_wid'],'target_label_fr':e.get('target_label_fr'),'target_label_en':e.get('target_label_en'),'direction':'outgoing'})
        if ic.get('include_reverse_influence',True):
            for e in reverse_edges(c,eid,infl_rels):
                influence_edges.append({'source_wid':e['source_wid'],'source_label_fr':e.get('source_label_fr'),'source_label_en':e.get('source_label_en'),'property_id':e['property_id'],'role':'influenced','target_person_key':p['seed_key'],'target_qid':p['qid'],'direction':'incoming'})
        print(f"context {i}/{len(people)} {p['seed_display_name']}",flush=True)
    currents=[]
    for wid,links in sorted(current_refs.items()):
        r=object_record(c,wid,ic.get('describe_relations',{}),True); r.update({'record_type':'intellectual_current_or_ideology','linked_people':links,'source':{'system':'Wikidata local snapshot','entity':wid,'db_dump_file':meta.get('dump_file')}}); currents.append(r)
    domains=[]
    for wid,links in sorted(domain_refs.items()):
        r=object_record(c,wid,ic.get('describe_relations',{}),True); r.update({'record_type':'field_of_work','linked_people':links,'source':{'system':'Wikidata local snapshot','entity':wid,'db_dump_file':meta.get('dump_file')}}); domains.append(r)
    write_jsonl(run/'currents.jsonl',currents); write_jsonl(run/'domains.jsonl',domains); write_jsonl(run/'influence-edges.jsonl',influence_edges)
    save_json(run/'intellectual-context.summary.json',{'schema_version':'encyklopedia-intellectual-context-working/v1','generated_at':utc_now(),'currents':len(currents),'domains':len(domains),'influence_edges':len(influence_edges)})
    c.close(); print(json.dumps({'currents':len(currents),'domains':len(domains),'influence_edges':len(influence_edges)},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
