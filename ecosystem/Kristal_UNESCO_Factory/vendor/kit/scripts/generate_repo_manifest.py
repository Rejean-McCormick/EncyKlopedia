#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'validation/repo-manifest.sha256.json'
EXCLUDE={'validation/repo-manifest.sha256.json','validation/manifest.sha256.json'}
rows=[]
for p in sorted(ROOT.rglob('*'),key=lambda x:x.relative_to(ROOT).as_posix()):
    if not p.is_file():continue
    rel=p.relative_to(ROOT).as_posix()
    if rel in EXCLUDE or rel.endswith('.zip') or '__pycache__' in p.parts or '.git' in p.parts:continue
    b=p.read_bytes();rows.append({'path':rel,'sha256':hashlib.sha256(b).hexdigest(),'size':len(b)})
obj={'format':'kristal.local-kit-repo-manifest/3.2.0','algorithm':'sha256','kit_version':(ROOT/'VERSION').read_text().strip(),'files':rows}
OUT.parent.mkdir(exist_ok=True);OUT.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(f'Wrote {OUT} ({len(rows)} files)')
