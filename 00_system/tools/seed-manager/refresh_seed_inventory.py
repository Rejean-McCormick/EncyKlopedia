#!/usr/bin/env python3
from pathlib import Path
import json, hashlib, datetime
BASE=Path(__file__).resolve().parents[3]
WORLDS=BASE/'10_sources/seeds/active/worlds'
REG=BASE/'10_sources/seeds/active/intellectual-registry/intellectuals.seed.json'
OUT=BASE/'20_ingest/manifests/seeds.inventory.json'

def sha256(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
worlds=[]
for d in sorted([p for p in WORLDS.iterdir() if p.is_dir()] if WORLDS.exists() else []):
 files=[p for p in d.rglob('*') if p.is_file()]
 worlds.append({'world_key':d.name,'file_count':len(files),'has_world_yaml':(d/'world.yaml').exists()})
records=0
if REG.exists():
 o=json.loads(REG.read_text(encoding='utf-8'));records=len(o.get('records',[])) if isinstance(o,dict) else len(o)
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({'schema_version':'encyklopedia-seed-inventory/v1','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'active_worlds':worlds,'active_world_count':len(worlds),'intellectual_registry_records':records,'intellectual_registry_sha256':sha256(REG) if REG.exists() else None},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(OUT)
