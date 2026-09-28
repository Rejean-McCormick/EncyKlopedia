from __future__ import annotations
import argparse, importlib.util, json, subprocess, sys


def installed(name): return importlib.util.find_spec(name) is not None

def main():
    ap=argparse.ArgumentParser(description='Install optional EncyKlopedia performance dependencies into the current Python environment.'); ap.add_argument('--root',default='')
    ap.add_argument('--try-bzip2',action='store_true',help='Also attempt indexed_bzip2. On CPython 3.14 Windows a wheel may not be available.')
    ap.add_argument('--dry-run',action='store_true'); a=ap.parse_args()
    packages=[]
    if not installed('orjson'): packages.append('orjson>=3.12,<4')
    if not installed('rapidgzip'): packages.append('rapidgzip>=0.16,<1')
    bzip_note=None
    if a.try_bzip2 and not installed('indexed_bzip2'):
        if sys.version_info >= (3,14) and sys.platform.startswith('win'):
            bzip_note='indexed_bzip2 skipped by default on Windows CPython 3.14 because the current indexed_bzip2 release may not provide a CPython 3.14 Windows wheel; use Python 3.13 or a local C++ build if desired.'
        else: packages.append('indexed_bzip2>=1.7,<2')
    cmd=[sys.executable,'-m','pip','install','--upgrade',*packages]
    report={'python':sys.version,'packages':packages,'command':cmd,'bzip2_note':bzip_note,'dry_run':a.dry_run}
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    if packages and not a.dry_run: raise SystemExit(subprocess.call(cmd))
if __name__=='__main__':main()
