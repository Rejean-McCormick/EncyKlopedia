from __future__ import annotations
import argparse, json, re, sys, time
from pathlib import Path
HERE=Path(__file__).resolve(); ROOT0=HERE.parents[4]; LIB=ROOT0/'00_system/lib'
if str(LIB) not in sys.path:sys.path.insert(0,str(LIB))
import encyklopedia_fast as fastio
ID=re.compile(rb'"id"\s*:\s*"([QPL]\d+)"')

def find_root(v):
 p=Path(v).resolve() if v else ROOT0
 for c in [p,*p.parents]:
  if (c/'MANIFEST.json').exists():return c
 return p

def find_dump(root):
 d=root/'10_sources/wikidata/dumps/current'; xs=[]
 for pat in ('*.json.gz','*.json.bz2','*.json'):xs.extend(d.glob(pat)) if d.exists() else None
 if not xs:raise FileNotFoundError('No Wikidata dump found')
 return max(xs,key=lambda p:p.stat().st_mtime)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='');ap.add_argument('--dump',default='');ap.add_argument('--entities',type=int,default=250000);ap.add_argument('--parse-every',type=int,default=10);ap.add_argument('--threads',type=int,default=0)
 a=ap.parse_args();root=find_root(a.root);dump=Path(a.dump) if a.dump else find_dump(root); start=time.time(); n=0; parsed=0; rawbytes=0
 idx=root/'30_working/wikidata-fast/benchmark.tmp.index'
 for raw in fastio.iter_dump_raw(dump,threads=a.threads,index_path=None,root=root):
  n+=1;rawbytes+=len(raw); ID.search(raw)
  if a.parse_every and n%a.parse_every==0:
   fastio.loads(raw);parsed+=1
  if n>=a.entities:break
 dt=time.time()-start;caps=fastio.backend_capabilities(dump,root)
 print(json.dumps({'dump':str(dump),'backend':caps,'json_backend':fastio.json_backend(),'entities':n,'parsed_entities':parsed,'raw_bytes':rawbytes,'seconds':round(dt,3),'entities_per_second':round(n/dt,1) if dt else None,'raw_mib_per_second':round(rawbytes/dt/1024/1024,2) if dt else None},indent=2))
if __name__=='__main__':main()
