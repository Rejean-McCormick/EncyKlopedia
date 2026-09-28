from __future__ import annotations
import re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
pat=re.compile(r'\[[^\]]+\]\(([^)]+)\)')
missing=[]
for p in ROOT.rglob('*.md'):
    for link in pat.findall(p.read_text(encoding='utf-8')):
        if '://' in link or link.startswith('#') or link.startswith('mailto:'): continue
        target=link.split('#',1)[0]
        if target and not (p.parent/target).resolve().exists(): missing.append((p.relative_to(ROOT),link))
if missing:
    for p,l in missing: print(f'{p}: missing {l}')
    sys.exit(1)
print(f'markdown links: PASS ({len(list(ROOT.rglob("*.md")))} files)')
