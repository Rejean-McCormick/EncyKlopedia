"""Read-only, bounded, evidence-preserving acquisition of full Wikidata JSON entities.

Sources:
  * Skope snapshot-manifest directory (part-*.jsonl.gz)
  * an explicit small JSONL or JSONL.GZ set of entity records
  * an already indexed local dump using Skope fast-access sidecars.

Never scans an unindexed Wikidata dump. Never writes the compact SQLite index.
No Wiki claims are promoted into a Kristal canonical artifact.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import json
import re
import sqlite3

QID_RE = re.compile(r'^Q[1-9]\d*$')
DUMP_RE = re.compile(r'\.json(?:\.gz|\.bz2)?$', re.I)

class EvidenceUnavailable(Exception):
    pass


def fingerprint(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def determine_source(raw, index):
    """Discover but do not read local source; never recurse over a filesystem."""
    if raw and str(raw).strip():
        p=Path(raw).expanduser()
        if p.exists():return p.resolve()
        raise EvidenceUnavailable('Chemin des entités Wikidata introuvable : '+str(p))
    idx=Path(index or '')
    if not idx.is_file():raise EvidenceUnavailable('Aucun fichier de fiches complètes et aucun index EncyK local disponible.')
    root=idx.resolve().parent.parent.parent
    folder=root/'10_sources'/'wikidata'/'dumps'/'current'
    if not folder.is_dir():raise EvidenceUnavailable('Dump original absent dans '+str(folder))
    sources=sorted(p for p in folder.iterdir() if p.is_file() and DUMP_RE.search(p.name))
    if len(sources)!=1:
        raise EvidenceUnavailable('La source n’est pas unique ('+str(len(sources))+') : sélectionner un dump explicitement dans l’interface.')
    return sources[0]


def _safe_entry(raw):
    if isinstance(raw, bytes):raw=raw.decode('utf-8-sig')
    raw=raw.strip().removeprefix('[').removesuffix(']').removesuffix(',').strip()
    if not raw:return None
    v=json.loads(raw)
    return v if isinstance(v,dict) and QID_RE.fullmatch(str(v.get('id',''))) else None


def _iter_jsonl(path, wanted, cancel):
    """Only accept explicitly extracted snapshots, never the giant full JSONL dump."""
    path=Path(path)
    if path.stat().st_size>2_000_000_000:
        raise EvidenceUnavailable('Fichier sans localisateur trop gros (>2 Go) ; sélectionner le dump indexé ou les parts Skope.')
    op=gzip.open if path.name.lower().endswith('.gz') else open
    with op(path,'rt',encoding='utf-8-sig') as f:
        for row in f:
            if cancel():raise InterruptedError('Extraction interrompue')
            if not row.strip():continue
            entity=_safe_entry(row)
            if entity and entity['id'] in wanted:yield entity


def _iter_skope_directory(folder,wanted,cancel):
    manifest=json.loads((folder/'snapshot-manifest.json').read_text(encoding='utf-8'))
    files=manifest.get('parts',[])
    if not isinstance(files,list):raise EvidenceUnavailable('Manifeste Skope invalide')
    for part in files:
        filename=part.get('file','') if isinstance(part,dict) else ''
        if not re.fullmatch(r'part-\d+\.jsonl\.gz',filename):
            raise EvidenceUnavailable('Nom de bloc Skope invalide : '+repr(filename))
        yield from _iter_jsonl(folder/filename,wanted,cancel)


def _iter_indexed_dump(path,index,wanted,cancel):
    from vendor.wikidata_skope import scope_common
    if not index or not Path(index).is_file():
        raise EvidenceUnavailable('Index compact EncyK absent : nécessaire à la localisation du dump.')
    root=scope_common.fast_access_status # same file bundled from original Skope
    data_root=Path(index).resolve().parent.parent.parent
    if not path.is_relative_to(data_root):
        raise EvidenceUnavailable('Dump en dehors du volume EncyK : accès Skope refusé.')
    status,detail=root(data_root,path)
    if not status or not detail.get('random_access_ready'):
        raise EvidenceUnavailable('Localisateur Skope ou lecteur compressé absent (rapidgzip/indexed_bzip2). '+str(detail.get('runtime_backend')))
    qids=sorted(wanted,key=lambda q:int(q[1:]))
    for start in range(0,len(qids),150):
        if cancel():raise InterruptedError('Extraction interrompue')
        batch=qids[start:start+150]
        raw_map=scope_common.fast_fetch_raw(data_root,path,batch,threads=4)
        for qid,raw in raw_map.items():
            item=_safe_entry(raw)
            if item and item['id']==qid:yield item


def iter_entities(source,index,wanted,cancel):
    source=Path(source)
    if source.is_dir():
        if not (source/'snapshot-manifest.json').is_file():
            raise EvidenceUnavailable('Dossier sans snapshot-manifest.json (export Skope attendu).')
        yield from _iter_skope_directory(source,wanted,cancel)
    elif source.name.lower().endswith(('.jsonl','.jsonl.gz')):
        yield from _iter_jsonl(source,wanted,cancel)
    elif DUMP_RE.search(source.name):
        yield from _iter_indexed_dump(source,index,wanted,cancel)
    else:
        raise EvidenceUnavailable('Format non reconnu : utiliser JSONL(.gz), dossier Skope ou dump .json(.gz/.bz2) indexé.')


def _normalize_statement(stmt, prop):
    mainsnak=stmt.get('mainsnak') or {}
    # Preserve datavalue typed structure and all qualifiers/references (avoid reducing ontology to text).
    return {'statement_id':stmt.get('id'),'property':prop,'rank':stmt.get('rank'),
            'mainsnak':mainsnak,'qualifiers':stmt.get('qualifiers') or {},
            'qualifiers_order':stmt.get('qualifiers-order') or [],
            'references':stmt.get('references') or [],'type':stmt.get('type')}


def _brief_text(snak):
    snaktype=snak.get('snaktype')
    if snaktype=='novalue':return 'sans valeur'
    if snaktype=='somevalue':return 'valeur inconnue'
    value=(snak.get('datavalue') or {}).get('value')
    if isinstance(value,dict):
        if 'id' in value:return str(value['id'])
        if 'text' in value:return str(value['text'])[:130]
        if 'time' in value:return str(value['time'])
        if 'amount' in value:return str(value['amount'])+(' '+str(value['unit']) if value.get('unit') and value['unit']!='1' else '')
        if 'latitude' in value and 'longitude' in value:return f"{value['latitude']}, {value['longitude']}"
        return json.dumps(value,ensure_ascii=False,sort_keys=True)[:130]
    if value is None:return '?'
    return str(value)[:130]


def extract(mapping, source, index, out, cancel=lambda:False, progress=None, source_origin=None):
    """Return (manifest, summaries). All raw source entities preserved in gzip; no canon."""
    target={m['wikidata_qid_candidate']:cid for cid,m in mapping.items()
            if m.get('status')=='SINGLE_P3916_CANDIDATE' and QID_RE.fullmatch(m.get('wikidata_qid_candidate') or '')}
    if not target:raise EvidenceUnavailable('Aucun QID P3916 unique : extraction ciblée impossible.')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    source=determine_source(source,index)
    origin=Path(source_origin).resolve() if source_origin else source
    seen={};property_tally=Counter();statements=0;refs=0;qualifiers=0;duplicates=0
    rawpath=out/'raw_entities.jsonl.gz'
    normalizedpath=out/'facts.jsonl'
    with gzip.open(rawpath,'wt',encoding='utf-8',compresslevel=6) as raw_out, normalizedpath.open('w',encoding='utf-8') as normalized:
        for entity in iter_entities(source,index,set(target),cancel):
            qid=entity['id']
            if qid in seen:
                duplicates+=1
                continue
            cid=target[qid]
            if len(json.dumps(entity,ensure_ascii=False))>25_000_000:
                # A single source entity larger than 25 MB is unsafe to inline; reject rather than silently truncate.
                raise EvidenceUnavailable('Entité Wikidata trop grande (>25 Mo) : '+qid)
            raw_out.write(json.dumps(entity,ensure_ascii=False,separators=(',',':'))+'\n')
            claims=entity.get('claims') or {}
            clean={}
            for pid,vals in claims.items():
                if not re.fullmatch('P[1-9][0-9]*',pid) or not isinstance(vals,list):continue
                clean[pid]=[_normalize_statement(st,pid) for st in vals if isinstance(st,dict)]
                statements+=len(clean[pid]);property_tally[pid]+=len(clean[pid])
                for s in clean[pid]:
                    refs+=len(s['references']);qualifiers+=sum(len(x) for x in s['qualifiers'].values() if isinstance(x,list))
            item={'format':'kristal.wikidata-evidence/1.0','unesco_id':cid,'qid':qid,'source_status':'read_only_external_not_reviewed',
                  'source_path':str(origin),'source_entity_sha256':hashlib.sha256(json.dumps(entity,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),
                  'labels':entity.get('labels') or {},'descriptions':entity.get('descriptions') or {},
                  'claims':clean,'statement_count':sum(map(len,clean.values()))}
            normalized.write(json.dumps(item,ensure_ascii=False)+'\n')
            seen[qid]={'qid':qid,'unesco_id':cid,'statement_count':item['statement_count'],'preview':fact_preview(item,10)}
            if progress and (len(seen)==1 or len(seen)%200==0):progress(len(seen),len(target))
    missing=sorted(set(target)-set(seen),key=lambda q:int(q[1:]))
    manifest={'format':'kristal.wikidata-full-source-report/1.0','created_at_utc':datetime.now(timezone.utc).isoformat(),
              'source_path':str(origin),'source_kind':('indexed_dump_via_private_reader' if source_origin else ('indexed_dump' if DUMP_RE.search(source.name) else 'extracted_snapshot')),
              'reader_snapshot':str(source) if source_origin else None,
              'requested_unique_qids':len(target),'entities_found':len(seen),'missing_qids':missing,
              'duplicate_entities_ignored':duplicates,'statement_count':statements,'reference_groups':refs,
              'qualifier_snaks':qualifiers,'property_statement_counts':dict(property_tally.most_common()),
              'canonical_write':False,'reviewed':False,'full_raw_records_file':rawpath.name,
              'raw_records_sha256':fingerprint(rawpath),'facts_file':normalizedpath.name,'facts_sha256':fingerprint(normalizedpath),
              'coverage_complete':not missing and len(seen)==len(target)}
    (out/'manifest_full.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return manifest,{target[qid]:entry for qid,entry in seen.items()}


def fact_preview(entity,limit=7):
    """Strict lexically transparent preview: only PID, original value, rank, #references."""
    if not entity:return []
    if 'preview' in entity:return entity['preview'][:limit]
    arr=[]
    for pid,statements in sorted(entity['claims'].items(),key=lambda x:int(x[0][1:])):
        for s in statements:
            if len(arr)>=limit:return arr
            value=_brief_text(s['mainsnak']);ref_ct=len(s.get('references') or [])
            arr.append(f"{pid} = {value} [rang: {s.get('rank') or '?'}; groupes de références: {ref_ct}]")
    return arr
