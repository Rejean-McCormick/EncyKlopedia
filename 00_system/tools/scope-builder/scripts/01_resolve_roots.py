from __future__ import annotations
import argparse, json, time
from collections import defaultdict
from pathlib import Path
from scope_common import *


def finalize_candidates(cands:list[dict[str,Any]])->dict[str,Any]:
    cands=sorted(cands,key=lambda x:x.get('score',0),reverse=True)
    if not cands:return {'qid':None,'confidence':'unresolved','candidates':[]}
    top=cands[0]; gap=top['score']-(cands[1]['score'] if len(cands)>1 else 0)
    conf='high' if top['score']>=82 and gap>=6 else ('medium' if top['score']>=74 and gap>=3 else 'ambiguous')
    return {'qid':top['qid'] if conf!='ambiguous' else None,'confidence':conf,'score':top['score'],'candidates':cands[:10]}


def raw_resolve(root:Path,dump:Path,seeds:list[dict[str,Any]])->dict[str,dict[str,Any]]:
    by_norm=defaultdict(list)
    for seed in seeds:by_norm[normalize_name(seed.get('display_name'))].append(seed)
    wanted=set(by_norm); candidates=defaultdict(list); scanned=0; started=time.time(); last=started
    print(f'[resolve/raw] scan {dump.name} for {len(seeds)} unresolved name(s)',flush=True)
    for raw in iter_dump_raw(dump,root=root):
        scanned+=1
        # Cheap prefilter: if none of the ASCII-ish display names occur, we still need aliases/escaped names,
        # so this is only used when exact UTF-8 names are all absent and does not skip non-ASCII targets.
        try:obj=json_loads(raw)
        except Exception:continue
        names=entity_normalized_names(obj)
        hits=names & wanted
        if hits:
            for norm in hits:
                for seed in by_norm[norm]:candidates[seed['key']].append(score_raw_candidate(seed,obj))
        now=time.time()
        if now-last>60:
            print(f'[resolve/raw] scanned {scanned:,} | matched seed keys {len(candidates):,} | elapsed {(now-started)/3600:.2f}h',flush=True); last=now
    return {seed['key']:finalize_candidates(candidates.get(seed['key'],[])) for seed in seeds}


def main():
    ap=argparse.ArgumentParser(description='Resolve scope roots. Uses declared/cached QIDs first; then complete global index when available, otherwise the raw dump.')
    ap.add_argument('--root',default=''); ap.add_argument('--scope',required=True); ap.add_argument('--backend',choices=['auto','index','fast','raw'],default='auto'); ap.add_argument('--db',default=''); ap.add_argument('--dump',default='')
    a=ap.parse_args(); root=find_root(a.root or None); cfg_path,cfg=load_scope_config(root,a.scope); key=cfg['scope_key']; wd=scope_workdir(root,key); wd.mkdir(parents=True,exist_ok=True)
    reg_meta,records,reg_path=load_registry(root,cfg); cache=load_cached_qid_map(root); result={}; unresolved=[]
    # 1) Explicit QIDs and previously stabilized QID map need no scan at all.
    remaining=[]
    for seed in records:
        q=declared_qid(cfg,seed)
        source='declared'
        if not q:
            cv=cache.get(seed.get('key'))
            if isinstance(cv,str):q=cv
            elif isinstance(cv,dict):q=cv.get('qid')
            source='cached_qid_map'
        if q:
            result[seed['key']]={'display_name':seed.get('display_name'),'qid':q,'confidence':'explicit' if source=='declared' else 'cached','resolution_source':source,'candidates':[]}
        else:remaining.append(seed)
    db=Path(a.db) if a.db else default_global_db(root); dump=Path(a.dump) if a.dump else None; backend=choose_discovery_backend(root,a.backend,db,dump)
    backend_meta={'requested':a.backend,'selected':backend}
    # 2) Resolve remaining names using chosen backend.
    if remaining and backend=='index':
        c=open_db(db,True); meta=assert_global_index(c,True); backend_meta['global_index']=str(db); backend_meta['global_index_meta']=meta
        for i,seed in enumerate(remaining,1):
            r=resolve_seed(c,seed); result[seed['key']]={'display_name':seed.get('display_name'),**r,'resolution_source':'global_index'}
            print(f"[resolve/index] {i}/{len(remaining)} {seed.get('display_name')} -> {r.get('qid')} [{r.get('confidence')}]",flush=True)
        c.close()
    elif remaining:
        dump=dump or find_dump(root); desc=dump_descriptor(root,dump); backend_meta['dump']=desc; backend_meta['fast_runtime']=performance_status(root)
        rr=raw_resolve(root,dump,remaining)
        for i,seed in enumerate(remaining,1):
            r=rr[seed['key']]; result[seed['key']]={'display_name':seed.get('display_name'),**r,'resolution_source':'raw_dump'}
            print(f"[resolve/raw-result] {i}/{len(remaining)} {seed.get('display_name')} -> {r.get('qid')} [{r.get('confidence')}]",flush=True)
    for seed in records:
        r=result.get(seed['key'],{})
        if not r.get('qid'):unresolved.append({'key':seed.get('key'),'display_name':seed.get('display_name'),**r})
    out=wd/'roots.resolved.json'; save_json(out,result); write_jsonl(wd/'roots.unresolved.jsonl',unresolved)
    save_json(wd/'roots.manifest.json',{'schema_version':'encyklopedia-scope-roots/v3','scope_key':key,'scope_config':str(cfg_path),'root_registry':str(reg_path),'registry_key':reg_meta.get('registry_key'),'root_semantics':scope_root_semantics(cfg),'root_count':len(records),'resolved_count':len(records)-len(unresolved),'unresolved_count':len(unresolved),'backend':backend_meta,'generated_at':utc_now()})
    print(json.dumps({'scope_key':key,'resolved':len(records)-len(unresolved),'total':len(records),'backend':backend,'out':str(out)},ensure_ascii=False,indent=2))
    if unresolved and cfg.get('resolution',{}).get('require_all_roots',False):raise SystemExit(f'{len(unresolved)} racine(s) non résolue(s).')

if __name__=='__main__':main()
