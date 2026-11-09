#!/usr/bin/env python3
"""Verify only installed v20 runtime additions, using a co-located manifest.

The manifest is NOT sought at C:\\mycode\\MANIFEST.json. No root-level README
is a runtime dependency. No installation, database access or side effect.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys


def main():
    try:
        this=Path(__file__).resolve()
        root=this.parents[4]
        manifest=this.with_name('MANIFEST_OVERLAY_UNESCO_EXTRACTION_V20.json')
        obj=json.loads(manifest.read_text(encoding='utf-8'))
        if obj.get('format')!='koa.unesco-wikipedia-multistream-overlay/1.0':
            raise ValueError('Format de manifeste V20 non reconnu')
        problems=[]
        for name,entry in obj['files'].items():
            candidate=(root/name).resolve()
            if not candidate.is_relative_to(root):
                problems.append(name+': chemin hors de C:\\mycode');continue
            if not candidate.is_file():
                problems.append(name+': absent');continue
            blob=candidate.read_bytes()
            if len(blob)!=entry['bytes'] or hashlib.sha256(blob).hexdigest()!=entry['sha256']:
                problems.append(name+': empreinte non conforme')
        result={'status':'OVERLAY_UNESCO_EXTRACTION_V20_VALID' if not problems else 'OVERLAY_V20_INTEGRITY_FAILED',
                'files_checked':len(obj['files']),'root':str(root),'manifest':str(manifest),
                'problems':problems}
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if not problems else 2
    except (OSError,ValueError,KeyError) as exc:
        print(json.dumps({'status':'OVERLAY_V20_INTEGRITY_FAILED','error':str(exc)},ensure_ascii=False))
        return 2

if __name__=='__main__':sys.exit(main())
