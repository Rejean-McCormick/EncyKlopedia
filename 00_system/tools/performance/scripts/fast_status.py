from __future__ import annotations
import argparse, json, sys
from pathlib import Path

HERE=Path(__file__).resolve(); ROOT0=HERE.parents[4]; LIB=ROOT0/'00_system/lib'
if str(LIB) not in sys.path: sys.path.insert(0,str(LIB))
import encyklopedia_fast as fastio


def find_root(start=''):
    p=Path(start).resolve() if start else ROOT0
    for c in [p,*p.parents]:
        if (c/'MANIFEST.json').exists(): return c
    return p


def find_dump(root:Path):
    d=root/'10_sources/wikidata/dumps/current'
    xs=[]
    for pat in ('*.json.gz','*.json.bz2','*.json'): xs.extend(d.glob(pat)) if d.exists() else None
    return max(xs,key=lambda p:p.stat().st_mtime) if xs else None


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default=''); a=ap.parse_args(); root=find_root(a.root)
    dump=find_dump(root); out={'schema_version':'encyklopedia-performance-status/v2','python':sys.version,'modules':fastio.module_status(root),'dump':None}
    if dump:
        out['dump']={'path':str(dump),'bytes':dump.stat().st_size,**fastio.backend_capabilities(dump,root)}
    out['recommendation']='Use .json.gz + rapidgzip for new dumps. Production full scans require explicit opt-in in v0.10; .bz2 random access requires indexed_bzip2.'
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
