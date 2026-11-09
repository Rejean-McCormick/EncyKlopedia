#!/usr/bin/env python3
"""Fail-closed verification of the v21 additive overlay via colocated manifest."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

FMT='koa.unesco-wikipedia-direct-xml-overlay/1.0'

def verify(root=None,manifest=None):
    this=Path(__file__).resolve()
    root=Path(root).resolve() if root else this.parents[4]
    manifest=Path(manifest) if manifest else this.with_name('MANIFEST_OVERLAY_WIKIPEDIA_ENTREPOT_V21.json')
    data=json.loads(manifest.read_text(encoding='utf-8'))
    if data.get('format')!=FMT:raise ValueError('Manifeste v21 non reconnu')
    problems=[]
    for name,entry in sorted(data['files'].items()):
        dest=(root/name).resolve()
        if not dest.is_relative_to(root):
            problems.append(name+': hors racine');continue
        if not dest.is_file():
            problems.append(name+': absent');continue
        blob=dest.read_bytes()
        if len(blob)!=entry['bytes'] or hashlib.sha256(blob).hexdigest()!=entry['sha256']:
            problems.append(name+': empreinte incorrecte')
    return {'status':'OVERLAY_WIKIPEDIA_ENTREPOT_V21_VALID' if not problems else 'OVERLAY_V21_INTEGRITY_FAILED',
            'files_checked':len(data['files']),'problems':problems,
            'manifest':str(manifest),'root':str(root)}

def main():
    try:
        data=verify()
        print(json.dumps(data,ensure_ascii=False,indent=2))
        return 0 if not data['problems'] else 2
    except (OSError,ValueError,KeyError) as exc:
        print(json.dumps({'status':'OVERLAY_V21_INTEGRITY_FAILED','error':str(exc)},ensure_ascii=False))
        return 2

if __name__=='__main__':sys.exit(main())
