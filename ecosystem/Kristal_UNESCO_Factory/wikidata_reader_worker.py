"""Isolated indexed-bzip2 worker. Can run under CPython 3.11/3.12/3.13.

Only opens existing Skope index + compressed dump read-only; no full dump scan.
Emits a bounded JSONL.GZ with Wikidata entity records, strictly QID-checked.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
from vendor.wikidata_skope import scope_common, fastio


def run(source, idx, request, out):
    source=Path(source).resolve();idx=Path(idx).resolve();out=Path(out)
    if not source.is_file() or not idx.is_file():raise ValueError('Source ou index absent')
    root=idx.parent.parent.parent
    if not source.is_relative_to(root):raise ValueError('Source hors du volume EncyK')
    wanted=json.loads(Path(request).read_text(encoding='utf-8'))['qids']
    wanted={q for q in wanted if isinstance(q,str) and re.fullmatch(r'Q[1-9][0-9]*',q)}
    ok,info=scope_common.fast_access_status(root,source)
    if not ok:raise ValueError('Localisateur qid-locator.bin absent')
    if not info['random_access_ready']:raise ValueError('Accès aléatoire BZIP2 et/ou index bzip2 incomplet')
    locator=Path(info['locator_path']);compression=Path(info['compression_index_path'])
    if not locator.is_file() or not compression.is_file():raise ValueError('Index locateur ou index de compression absent')
    rows=[];unlocated=[]
    with fastio.DenseQidLocatorReader(locator) as loc:
        for q in wanted:
            rec=loc.get(int(q[1:]))
            if rec:rows.append((rec[0],rec[1],q))
            else:unlocated.append(q)
    rows.sort()
    out.parent.mkdir(parents=True,exist_ok=True)
    valid=0;rejected=[]
    with fastio.DumpStream(source,index_path=compression,root=root,threads=4) as stream, gzip.open(out,'wt',encoding='utf-8',compresslevel=6) as f:
        if not stream.random_access or (source.suffix.lower() in ('.bz2','.gz') and not stream._index_loaded):
            raise ValueError('Index compression.bz2blocks.pkl non importé : interruption sans lecture séquentielle')
        for offset,length,qid in rows:
            if length<=0 or length>25_000_000:
                rejected.append({'qid':qid,'reason':'invalid-length','length':length});continue
            try:
                stream.seek(offset)
                raw=fastio.normalize_dump_line(stream.read(length))
                if not raw:raise ValueError('empty line')
                obj=json.loads(raw)
                if not isinstance(obj,dict) or obj.get('id')!=qid:raise ValueError('qid/locator mismatch')
                f.write(json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n')
                valid+=1
            except (OSError,ValueError,json.JSONDecodeError) as e:
                rejected.append({'qid':qid,'reason':type(e).__name__+': '+str(e)[:150]})
            if valid and valid%200==0:print(f'Lecteur aléatoire : {valid}/{len(wanted)} entités',flush=True)
    with out.open('rb') as f:
        h=hashlib.file_digest(f,'sha256').hexdigest()
    manifest={'format':'kristal.wikidata-indexed-reader/1.0','source_dump':str(source),
              'index_locator':str(locator),'compression_index':str(compression),
              'backend':info['runtime_backend'],'requested':len(wanted),
              'located':len(rows),'found':valid,'unlocated_qids':sorted(unlocated),
              'rejected':rejected,'sha256':h,'path':str(out),'source_modified':False,'scan_entire_dump':False}
    meta=out.with_suffix(out.suffix+'.reader.json')
    meta.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Lecteur terminé : '+str(valid)+' entités ; '+str(len(rejected))+' enregistrements rejetés',flush=True)
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--dump',required=True);p.add_argument('--index',required=True)
    p.add_argument('--request',required=True);p.add_argument('--out',required=True)
    x=p.parse_args()
    try:run(x.dump,x.index,x.request,x.out)
    except Exception as e:
        print('ERREUR LECTEUR : '+str(e),file=sys.stderr,flush=True)
        sys.exit(2)
