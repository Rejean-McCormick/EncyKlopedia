"""Extract ONLY explicitly inventoried enwiki article text from local multistream XML.bz2.

Research evidence, not canonical Kristal assertions or authorization to publish.
No HTTP, GitHub, translation, or writes to any input/index. Streaming parse,
no decompressed whole-dump copy. Even after extraction, wikitext is not a
validated fact, source quotation, or copyright clearance.
"""
from __future__ import annotations
import argparse
import bz2
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import xml.etree.ElementTree as ET

PROFILE='encyklopedia.unesco-enwiki-text-evidence/1.0'
SOURCE_PROFILE='encyklopedia.unesco-local-wikipedia-handoff/1.0'
MAX_ENTRY_BYTES=16*1024*1024

class EvidenceError(ValueError): pass


def _local_name(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]


def _direct(node, name):
    for child in node:
        if _local_name(child.tag)==name:
            return child
    return None


def _text(node, name):
    el=_direct(node,name)
    return el.text if el is not None else None


def _sha(content: bytes):
    return hashlib.sha256(content).hexdigest()


def read_inventory(path: Path):
    if not path.is_file() or path.stat().st_size > 5_000_000:
        raise EvidenceError('Private inventory absent or too large')
    blob=path.read_bytes(); d=json.loads(blob)
    if d.get('profile')!=SOURCE_PROFILE or d.get('branch')!='unesco-mt1-10':
        raise EvidenceError('Wrong source profile/branch')
    if not(d.get('not_canonical') is True and d.get('not_publication') is True and
           d.get('approval_status')=='BLOCKED' and d.get('wiki_content_extracted') is False):
        raise EvidenceError('Input must be the untouched Lot 1 private inventory')
    rec=d.get('records')
    if not isinstance(rec,list) or len(rec)!=41:
        raise EvidenceError('Expected 41 source concept records')
    ids={}; seen=set()
    for r in rec:
        cid=r.get('unesco_id')
        if not isinstance(cid,str) or cid in seen: raise EvidenceError('Invalid concept identities')
        seen.add(cid)
        for page in r.get('wikipedia_en_inventory',[]):
            if page.get('redirect') is True: continue
            pid=page.get('page_id')
            if type(pid) is not int or pid<1: raise EvidenceError('Malformed page id')
            ids.setdefault(pid,[]).append({'unesco_id':cid, 'qid_candidate':r['wikidata']['qid'],
                                            'title_inventory':page.get('title'),
                                            'revision_inventory':page.get('latest_revision_id')})
    if not ids: raise EvidenceError('No nonredirect Wikipedia EN page IDs in local inventory')
    return ids,_sha(blob)


def _safe_dir(out:Path, inputs):
    out=out.resolve()
    if out.exists() or out.is_symlink():raise EvidenceError('Output must be a NEW folder')
    for inp in inputs:
        if out==inp.resolve() or inp.resolve().is_relative_to(out):
            raise EvidenceError('Output may not contain an input')
    for a in (out.parent,*out.parents):
        if (a/'.git').exists():raise EvidenceError('Private output under a Git checkout refused')
        if a.is_symlink():raise EvidenceError('Symlinked output parent refused')
    if not out.parent.is_dir():raise EvidenceError('Output parent must exist')
    return out


def _parse_page(page, targets):
    try: pid=int(_text(page,'id') or '0')
    except ValueError:return None
    if pid not in targets or _text(page,'ns')!='0':return None
    revision=_direct(page,'revision')
    if revision is None:return None
    raw=_text(revision,'text')
    if raw is None:return None
    blob=raw.encode('utf-8')
    if len(blob)>MAX_ENTRY_BYTES:
        return {'page_id':pid,'oversized':True,'bytes':len(blob)}
    title=_text(page,'title')
    return {'page_id':pid,'title':title,'revision_id':_text(revision,'id'),
            'revision_timestamp':_text(revision,'timestamp'),'bytes':len(blob),
            'sha256':_sha(blob),'wikitext':blob}


def extract(inventory:Path,xml_bz2:Path,out:Path,*,progress_every=1_000_000):
    targets,inventory_sha=read_inventory(inventory)
    if not xml_bz2.is_file() or not xml_bz2.name.endswith('.xml.bz2'):
        raise EvidenceError('Expected existing local .xml.bz2 dump')
    out=_safe_dir(out,(inventory,xml_bz2))
    os.mkdir(out)
    completed={}; count=0; root=None
    try:
        try:
            with bz2.open(xml_bz2,'rb') as stream:
                for event,node in ET.iterparse(stream,events=('start','end')):
                    if event=='start' and root is None:
                        root=node
                    if event=='end' and _local_name(node.tag)=='page':
                        count+=1
                        r=_parse_page(node,targets)
                        if r is not None:
                            pid=r['page_id']
                            if pid in completed: raise EvidenceError('Repeated page ID in XML')
                            payload=r.pop('wikitext',None)
                            r['concept_matches']=targets[pid]
                            if payload is not None:
                                filename=f'page-{pid}.wikitext.txt'
                                with (out/filename).open('xb') as f:
                                    f.write(payload); f.flush(); os.fsync(f.fileno())
                                r['relative_path']=filename
                                r['inventory_revision_agrees']=all(
                                  str(x['revision_inventory'])==str(r['revision_id']) for x in targets[pid]
                                  if x['revision_inventory'] is not None)
                                r['inventory_title_agrees']=all(
                                  str(x['title_inventory']).replace('_',' ')==str(r['title']).replace('_',' ')
                                  for x in targets[pid])
                            completed[pid]=r
                        # Clearing root each page prevents accumulation of 66m empty
                        # nodes under the XML document root.
                        if root is not None: root.clear()
                        if progress_every and count%progress_every==0:
                            print(json.dumps({'event':'scan_progress','pages_scanned':count,
                                              'pages_extracted':sum('relative_path' in x for x in completed.values())}),flush=True)
        except (OSError,EOFError,ET.ParseError) as exc:
            raise EvidenceError(f'Local XML/bzip2 stream unreadable or truncated: {exc}') from exc
        data={'profile':PROFILE,'branch':'unesco-mt1-10','source':'local_enwiki_xml_bz2',
              'source_file_name':xml_bz2.name,'source_bytes':xml_bz2.stat().st_size,
              'source_mtime_ns':xml_bz2.stat().st_mtime_ns,'private':True,'not_canonical':True,
              'public_upload_authorized':False,'wikimedia_attribution_required':True,
              'licenses_not_cleared':True,'source_inventory_sha256':inventory_sha,
              'target_page_ids':sorted(targets),'pages_scanned':count,
              'found_pages':len(completed),'extracted_pages':sum('relative_path' in x for x in completed.values()),
              'missing_page_ids':sorted(set(targets)-set(completed)),
              'pages':[completed[x] for x in sorted(completed)]}
        with (out/'manifest.json').open('x',encoding='utf-8') as f:
            json.dump(data,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
        return data
    except Exception:
        # Preserve partial private text files for investigation, but mark NOT COMPLETE.
        (out/'INCOMPLETE.txt').write_text('Extraction failed. No completed manifest. Do not publish these files.\n',encoding='utf8')
        raise


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inventory',required=True,type=Path)
    p.add_argument('--xml',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--progress-every',type=int,default=1_000_000)
    a=p.parse_args(argv)
    try:
        r=extract(a.inventory,a.xml,a.out,progress_every=a.progress_every)
        print(json.dumps({'status':'PRIVATE_EVIDENCE_ONLY','extracted_pages':r['extracted_pages'],
                          'missing_page_ids':len(r['missing_page_ids']),'pages_scanned':r['pages_scanned'],
                          'out':str(a.out)},ensure_ascii=False));return 0
    except (EvidenceError,ValueError,KeyError,TypeError,FileExistsError) as e:
        print(json.dumps({'status':'BLOCKED','error':str(e)},ensure_ascii=False),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
