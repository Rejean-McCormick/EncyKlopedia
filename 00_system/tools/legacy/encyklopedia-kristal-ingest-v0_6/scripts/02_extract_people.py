from __future__ import annotations
import argparse, json
from pathlib import Path
from harvestlib import *


def main():
    ap=argparse.ArgumentParser(description='Extract people-centred Wikidata working records.')
    ap.add_argument('--root',default=''); ap.add_argument('--run-dir',required=True); ap.add_argument('--config',default='')
    ap.add_argument('--db',default=''); ap.add_argument('--registry',default=''); ap.add_argument('--qid-map',default=''); ap.add_argument('--allow-partial-db',action='store_true')
    a=ap.parse_args(); root=find_root(a.root or None); run=Path(a.run_dir); run.mkdir(parents=True,exist_ok=True)
    cfg=load_json(a.config or root/'00_system/tools/encyklopedia-kristal-ingest/config/harvest.default.json',{})
    db=Path(a.db) if a.db else root/'30_working/wikidata/wikidata.compact.sqlite'; reg=Path(a.registry) if a.registry else root/'10_sources/seeds/active/intellectual-registry/intellectuals.seed.json'; qmp=Path(a.qid_map) if a.qid_map else root/'30_working/registry/qid-map.local.json'
    regmeta, records=load_registry(reg); qmap=load_qid_map(qmp); c=open_db(db); meta=assert_db_ready(c,a.allow_partial_db)
    rels=cfg['people']['direct_relations']; rows=[]; coverage={}; unresolved=[]
    for i,seed in enumerate(records,1):
        qm=qmap.get(seed.get('key'),{}); qid=qm.get('qid')
        if not qid:
            unresolved.append({'key':seed.get('key'),'display_name':seed.get('display_name'),'resolution':qm}); continue
        eid=encode_wid(qid); e=entity(c,eid)
        edges=relation_edges(c,eid,rels); present=relation_presence(c,eid) if cfg['people'].get('include_all_relation_presence',True) else []
        for x in present: coverage[x['property_id']]=coverage.get(x['property_id'],0)+1
        rows.append({
            'record_type':'person', 'seed_key':seed.get('key'), 'seed_display_name':seed.get('display_name'), 'qid':qid,
            'resolution':{k:v for k,v in qm.items() if k!='candidates'},
            'representation_kind':seed.get('representation_kind'), 'seed_chronology':seed.get('chronology'), 'region_tradition':seed.get('region_tradition'),
            'isced_f_domains':seed.get('isced_f_domains') or [], 'tags':seed.get('tags') or [], 'seed_notes':seed.get('notes'),
            'labels':{'fr':e.get('label_fr'),'en':e.get('label_en'),'mul':e.get('label_mul')},
            'descriptions':{'fr':e.get('description_fr'),'en':e.get('description_en')}, 'aliases':aliases(c,eid),
            'wikidata_chronology':chronology(c,eid), 'relations':edges, 'available_relations':present,
            'source':{'system':'Wikidata local snapshot','entity':qid,'db_dump_file':meta.get('dump_file'),'db_dump_sha1':meta.get('dump_sha1')}
        })
        print(f"people {i}/{len(records)} {seed.get('display_name')} -> {qid}",flush=True)
    n=write_jsonl(run/'people.jsonl',rows); write_jsonl(run/'people.unresolved.jsonl',unresolved)
    cov=[{'property_id':p,'people_with_relation':n2,'coverage_pct':round(n2*100/max(1,n),2)} for p,n2 in coverage.items()]; cov.sort(key=lambda x:(-x['people_with_relation'],x['property_id']))
    write_csv(run/'people.relation-coverage.csv',cov,['property_id','people_with_relation','coverage_pct'])
    save_json(run/'people.summary.json',{'schema_version':'encyklopedia-people-working/v1','generated_at':utc_now(),'resolved_people':n,'unresolved_people':len(unresolved),'registry_schema':regmeta.get('schema_version'),'db_meta':meta})
    c.close(); print(json.dumps({'people':n,'unresolved':len(unresolved),'out':str(run)},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
