#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,stat,zipfile
ROOT=Path(__file__).resolve().parents[1]
VERSION=(ROOT/'VERSION').read_text().strip()
FIXED=(2026,10,7,0,0,0)
EXCLUDED={'.git','__pycache__','.pytest_cache'}

def files():
    for p in sorted(ROOT.rglob('*'),key=lambda x:x.relative_to(ROOT).as_posix()):
        if not p.is_file() or any(part in EXCLUDED for part in p.parts) or p.suffix=='.pyc' or p.suffix=='.zip':continue
        yield p,p.relative_to(ROOT).as_posix()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',nargs='?',default=str(ROOT.parent/f'Kristal-Authoring-Kit-{VERSION}.zip'));args=ap.parse_args();out=Path(args.output).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    prefix=f'Kristal-Authoring-Kit-{VERSION}'
    with zipfile.ZipFile(out,'w') as z:
        for p,rel in files():
            zi=zipfile.ZipInfo(f'{prefix}/{rel}',FIXED);zi.create_system=3;zi.external_attr=(stat.S_IFREG|(0o755 if p.suffix=='.py' else 0o644))<<16;zi.compress_type=zipfile.ZIP_DEFLATED;z.writestr(zi,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    print(f'{hashlib.sha256(out.read_bytes()).hexdigest()}  {out.name}')
if __name__=='__main__':main()
