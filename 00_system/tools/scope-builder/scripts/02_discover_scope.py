from __future__ import annotations
import argparse, json, time
from collections import defaultdict
from pathlib import Path
from scope_common import *


def add_entity(ent:dict[str,dict[str,Any]],wid:str,role:str,reason:dict[str,Any],depth:int=1)->bool:
    rec=ent.setdefault(wid,{'wid':wid,'roles':set(),'reasons':[],'first_depth':depth})
    before=(len(rec['roles']),len(rec['reasons']),rec['first_depth'])
    rec['roles'].add(role); rec['first_depth']=min(rec['first_depth'],depth)
    sig=json.dumps(reason,sort_keys=True,separators=(',',':'))
    if all(json.dumps(x,sort_keys=True,separators=(',',':'))!=sig for x in rec['reasons']):rec['reasons'].append(reason)
    return before!=(len(rec['roles']),len(rec['reasons']),rec['first_depth'])


def query_out(c,sources:list[str],pids:list[int]|None=None):
    eids=[encode_wid(x) for x in sources]; eids=[x for x in eids if x is not None]
    for batch in chunks(eids,500):
        qs=','.join('?'*len(batch)); params=list(batch); cond=''
        if pids:
            ps=','.join('?'*len(pids)); cond=f' AND property_id IN ({ps})'; params+=pids
        sql=f'SELECT subject_id,property_id,target_id,statement_count,best_rank FROM entity_edge WHERE subject_id IN ({qs}){cond}'
        yield from c.execute(sql,params)


def query_in(c,targets:list[str],pids:list[int]):
    if not pids:return
    eids=[encode_wid(x) for x in targets]; eids=[x for x in eids if x is not None]
    for batch in chunks(eids,400):
        qs=','.join('?'*len(batch)); ps=','.join('?'*len(pids)); params=list(batch)+pids
        sql=f'SELECT subject_id,property_id,target_id,statement_count,best_rank FROM entity_edge WHERE target_id IN ({qs}) AND property_id IN ({ps})'
        yield from c.execute(sql,params)


def policy(cfg:dict[str,Any])->dict[str,Any]:
    disc=cfg.get('discovery') or {}; sem=scope_root_semantics(cfg)
    return {
        'root_role':sem['role'],
        'root_kind':sem['kind'],
        'include_all':include_all_root_relations(cfg),
        'root_roles':disc.get('root_relation_roles') or {},
        'default_neighbor':root_neighbor_role(cfg),
        'reverse':reverse_root_relations(cfg),
    }


def add_reverse_entity(entities,edges,edge_keys,src,pid,target,rule,*,statement_id=None,rank=None,count=None,best_rank=None):
    source_role=rule.get('source_role') or 'other'; relation_role=rule.get('relation_role') or 'reverse_root_relation'
    add_entity(entities,src,source_role,{'kind':'reverse_root_relation','root':target,'property_id':pid},2)
    k=(src,pid,target,'reverse_root_relation',statement_id)
    if k not in edge_keys:
        edge_keys.add(k)
        edges.append({'source_wid':src,'property_id':pid,'target_wid':target,'direction':'out','role':relation_role,
                      'statement_id':statement_id,'rank':rank,'statement_count':count,'best_rank':best_rank,
                      'stage':'reverse_root_relation'})


def index_discovery(root:Path,cfg:dict[str,Any],roots:list[str],db:Path)->tuple[dict,list,dict,dict]:
    c=open_db(db,True); meta=assert_global_index(c,True); groups=property_groups(root); disc=cfg.get('discovery') or {}; pol=policy(cfg)
    max_entities=int(disc.get('max_entities') or 250000); max_edges=int(disc.get('max_edges') or 2000000)
    entities={}; edges=[]; edge_keys=set()
    for q in roots:add_entity(entities,q,pol['root_role'],{'kind':'root','root_kind':pol['root_kind']},1)

    def push(src,pid,dst,role,stage,count=None,rank=None,depth=2):
        add_entity(entities,dst,role,{'kind':stage,'source':src,'property_id':pid},depth); k=(src,pid,dst,stage)
        if k not in edge_keys:
            edge_keys.add(k); edges.append({'source_wid':src,'property_id':pid,'target_wid':dst,'direction':'out','role':role,
                                            'statement_count':count,'best_rank':rank,'stage':stage})
        if len(entities)>max_entities or len(edges)>max_edges:raise RuntimeError('Scope discovery cap exceeded; tighten scope config.')

    if pol['include_all']:
        for r in query_out(c,roots,None):
            src=decode_wid(r['subject_id']); pid=f"P{r['property_id']}"; dst=decode_wid(r['target_id'])
            push(src,pid,dst,pol['root_roles'].get(pid,pol['default_neighbor']),'root_all_entity_relations',r['statement_count'],r['best_rank'],2)

    rev=pol['reverse']
    if rev:
        pids=[pid_num(x) for x in rev]
        for r in query_in(c,roots,pids):
            src=decode_wid(r['subject_id']); pid=f"P{r['property_id']}"; target=decode_wid(r['target_id'])
            add_reverse_entity(entities,edges,edge_keys,src,pid,target,rev[pid],count=r['statement_count'],best_rank=r['best_rank'])
            if len(entities)>max_entities or len(edges)>max_edges:raise RuntimeError('Scope discovery cap exceeded; tighten scope config.')

    for stage_index,rule in enumerate(disc.get('follow_rules') or [],1):
        src_roles=set(rule.get('source_roles') or []); sources=[w for w,e in entities.items() if e['roles'] & src_roles]
        if not sources:continue
        props=groups.get(rule.get('property_group')) or {}; pids=[pid_num(x) for x in props]; default_role=rule.get('default_target_role') or 'context'; before=len(entities)
        rows=query_out(c,sources,pids) if rule.get('direction','out')=='out' else query_in(c,sources,pids)
        for r in rows:
            src=decode_wid(r['subject_id']); dst=decode_wid(r['target_id']); pid=f"P{r['property_id']}"; role=(rule.get('target_roles') or {}).get(pid,default_role)
            push(src,pid,dst,role,rule.get('name') or 'follow',r['statement_count'],r['best_rank'],3+stage_index)
        print(f"[discover/index] {rule.get('name')}: sources={len(sources)} new_entities={len(entities)-before}",flush=True)

    metadata=entity_rows(c,entities.keys()); c.close()
    return entities,edges,metadata,{'backend':'index','global_index':str(db),'global_index_meta':meta,'closure_complete':True}


def fast_discovery(root:Path,cfg:dict[str,Any],roots:list[str],dump:Path)->tuple[dict,list,dict,dict]:
    ok,fastmeta=fast_access_status(root,dump)
    if not ok or not fastmeta.get('random_access_ready'):
        raise RuntimeError('Fast-access index exists but random access is unavailable with the installed decompressor backend.')
    groups=property_groups(root); disc=cfg.get('discovery') or {}; pol=policy(cfg)
    max_entities=int(disc.get('max_entities') or 250000); max_edges=int(disc.get('max_edges') or 2000000)
    reverse_props=set(pol['reverse'])
    rules=[]
    for i,rule in enumerate(disc.get('follow_rules') or [],1):
        props=set((groups.get(rule.get('property_group')) or {}).keys()); rules.append((i,rule,props,set(rule.get('source_roles') or [])))
    entities={}; edges=[]; edge_keys=set(); metadata={}
    for q in roots:add_entity(entities,q,pol['root_role'],{'kind':'root','root_kind':pol['root_kind']},1)

    def push(src,pid,dst,role,stage,depth,statement_id=None,rank=None,count=None,best_rank=None):
        changed=add_entity(entities,dst,role,{'kind':stage,'source':src,'property_id':pid},depth); k=(src,pid,dst,stage,statement_id)
        if k not in edge_keys:
            edge_keys.add(k); edges.append({'source_wid':src,'property_id':pid,'target_wid':dst,'direction':'out','role':role,
                                            'statement_id':statement_id,'rank':rank,'statement_count':count,'best_rank':best_rank,'stage':stage}); changed=True
        if len(entities)>max_entities or len(edges)>max_edges:raise RuntimeError('Scope discovery cap exceeded; tighten scope config.')
        return changed

    if reverse_props:
        for r in fast_reverse_edges(root,dump,roots,reverse_props):
            src=r['source_wid']; target=r['target_wid']; pid=r['property_id']
            add_reverse_entity(entities,edges,edge_keys,src,pid,target,pol['reverse'][pid],
                               count=r.get('statement_count'),best_rank=r.get('best_rank'))
            if len(entities)>max_entities or len(edges)>max_edges:raise RuntimeError('Scope discovery cap exceeded; tighten scope config.')

    done_root=set(); done_rules=set(); loops=0; fetched_total=0
    while True:
        loops+=1; need=set()
        for wid,rec in entities.items():
            roles=set(rec['roles'])
            if pol['root_role'] in roles and pol['include_all'] and wid not in done_root:need.add(wid)
            for idx,rule,props,src_roles in rules:
                if roles & src_roles and (wid,idx) not in done_rules:
                    if rule.get('direction','out')!='out':
                        raise RuntimeError('Fast backend supports generic follow rules only in outgoing direction; use global index for generic reverse follow rules.')
                    need.add(wid)
        if not need:break
        rawmap=fast_fetch_raw(root,dump,need)
        missing=need-set(rawmap)
        if missing:raise RuntimeError(f'Fast locator could not fetch {len(missing)} selected QID(s), e.g. {sorted(missing)[:10]}')
        fetched_total+=len(rawmap)
        for wid,raw in rawmap.items():
            try:obj=json_loads(raw)
            except Exception:continue
            label,lang=entity_label(obj); metadata[wid]={'wid':wid,'kind':obj.get('type'),'label_fr':((obj.get('labels') or {}).get('fr') or {}).get('value'),'label_en':((obj.get('labels') or {}).get('en') or {}).get('value'),'label_mul':((obj.get('labels') or {}).get('mul') or {}).get('value'),'label_any':label,'label_lang':lang}
            roles=set(entities.get(wid,{}).get('roles') or [])
            if pol['root_role'] in roles and pol['include_all'] and wid not in done_root:
                for e in entity_edges_from_obj(obj,None):
                    push(wid,e['property_id'],e['target_wid'],pol['root_roles'].get(e['property_id'],pol['default_neighbor']),
                         'root_all_entity_relations',2,e.get('statement_id'),e.get('rank'))
                done_root.add(wid)
            roles=set(entities.get(wid,{}).get('roles') or [])
            for idx,rule,props,src_roles in rules:
                if not (roles & src_roles) or (wid,idx) in done_rules:continue
                default_role=rule.get('default_target_role') or 'context'; role_map=rule.get('target_roles') or {}
                for e in entity_edges_from_obj(obj,props):
                    push(wid,e['property_id'],e['target_wid'],role_map.get(e['property_id'],default_role),
                         rule.get('name') or 'follow',3+idx,e.get('statement_id'),e.get('rank'))
                done_rules.add((wid,idx))
        print(f'[discover/fast] loop={loops} fetched={len(rawmap):,} entities={len(entities):,} edges={len(edges):,}',flush=True)
    return entities,edges,metadata,{'backend':'fast','fast_access':fastmeta,'closure_complete':True,'fetch_loops':loops,'fetched_entities':fetched_total}


def raw_discovery(root:Path,cfg:dict[str,Any],roots:list[str],dump:Path)->tuple[dict,list,dict,dict]:
    groups=property_groups(root); disc=cfg.get('discovery') or {}; pol=policy(cfg)
    max_entities=int(disc.get('max_entities') or 250000); max_edges=int(disc.get('max_edges') or 2000000); max_passes=int(disc.get('raw_max_passes') or 5)
    reverse_props=set(pol['reverse']); root_set=set(roots)
    rules=[]
    for i,rule in enumerate(disc.get('follow_rules') or [],1):
        props=set((groups.get(rule.get('property_group')) or {}).keys()); rules.append((i,rule,props,set(rule.get('source_roles') or [])))
    entities={}; edges=[]; edge_keys=set(); metadata={}
    for q in roots:add_entity(entities,q,pol['root_role'],{'kind':'root','root_kind':pol['root_kind']},1)
    root_bytes=[q.encode('ascii') for q in roots]; reverse_prop_bytes=[f'"{p}"'.encode() for p in reverse_props]

    def push(src,pid,dst,role,stage,depth,statement_id=None,rank=None)->bool:
        changed=add_entity(entities,dst,role,{'kind':stage,'source':src,'property_id':pid},depth); k=(src,pid,dst,stage,statement_id)
        if k not in edge_keys:
            edge_keys.add(k); edges.append({'source_wid':src,'property_id':pid,'target_wid':dst,'direction':'out','role':role,
                                            'statement_id':statement_id,'rank':rank,'stage':stage}); changed=True
        if len(entities)>max_entities or len(edges)>max_edges:raise RuntimeError('Scope discovery cap exceeded; tighten scope config.')
        return changed

    closure=False; pass_reports=[]
    for pass_no in range(1,max_passes+1):
        before_entities=len(entities); before_edges=len(edges); scanned=0; parsed=0; started=time.time(); last=started
        print(f'[discover/raw] pass {pass_no}/{max_passes} | selected_start={len(entities):,}',flush=True)
        for raw in iter_dump_raw(dump,root=root):
            scanned+=1; wid=raw_entity_id(raw)
            if not wid:continue
            selected=wid in entities; reverse_possible=False
            if pass_no==1 and reverse_props and not selected:
                reverse_possible=any(pb in raw for pb in reverse_prop_bytes) and any(qb in raw for qb in root_bytes)
            if not selected and not reverse_possible:continue
            try:obj=json_loads(raw); parsed+=1
            except Exception:continue
            label,lang=entity_label(obj); metadata[wid]={'wid':wid,'kind':obj.get('type'),'label_fr':((obj.get('labels') or {}).get('fr') or {}).get('value'),'label_en':((obj.get('labels') or {}).get('en') or {}).get('value'),'label_mul':((obj.get('labels') or {}).get('mul') or {}).get('value'),'label_any':label,'label_lang':lang}

            if pass_no==1 and reverse_props:
                for e in entity_edges_from_obj(obj,reverse_props):
                    if e['target_wid'] in root_set:
                        add_reverse_entity(entities,edges,edge_keys,wid,e['property_id'],e['target_wid'],pol['reverse'][e['property_id']],
                                           statement_id=e.get('statement_id'),rank=e.get('rank'))
                        if len(entities)>max_entities or len(edges)>max_edges:raise RuntimeError('Scope discovery cap exceeded; tighten scope config.')

            roles=set(entities.get(wid,{}).get('roles') or [])
            if pol['root_role'] in roles and pol['include_all']:
                for e in entity_edges_from_obj(obj,None):
                    push(wid,e['property_id'],e['target_wid'],pol['root_roles'].get(e['property_id'],pol['default_neighbor']),
                         'root_all_entity_relations',2,e.get('statement_id'),e.get('rank'))

            roles=set(entities.get(wid,{}).get('roles') or [])
            for idx,rule,props,source_roles in rules:
                if not (roles & source_roles):continue
                if rule.get('direction','out')!='out':
                    continue
                default_role=rule.get('default_target_role') or 'context'; role_map=rule.get('target_roles') or {}
                for e in entity_edges_from_obj(obj,props):
                    push(wid,e['property_id'],e['target_wid'],role_map.get(e['property_id'],default_role),
                         rule.get('name') or 'follow',3+idx,e.get('statement_id'),e.get('rank'))
            now=time.time()
            if now-last>60:
                print(f'[discover/raw] pass={pass_no} scanned={scanned:,} parsed={parsed:,} entities={len(entities):,} edges={len(edges):,} elapsed={(now-started)/3600:.2f}h',flush=True); last=now

        added_entities=len(entities)-before_entities; added_edges=len(edges)-before_edges
        pass_reports.append({'pass':pass_no,'scanned':scanned,'parsed':parsed,'added_entities':added_entities,'added_edges':added_edges,'entity_count':len(entities),'edge_count':len(edges),'elapsed_seconds':round(time.time()-started,2)})
        print(f'[discover/raw] pass {pass_no} done | +entities={added_entities:,} +edges={added_edges:,}',flush=True)
        if added_entities==0 and added_edges==0:
            closure=True; break
    if not closure:
        raise RuntimeError(f'Raw discovery did not reach closure after {max_passes} passes. Increase discovery.raw_max_passes or tighten follow rules.')
    return entities,edges,metadata,{'backend':'raw','dump':dump_descriptor(root,dump),'closure_complete':closure,'passes':pass_reports}


def main():
    ap=argparse.ArgumentParser(description='Discover a scope from configured roots. Root semantics are domain-specific; raw evidence remains lossless.')
    ap.add_argument('--root',default=''); ap.add_argument('--scope',required=True); ap.add_argument('--backend',choices=['auto','index','fast','raw'],default='auto'); ap.add_argument('--db',default=''); ap.add_argument('--dump',default='')
    a=ap.parse_args(); root=find_root(a.root or None); cfg_path,cfg=load_scope_config(root,a.scope); key=cfg['scope_key']; wd=scope_workdir(root,key); wd.mkdir(parents=True,exist_ok=True)
    qmap=load_json(wd/'roots.resolved.json',{}) or {}; roots=[v['qid'] for v in qmap.values() if isinstance(v,dict) and v.get('qid')]
    if not roots:raise SystemExit('Aucune racine résolue. Exécute 01_resolve_roots.py.')
    db=Path(a.db) if a.db else default_global_db(root); dump=Path(a.dump) if a.dump else find_dump(root); backend=choose_discovery_backend(root,a.backend,db,dump)
    if backend=='index':entities,edges,metadata,backend_info=index_discovery(root,cfg,roots,db)
    elif backend=='fast':
        try:entities,edges,metadata,backend_info=fast_discovery(root,cfg,roots,dump)
        except Exception as exc:
            if a.backend!='auto':raise
            print(f'[discover/auto] fast backend unavailable for this scope ({exc}); falling back to raw scan.',flush=True)
            backend='raw'; entities,edges,metadata,backend_info=raw_discovery(root,cfg,roots,dump)
    else:entities,edges,metadata,backend_info=raw_discovery(root,cfg,roots,dump)

    rows=[]; role_counts=defaultdict(int)
    for wid in sorted(entities,key=lambda x:(x[0],int(x[1:]) if x[1:].isdigit() else 0)):
        rec=entities[wid]; m=metadata.get(wid,{"wid":wid}); roles=sorted(rec['roles'])
        for role in roles:role_counts[role]+=1
        rows.append({'wid':wid,'roles':roles,'first_depth':rec['first_depth'],'label_fr':m.get('label_fr'),'label_en':m.get('label_en'),'label_mul':m.get('label_mul'),'label_any':m.get('label_any'),'kind':m.get('kind'),'reasons':rec['reasons']})
    outdir=wd/'discovery'; outdir.mkdir(parents=True,exist_ok=True); write_jsonl(outdir/'entities.jsonl',rows); write_jsonl(outdir/'edges.jsonl',edges)
    stats={'schema_version':'encyklopedia-scope-discovery/v3','scope_key':key,'scope_config':str(cfg_path),'root_semantics':scope_root_semantics(cfg),'root_count':len(roots),'entity_count':len(rows),'edge_count':len(edges),'role_counts':dict(sorted(role_counts.items())),'discovery_backend':backend_info,'generated_at':utc_now(),'semantics':'Discovery chooses entities only. Once admitted, complete raw Wikidata entity JSON is preserved in evidence. Root roles are scope policy, not universal ontology.'}
    save_json(outdir/'stats.json',stats); print(json.dumps(stats,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
