#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from common import load_json, sha1_file


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--snapshot',required=True); ap.add_argument('--file',required=True); ap.add_argument('--write-marker',default='')
    a=ap.parse_args(); s=load_json(a.snapshot); p=Path(a.file)
    if not p.exists(): raise SystemExit(f"absent: {p}")
    got=sha1_file(p); expected=(s.get('sha1') or '').lower(); ok=bool(expected) and got==expected
    result={"file":str(p),"bytes":p.stat().st_size,"sha1":got,"expected_sha1":expected or None,"verified":ok if expected else None}
    print(json.dumps(result,indent=2))
    if a.write_marker:
        Path(a.write_marker).write_text(json.dumps(result,indent=2)+"\n",encoding='utf-8')
    if expected and not ok: raise SystemExit(2)

if __name__=='__main__': main()
