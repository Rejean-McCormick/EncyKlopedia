from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path
from harvestlib import find_root


def main():
    ap=argparse.ArgumentParser(description='Resolve seed people to Wikidata QIDs using the existing local graph resolver.')
    ap.add_argument('--root',default=''); ap.add_argument('--db',default=''); ap.add_argument('--registry',default=''); ap.add_argument('--out',default='')
    a=ap.parse_args(); root=find_root(a.root or None)
    db=Path(a.db) if a.db else root/'30_working/wikidata/wikidata.compact.sqlite'
    reg=Path(a.registry) if a.registry else root/'10_sources/seeds/active/intellectual-registry/intellectuals.seed.json'
    out=Path(a.out) if a.out else root/'30_working/registry/qid-map.local.json'
    tool=root/'00_system/tools/wikidata-manager/scripts/local_graph.py'
    out.parent.mkdir(parents=True,exist_ok=True)
    cmd=[sys.executable,str(tool),'resolve','--db',str(db),'--registry',str(reg),'--out',str(out)]
    print('$ '+' '.join(cmd),flush=True)
    raise SystemExit(subprocess.call(cmd))

if __name__=='__main__': main()
