from __future__ import annotations
import argparse, gzip, json, re
from pathlib import Path
from scope_common import *

ROLE_KIND = {
    'person_root':'person',
    'person':'person',
    'work':'work',
    'place':'place',
    'country':'place',
    'institution':'collective',
    'institution_or_group':'collective',
    'field':'concept',
    'occupation':'concept',
    'worldview':'concept',
    'movement':'concept',
    'intellectual_context':'concept',
    'work_context':'other',
    'place_or_institution_context':'other',
    'person_neighbor':'other',
    'root_neighbor':'other',
    'person_or_influence':'other',
}

EXTERNAL_ID_SYSTEMS = {
    'P214':'viaf',
    'P1938':'project-gutenberg-author',
    'P648':'openlibrary',
    'P268':'bnf',
    'P950':'bne',
    'P212':'isbn13',
    'P957':'isbn10',
    'P356':'doi',
}


def labels(obj:dict[str,Any])->list[dict[str,str]]:
    out=[]
    for lang,val in (obj.get('labels') or {}).items():
        if isinstance(val,dict) and val.get('value'):
            rec={'text':str(val['value'])}
            if re.fullmatch(r'^[a-zA-Z]{2,3}(-[a-zA-Z0-9]{2,8})*$',str(lang)):rec['lang']=str(lang)
            out.append(rec)
    return out or [{'text':str(obj.get('id') or 'unknown'),'lang':'en'}]


def description(obj:dict[str,Any])->str|None:
    desc=obj.get('descriptions') or {}
    for lang in ('fr','en','mul'):
        val=desc.get(lang)
        if isinstance(val,dict) and val.get('value'):return str(val['value'])
    for val in desc.values():
        if isinstance(val,dict) and val.get('value'):return str(val['value'])
    return None


def source_external_ids(obj:dict[str,Any])->list[dict[str,str]]:
    out=[]
    wid=obj.get('id')
    if wid:out.append({'system':'wikidata','id':wid,'url':f'https://www.wikidata.org/wiki/{wid}'})
    claims=obj.get('claims') or {}
    for pid,system in EXTERNAL_ID_SYSTEMS.items():
        for st in claims.get(pid,[]) or []:
            sn=st.get('mainsnak') or {}; dv=sn.get('datavalue') or {}
            if dv.get('type')=='string' and isinstance(dv.get('value'),str):
                out.append({'system':system,'id':dv['value']})
    seen=set(); dedup=[]
    for x in out:
        key=(x['system'],x['id'])
        if key not in seen:seen.add(key); dedup.append(x)
    return dedup


def infer_kind(cfg:dict[str,Any],roles:list[str])->str:
    sem=scope_root_semantics(cfg)
    if sem['role'] in roles:return sem['kind']
    overrides=((cfg.get('referents') or {}).get('role_kind_overrides') or {})
    for role in roles:
        kind=overrides.get(role) or ROLE_KIND.get(role)
        if kind in KRISTAL_REFERENT_KINDS:return kind
    return 'other'


def main():
    ap=argparse.ArgumentParser(description='Publish a candidate Kristal Referent Registry from one frozen EncyKlopedia scope.')
    ap.add_argument('--root',default=''); ap.add_argument('--scope',required=True)
    a=ap.parse_args(); root=find_root(a.root or None); _,cfg=load_scope_config(root,a.scope); key=cfg['scope_key']; wd=scope_workdir(root,key)

    latest=load_json(wd/'evidence.latest.json',{}) or {}; sid=latest.get('snapshot_id')
    if not sid:raise SystemExit('Evidence snapshot absent.')
    freeze=load_json(wd/'scope.freeze.json',{}) or {}; roles=freeze.get('entity_roles') or {}
    snap=scope_snapshot_dir(root,key,sid); evidence=snap/'entities.wikidata.jsonl.gz'
    if not evidence.exists():raise FileNotFoundError(evidence)

    refs=[]
    with gzip.open(evidence,'rt',encoding='utf-8') as f:
        for line in f:
            if not line.strip():continue
            obj=json_loads(line); wid=obj.get('id')
            rs=sorted(set((roles.get(wid) or {}).get('roles') or []))
            rec={
                'ref':f'wikidata:{wid}',
                'kind':infer_kind(cfg,rs),
                'labels':labels(obj),
                'external_ids':source_external_ids(obj),
                'classifications':rs,
                'attributes':{
                    'source_scope':key,
                    'source_snapshot':sid,
                    'candidate_identity':True,
                },
            }
            d=description(obj)
            if d:rec['description']=d
            refs.append(rec)
    refs.sort(key=lambda x:x['ref'])

    payload={
        'schema_version':'5.0',
        'artifact_type':'referent_registry',
        'profile_version':'1.0.0',
        'registry_id':'',
        'scope':{'domain':key},
        'referents':refs,
        'external_sources':[{'system':'wikidata','id':sid}],
        'extensions':{
            'authority':'candidate_only',
            'source_snapshot':sid,
            'ref_semantics':'Source-qualified candidate refs; Da’at/Kristal owns canonical mapping/acceptance.',
            'root_semantics':scope_root_semantics(cfg),
        },
    }
    canon=json.dumps({k:v for k,v in payload.items() if k!='registry_id'},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    payload['registry_id']='sha256:'+sha256_bytes(canon)

    outdir=root/'20_ingest/referent-registries'/key; outdir.mkdir(parents=True,exist_ok=True)
    out=outdir/f'{sid}.referents.json'; save_json(out,payload)
    save_json(outdir/'latest.json',{
        'snapshot_id':sid,
        'path':str(out.relative_to(root)).replace('\\','/'),
        'registry_id':payload['registry_id'],
        'sha256':'sha256:'+sha256_file(out),
        'referent_count':len(refs),
    })
    print(json.dumps({'scope_key':key,'referents':len(refs),'out':str(out),'registry_id':payload['registry_id']},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
