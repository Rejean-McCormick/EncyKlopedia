"""Pilotage optionnel E0-E2. Aucun moteur ni registre de production nouveau."""
from __future__ import annotations
import argparse, json, os, sqlite3, sys, subprocess, threading
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parent.parent
DATA = Path(r'D:\EncyKlopedia')
REGISTRY = Path(__file__).with_name('capacites.json')

def utc(): return datetime.now(timezone.utc).isoformat()
def read_json(p):
    with p.open(encoding='utf-8-sig') as f: return json.load(f)

def inventory(repo=REPO, registry=REGISTRY):
    rows=read_json(registry)
    out=[]
    for row in rows:
        p=Path(row['path']) if row['external'] else repo / row['path']
        present=p.is_dir() if row['kind']=='folder' else p.is_file()
        out.append(dict(row, resolved=str(p), presence='PRESENT' if present else 'ABSENT', operational='NON_VERIFIE'))
    return out

def health(data=DATA, compact=None):
    data=Path(data)
    db=Path(compact) if compact else data/'30_working/wikidata/wikidata.compact.sqlite'
    manifest=data/'20_evidence/manifests/wikidata-dump-verified.json'
    checkpoint=data/'90_runtime/checkpoints/wikidata-index-state.json'
    result={'observed_at':utc(),'scope':'METADATA_READ_ONLY','publication_authorized':False,
            'compact':str(db),'state':'UNKNOWN','warnings':[], 'integrity_recomputed':False}
    try:
        m=read_json(manifest); dump=Path(m['file']); size=dump.stat().st_size
        result['dump']={'path':str(dump),'bytes':size,'manifest_bytes':m.get('bytes'), 'sha1_recorded':m.get('sha1'),
                        'historically_verified':m.get('verified') is True and bool(m.get('sha1')) and m.get('sha1')==m.get('expected_sha1'), 'size_matches':size==m.get('bytes')}
    except (OSError,ValueError,KeyError,TypeError) as e: result['warnings'].append('Manifeste/dump : '+str(e))
    try: result['checkpoint']=read_json(checkpoint)
    except (OSError,ValueError) as e: result['warnings'].append('Checkpoint : '+str(e))
    if not db.is_file(): result['state']='ABSENT'; return result
    try:
        from contextlib import closing
        with closing(sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True,timeout=1)) as c:
            c.execute('PRAGMA query_only=ON'); c.execute('BEGIN')
            meta=dict(c.execute('SELECT key,value FROM meta'))
            req={'entity':{'id','wid','kind'},'name':{'entity_id','lang','name_kind','value','norm'},'meta':{'key','value'},'entity_edge':{'subject_id','property_id','target_id','statement_count','best_rank'}}
            missing={t:sorted(cols-{r[1] for r in c.execute('PRAGMA table_info('+t+')')}) for t,cols in req.items()}
            result['missing_columns']={k:v for k,v in missing.items() if v}
            result['meta']=meta
            if result['missing_columns']: result['state']='SCHEMA_INCOMPATIBLE'
            elif meta.get('schema_version')!='encyklopedia-wikidata-compact-index/v1': result['state']='SCHEMA_VERSION_UNKNOWN'
            elif meta.get('complete') in ('1','true','True'): result['state']='DECLARED_COMPLETE'
            else: result['state']='NOT_DECLARED_COMPLETE'
        cp=result.get('checkpoint',{})
        if isinstance(cp,dict) and cp.get('db') and Path(cp['db']).resolve()==db.resolve() and result['state']=='DECLARED_COMPLETE' and cp.get('complete') is False:
            result['warnings'].append('Checkpoint externe contradictoire ; non modifié. SQLite déclare la finalisation.')
    except (OSError,sqlite3.Error,ValueError) as e:
        result['state']='UNREADABLE'; result['warnings'].append(str(e))
    return result

def resolve_compact(data=DATA, compact=None):
    if compact is not None: return Path(compact)
    if data != DATA: return Path(data)/'30_working/wikidata/wikidata.compact.sqlite'
    sys.path.insert(0,str(REPO))
    from encyk_v32.config import Settings
    return Path(Settings.load().wikidata_sql)

def dashboard(data=DATA, compact=None, dik=None, v8=None):
    from ressources import dashboard as collect, DIK_ROOT, V8_ROOT
    db=resolve_compact(data,compact)
    return collect(data,dik or DIK_ROOT,v8 or V8_ROOT,health(data,db),inventory())

def lookup(wid,languages=None,data=DATA,compact=None):
    from ressources import lookup as find
    return find(resolve_compact(data,compact),wid,languages)

def lookup_world(wid,languages=None,data=DATA):
    from world import lookup_world as find
    return find(data,wid,languages)

def gui():
    from interface import gui as open_gui
    open_gui({'inventory':inventory,'dashboard':dashboard,'lookup':lookup,'lookup_world':lookup_world,'data':DATA})

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['gui','inventory','health','dashboard','lookup','lookup-world'],nargs='?',default='gui');p.add_argument('--data',type=Path,default=DATA);p.add_argument('--compact',type=Path);p.add_argument('--dik',type=Path);p.add_argument('--v8',type=Path);p.add_argument('--id');p.add_argument('--languages')
    a=p.parse_args()
    if a.mode=='gui': gui();return
    if a.mode=='inventory': result=inventory()
    elif a.mode=='health': result=health(a.data,resolve_compact(a.data,a.compact))
    elif a.mode=='dashboard': result=dashboard(a.data,a.compact,a.dik,a.v8)
    else:
        if not a.id:p.error('--id requis pour lookup')
        langs=a.languages.split(',') if a.languages else None
        result=lookup_world(a.id,langs,a.data) if a.mode=='lookup-world' else lookup(a.id,langs,a.data,a.compact)
    if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
