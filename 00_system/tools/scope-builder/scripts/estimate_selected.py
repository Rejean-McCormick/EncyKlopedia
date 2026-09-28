from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path
from scope_common import find_root

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default=''); ap.add_argument('--scope',action='append',required=True); a=ap.parse_args(); root=find_root(a.root or None); script=Path(__file__).resolve().parent/'03_estimate.py'
    for s in a.scope:
        print(f'\n=== {s} ===',flush=True)
        rc=subprocess.call([sys.executable,str(script),'--root',str(root),'--scope',s])
        if rc: raise SystemExit(rc)
if __name__=='__main__': main()
