#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,shutil,subprocess,sys,os
from pathlib import Path
from common import human_bytes
from discover_dump import discover

def run(cmd):
 print('$ '+' '.join(map(str,cmd)),flush=True);r=subprocess.call([str(x) for x in cmd]);
 if r: raise SystemExit(r)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--languages',default='fr,en,mul');ap.add_argument('--python',default=sys.executable);ap.add_argument('--force-space',action='store_true');ap.add_argument('--dump-format',choices=['auto','gz','bz2'],default='auto');ap.add_argument('--threads',type=int,default=0);ap.add_argument('--temp-dir',default='')
 a=ap.parse_args();root=Path(a.root).resolve();scripts=Path(__file__).resolve().parent;tool=scripts.parent
 env=root/'00_system/config/environment.json'; snap_path=root/'20_ingest/snapshots/wikidata/latest.json'; dumpdir=root/'10_sources/wikidata/dumps/current'; db=root/'30_working/wikidata/wikidata.compact.sqlite'; state=root/'20_ingest/checkpoints/wikidata-index-state.json'; marker=root/'20_ingest/manifests/wikidata-dump-verified.json'
 for p in [env.parent,snap_path.parent,dumpdir,db.parent,state.parent,marker.parent]:p.mkdir(parents=True,exist_ok=True)
 if os.name=='nt' and not env.exists():
  pwsh=shutil.which('pwsh.exe') or shutil.which('pwsh');diag=tool/'diagnostics'/'diag_environment.ps1'
  if pwsh and diag.exists():run([pwsh,'-NoProfile','-ExecutionPolicy','Bypass','-File',diag,'-OutputPath',env])
 if env.exists():
  try:
   e=json.loads(env.read_text(encoding='utf-8-sig'));print('[environment] RAM={} GiB | disks={}'.format(e.get('memory',{}).get('total_gib'),', '.join(f"{d.get('drive')}:{d.get('free_gib')}GiB free" for d in e.get('logical_disks',[]))),flush=True)
  except Exception as exc:print(f'[environment] diagnostic illisible: {exc}',flush=True)
 snap=discover('https://dumps.wikimedia.org/wikidatawiki/entities/',a.dump_format);snap_path.write_text(json.dumps(snap,indent=2)+'\n',encoding='utf-8');print(f"[snapshot] {snap['filename']} {human_bytes(snap['content_length'])}",flush=True)
 need=snap['content_length']*3.2;free=shutil.disk_usage(root).free;print(f"[space] libre={human_bytes(free)} prudence={human_bytes(need)}",flush=True)
 if free<need and not a.force_space:raise SystemExit('Espace libre sous le seuil prudent. Utilise --force-space seulement si tu acceptes le risque.')
 dump=dumpdir/snap['filename']
 if not (dump.exists() and dump.stat().st_size==snap['content_length']):run([a.python,scripts/'download_dump.py','--snapshot',snap_path,'--dest-dir',dumpdir])
 run([a.python,scripts/'verify_dump.py','--snapshot',snap_path,'--file',dump,'--write-marker',marker])
 cmd=[a.python,scripts/'build_compact_index.py','--dump',dump,'--db',db,'--languages',a.languages,'--state',state,'--skip-sha1','--root',root];
 if a.threads:cmd += ['--threads',str(a.threads)];
 if a.temp_dir:cmd += ['--temp-dir',a.temp_dir];
 run(cmd)
 print(json.dumps({'complete':True,'root':str(root),'dump':str(dump),'db':str(db)},indent=2))
if __name__=='__main__':main()
