#!/usr/bin/env python3
from __future__ import annotations

import argparse,csv,json,sqlite3
from collections import Counter,defaultdict,deque
from pathlib import Path
from typing import Any
from common import decode_wid,encode_wid,load_json,normalize_name,save_json

FOCUS={
"identity_and_type":[31,21,1559,735,734],"chronology":[569,570,1317],"geography":[19,20,27,495,551],
"intellectual_context":[101,106,135,140,1142,737],"works_bridge":[800],"education_and_affiliation":[69,108,463]}


def conn_db(p):
    c=sqlite3.connect(p); c.row_factory=sqlite3.Row; return c


def relation_class(dt:str|None)->str:
    if dt in {'wikibase-item','wikibase-property','wikibase-lexeme','wikibase-form','wikibase-sense'}: return 'semantic_relation'
    if dt=='external-id': return 'external_identifier'
    if dt in {'commonsMedia','url'}: return 'media_or_locator'
    return 'literal_attribute'


def entity_label(c,eid:int)->dict:
    r=c.execute('SELECT wid,label_fr,label_en,label_mul,kind FROM entity WHERE id=?',(eid,)).fetchone()
    if not r: return {'wid':decode_wid(eid),'label_fr':None,'label_en':None,'label_mul':None}
    return dict(r)


def load_records(registry:Path):
    o=load_json(registry,{})
    return o.get('records') if isinstance(o,dict) else o


def years(c,eid:int)->dict[int,list[int]]:
    d=defaultdict(list)
    for r in c.execute('SELECT property_id,year FROM chronology WHERE subject_id=?',(eid,)): d[r['property_id']].append(r['year'])
    return d


def is_human(c,eid:int)->bool:
    q5=encode_wid('Q5')
    return c.execute('SELECT 1 FROM entity_edge WHERE subject_id=? AND property_id=31 AND target_id=? LIMIT 1',(eid,q5)).fetchone() is not None


def resolve_one(c,seed:dict)->dict:
    norm=normalize_name(seed.get('display_name')); rows=c.execute('SELECT entity_id,lang,name_kind,value FROM name WHERE norm=? LIMIT 50',(norm,)).fetchall()
    candidates=defaultdict(lambda:{'names':[]})
    for r in rows: candidates[r['entity_id']]['names'].append(dict(r))
    birth=((seed.get('chronology') or {}).get('birth_year')); death=((seed.get('chronology') or {}).get('death_year'))
    scored=[]
    for eid,meta in candidates.items():
        s=70.0; reasons=['exact_normalized_name']; ys=years(c,eid)
        if seed.get('representation_kind')=='historical_person' and is_human(c,eid): s+=12; reasons.append('human')
        for pid,wanted,label in [(569,birth,'birth'),(570,death,'death')]:
            if wanted is not None and ys.get(pid):
                delta=min(abs(int(y)-int(wanted)) for y in ys[pid]); bonus=max(0,12-min(delta,12)); s+=bonus
                if delta<=2: reasons.append(label+'_year_close')
        lab=entity_label(c,eid); scored.append({'qid':lab['wid'],'score':round(s,2),'label_fr':lab.get('label_fr'),'label_en':lab.get('label_en'),'reasons':reasons})
    scored.sort(key=lambda x:x['score'],reverse=True)
    if not scored: return {'qid':None,'confidence':'unresolved','candidates':[]}
    top=scored[0]; gap=top['score']-(scored[1]['score'] if len(scored)>1 else 0)
    conf='high' if top['score']>=82 and gap>=6 else ('medium' if top['score']>=74 and gap>=3 else 'ambiguous')
    return {'qid':top['qid'] if conf!='ambiguous' else None,'confidence':conf,'score':top['score'],'candidates':scored[:8]}


def resolve_registry(db:Path,registry:Path,out:Path):
    c=conn_db(db); records=load_records(registry); result={}; unresolved=[]
    for i,s in enumerate(records,1):
        r=resolve_one(c,s); result[s['key']]={'display_name':s['display_name'],**r}
        if not r.get('qid'): unresolved.append({'key':s['key'],'display_name':s['display_name'],**r})
        print(f"resolve {i}/{len(records)} {s['display_name']} -> {r.get('qid')} [{r.get('confidence')}]",flush=True)
    save_json(out,result); up=out.with_name('unresolved.local.jsonl')
    with up.open('w',encoding='utf-8') as f:
        for x in unresolved:f.write(json.dumps(x,ensure_ascii=False)+"\n")
    c.close(); return {'resolved':sum(1 for x in result.values() if x.get('qid')),'total':len(result),'qid_map':str(out)}


def load_qids(p:Path,limit=0):
    o=load_json(p,{}) ; out=[]
    for k,v in o.items():
        q=v.get('qid') if isinstance(v,dict) else v
        if q: out.append((k,q))
    return out[:limit or None]


def property_meta(c,pid:int)->dict:
    r=c.execute('SELECT label_fr,label_en,label_mul FROM entity WHERE id=?',(encode_wid(f'P{pid}'),)).fetchone()
    return {'label_fr':r['label_fr'] if r else None,'label_en':r['label_en'] if r else None,'label_mul':r['label_mul'] if r else None}


def build_signature(db:Path,qidmap:Path,outdir:Path):
    c=conn_db(db); roots=load_qids(qidmap); outdir.mkdir(parents=True,exist_ok=True); sigs=[]; catalog=defaultdict(lambda:{'people':0,'statements':0,'datatype':None})
    for key,q in roots:
        eid=encode_wid(q); rels=[]
        for r in c.execute('SELECT * FROM claim_presence WHERE subject_id=? ORDER BY property_id',(eid,)):
            rec={'property_id':f"P{r['property_id']}",'datatype':r['datatype'],'statement_count':r['statement_count'],'preferred_count':r['preferred_count'],'normal_count':r['normal_count'],'deprecated_count':r['deprecated_count'],'relation_class':relation_class(r['datatype'])}
            rels.append(rec); z=catalog[r['property_id']];z['people']+=1;z['statements']+=r['statement_count'];z['datatype']=z['datatype'] or r['datatype']
        sigs.append({'key':key,'qid':q,'relation_count':len(rels),'relations':rels})
    with (outdir/'people.relation-signatures.jsonl').open('w',encoding='utf-8') as f:
        for s in sigs:f.write(json.dumps(s,ensure_ascii=False)+"\n")
    rows=[]
    for pid,z in catalog.items():
        m=property_meta(c,pid); rows.append({'property_id':f'P{pid}',**m,'datatype':z['datatype'],'relation_class':relation_class(z['datatype']),'people_with_relation':z['people'],'coverage_pct':round(z['people']*100/max(1,len(roots)),2),'total_statements':z['statements']})
    rows.sort(key=lambda x:(-x['people_with_relation'],int(x['property_id'][1:])))
    fields=['property_id','label_fr','label_en','label_mul','datatype','relation_class','people_with_relation','coverage_pct','total_statements']
    with (outdir/'relations.catalog.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    pids=[int(x['property_id'][1:]) for x in rows]
    with (outdir/'people.relation-presence-matrix.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields2=['key','qid']+[f'P{x}' for x in pids];w=csv.DictWriter(f,fieldnames=fields2);w.writeheader()
        for s in sigs:
            present={x['property_id'] for x in s['relations']}; row={'key':s['key'],'qid':s['qid']}; row.update({f'P{x}':1 if f'P{x}' in present else 0 for x in pids});w.writerow(row)
    focus=[]
    bypid={int(x['property_id'][1:]):x for x in rows}
    for group,ps in FOCUS.items():
        for pid in ps:
            x=bypid.get(pid,{});focus.append({'group':group,'property_id':f'P{pid}','label_fr':x.get('label_fr'),'label_en':x.get('label_en'),'people_with_relation':x.get('people_with_relation',0),'coverage_pct':x.get('coverage_pct',0)})
    with (outdir/'focus-relations.coverage.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields3=['group','property_id','label_fr','label_en','people_with_relation','coverage_pct'];w=csv.DictWriter(f,fieldnames=fields3);w.writeheader();w.writerows(focus)
    save_json(outdir/'run-manifest.json',{'backend':'local_sqlite','root_count':len(roots),'values_stored':False,'db':str(db)})
    c.close(); return {'roots':len(roots),'relations':len(rows),'out':str(outdir)}


def pids_from_file(p:Path)->set[int]:
    o=load_json(p,[]); vals=o if isinstance(o,list) else o.get('selected_properties',[])
    return {int(x[1:]) for x in vals if isinstance(x,str) and x.startswith('P') and x[1:].isdigit()}


def traverse(c,roots:set[int],pids:set[int],levels:int,collect=False):
    frontier=set(roots); nodes={x:1 for x in roots}; edges=[]; sigrows=[]; layers=[{'level':1,'kind':'object','unique_objects':len(frontier)}]
    rel_level=2
    while frontier and rel_level<=levels:
        marker_total=0
        for batch in chunks(sorted(frontier),700):
            qs=','.join('?'*len(batch)); marker_total+=c.execute(f'SELECT COUNT(*) FROM claim_presence WHERE subject_id IN ({qs})',batch).fetchone()[0]
            if collect:
                for r in c.execute(f'SELECT subject_id,property_id,datatype,statement_count FROM claim_presence WHERE subject_id IN ({qs})',batch):
                    sigrows.append({'level':rel_level,'qid':decode_wid(r['subject_id']),'property_id':f"P{r['property_id']}",'datatype':r['datatype'],'statement_count':r['statement_count']})
        layers.append({'level':rel_level,'kind':'relation_marker','marker_rows':marker_total,'objects':len(frontier)})
        if rel_level+1>levels: break
        nxt=set(); edge_count=0
        for batch in chunks(sorted(frontier),500):
            qs=','.join('?'*len(batch)); ps=','.join('?'*len(pids)); params=batch+sorted(pids)
            sql=f'SELECT subject_id,property_id,target_id,statement_count,best_rank FROM entity_edge WHERE subject_id IN ({qs}) AND property_id IN ({ps})'
            for r in c.execute(sql,params):
                edge_count+=1; nxt.add(r['target_id'])
                if r['target_id'] not in nodes:nodes[r['target_id']]=rel_level+1
                if collect:edges.append({'source_qid':decode_wid(r['subject_id']),'property_id':f"P{r['property_id']}",'target_wid':decode_wid(r['target_id']),'statement_count':r['statement_count'],'best_rank':r['best_rank'],'relation_level':rel_level,'value_level':rel_level+1})
        frontier=nxt;layers.append({'level':rel_level+1,'kind':'object','unique_objects':len(frontier),'edges':edge_count});rel_level+=2
    return nodes,edges,sigrows,layers


def chunks(xs:list[int],n:int):
    for i in range(0,len(xs),n):yield xs[i:i+n]


def estimate_expand(db:Path,qidmap:Path,pids:set[int],levels:int):
    c=conn_db(db); roots={encode_wid(q) for _,q in load_qids(qidmap)}; roots={x for x in roots if x is not None}; nodes,edges,sigs,layers=traverse(c,roots,pids,levels,False);c.close()
    return {'exact_local_estimate':True,'root_count':len(roots),'selected_properties':[f'P{x}' for x in sorted(pids)],'levels':levels,'layers':layers,'unique_objects_total':len(nodes)}


def expand(db:Path,qidmap:Path,pids:set[int],levels:int,outdir:Path):
    c=conn_db(db); roots={encode_wid(q) for _,q in load_qids(qidmap)};roots={x for x in roots if x is not None}; nodes,edges,sigs,layers=traverse(c,roots,pids,levels,True);outdir.mkdir(parents=True,exist_ok=True)
    with (outdir/'graph.nodes.jsonl').open('w',encoding='utf-8') as f:
        for eid,level in sorted(nodes.items()):
            m=entity_label(c,eid);m.update({'first_seen_level':level});f.write(json.dumps(m,ensure_ascii=False)+"\n")
    with (outdir/'graph.edges.jsonl').open('w',encoding='utf-8') as f:
        for e in edges:f.write(json.dumps(e,ensure_ascii=False)+"\n")
    with (outdir/'node.relation-signatures.jsonl').open('w',encoding='utf-8') as f:
        for s in sigs:f.write(json.dumps(s,ensure_ascii=False)+"\n")
    man={'backend':'local_sqlite','levels':levels,'selected_properties':[f'P{x}' for x in sorted(pids)],'node_count':len(nodes),'edge_count':len(edges),'layers':layers};save_json(outdir/'expansion-manifest.json',man);c.close();return man


def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    r=sub.add_parser('resolve');r.add_argument('--db',required=True);r.add_argument('--registry',required=True);r.add_argument('--out',required=True)
    s=sub.add_parser('signature');s.add_argument('--db',required=True);s.add_argument('--qid-map',required=True);s.add_argument('--out',required=True)
    for name in ['estimate','expand']:
        x=sub.add_parser(name);x.add_argument('--db',required=True);x.add_argument('--qid-map',required=True);x.add_argument('--properties-file',required=True);x.add_argument('--levels',type=int,default=3);x.add_argument('--out',default='')
    a=ap.parse_args()
    if a.cmd=='resolve': print(json.dumps(resolve_registry(Path(a.db),Path(a.registry),Path(a.out)),ensure_ascii=False,indent=2))
    elif a.cmd=='signature': print(json.dumps(build_signature(Path(a.db),Path(a.qid_map),Path(a.out)),ensure_ascii=False,indent=2))
    else:
        pids=pids_from_file(Path(a.properties_file))
        if not pids: raise SystemExit('Aucune propriété sélectionnée')
        if a.cmd=='estimate': print(json.dumps(estimate_expand(Path(a.db),Path(a.qid_map),pids,a.levels),ensure_ascii=False,indent=2))
        else: print(json.dumps(expand(Path(a.db),Path(a.qid_map),pids,a.levels,Path(a.out)),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
