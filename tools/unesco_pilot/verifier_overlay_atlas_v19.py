#!/usr/bin/env python3
"""Verify additive v19 overlay bytes without changing any repository."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

MANIFEST='MANIFEST_OVERLAY_UNESCO_ATLAS_V19_20261109.json'

def main(argv=None):
    root=Path(argv[0] if argv else Path(__file__).resolve().parents[4])
    path=root/MANIFEST
    try:
        m=json.loads(path.read_text(encoding='utf-8'))
        failed=[]
        for relative,expected in m['files'].items():
            p=root/relative
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected['sha256']:
                failed.append(relative)
        result={'status':'OVERLAY_UNESCO_ATLAS_V19_VALID' if not failed else 'OVERLAY_INTEGRITY_FAILED',
                'files_checked':len(m['files']),'problems':failed,'root':str(root)}
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if not failed else 2
    except (OSError,ValueError,KeyError) as exc:
        print(json.dumps({'status':'OVERLAY_INTEGRITY_FAILED','error':str(exc)},ensure_ascii=False))
        return 2

if __name__=='__main__':sys.exit(main(sys.argv[1:]))
