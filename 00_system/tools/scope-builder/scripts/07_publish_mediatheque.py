from __future__ import annotations
import argparse, gzip, json
from pathlib import Path
from scope_common import *

BIB_PROPS={
 'P31','P50','P170','P1476','P577','P407','P136','P921','P123','P629','P747','P144','P361',
 'P953','P856','P212','P957','P356','P1938','P724','P648','P675','P950','P268','P214'
}


def external_ids(obj:dict[str,Any])->dict[str,list[Any]]:
    out={}
    for pid,sts in (obj.get('claims') or {}).items():
        vals=[]
        for st in sts or []:
            sn=st.get('mainsnak') or {}
            if sn.get('datatype')!='external-id':continue
            dv=sn.get('datavalue') or {}
            if dv.get('type')=='string':vals.append(dv.get('value'))
        if vals:out[pid]=vals
    return out


def main():
    ap=argparse.ArgumentParser(description='Publish UCKK Mediatheque work candidates directly from lossless scope evidence. Project SQLite is not required.')
    ap.add_argument('--root',default=''); ap.add_argument('--scope',required=True)
    a=ap.parse_args(); root=find_root(a.root or None); _,cfg=load_scope_config(root,a.scope); key=cfg['scope_key']; wd=scope_workdir(root,key)
    latest=load_json(wd/'evidence.latest.json',{}) or {}; sid=latest.get('snapshot_id')
    if not sid:raise SystemExit('Evidence snapshot absent. Exécute 04_extract_evidence.py.')
    snap=scope_snapshot_dir(root,key,sid); evidence=snap/'entities.wikidata.jsonl.gz'; freeze=load_json(wd/'scope.freeze.json',{}) or {}; roles=freeze.get('entity_roles') or {}
    works={wid for wid,r in roles.items() if 'work' in set((r or {}).get('roles') or [])}
    # Backward compatibility with v1 freeze: derive roles from discovery if needed.
    if not works:
        works={r['wid'] for r in read_jsonl(wd/'discovery/entities.jsonl') if 'work' in set(r.get('roles') or [])}
    entity_hash={r['wid']:r.get('sha256') for r in read_jsonl(snap/'entities.manifest.jsonl')}; out=[]
    with gzip.open(evidence,'rt',encoding='utf-8') as f:
        for line in f:
            if not line.strip():continue
            obj=json_loads(line); wid=obj.get('id')
            if wid not in works:continue
            claims=obj.get('claims') or {}; bib={pid:claims[pid] for pid in claims if pid in BIB_PROPS}
            out.append({
                'schema_version':'encyklopedia-mediatheque-candidate/v3',
                'record_type':'work_or_document_candidate',
                'wid':wid,
                'labels':obj.get('labels') or {},
                'descriptions':obj.get('descriptions') or {},
                'aliases':obj.get('aliases') or {},
                'bibliographic_claims':bib,
                'external_identifiers':external_ids(obj),
                'sitelinks':obj.get('sitelinks') or {},
                'source_scope':key,
                'source_snapshot':sid,
                'source_entity_sha256':entity_hash.get(wid),
                'status':'candidate_from_lossless_wikidata_scope',
                'bibliographic_resolution':{
                    'work_identity':'candidate',
                    'edition_identity':'not_resolved',
                    'manifestation_or_file':'not_resolved',
                    'provider_access_rights':'not_resolved',
                },
                'note':'Candidate only. Work, edition and manifestation/file are not collapsed. UCKK Mediatheque remains authoritative for final edition, provider, access and rights resolution.'
            })
    out.sort(key=lambda r:r['wid']); dest=root/'50_mediatheque/catalog/candidates/wikidata'/key; dest.mkdir(parents=True,exist_ok=True); f=dest/f'{sid}.works.jsonl'; write_jsonl(f,out)
    man={'schema_version':'encyklopedia-mediatheque-candidate-set/v3','scope_key':key,'snapshot_id':sid,'candidate_count':len(out),'work_count':len(out),'source':'lossless_evidence_direct','bibliographic_invariant':'work != edition != manifestation/file','project_index_required':False,'file':str(f.relative_to(root)).replace('\\','/'),'sha256':sha256_file(f),'generated_at':utc_now()}; save_json(dest/f'{sid}.manifest.json',man); save_json(dest/'latest.json',man); print(json.dumps(man,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
