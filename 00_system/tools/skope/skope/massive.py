"""Opt-in, disk-backed taxonomic scope inventory over EncyK compact SQLite.

NOT source JSON extraction and NOT a Wikidata occurrence proof. No global-memory
selected-node set. Original EncyK index stays read only; state lives in 30_working.
"""
from __future__ import annotations
import json
import shutil
import sqlite3
import threading
import time
import uuid
import os
import io
import struct
import zipfile
from pathlib import Path
from contextlib import closing
from .db import connect,_eid,_wid
from .scope import validate_recipe

_lock=threading.RLock()
_running={}  # job id => threading.Event; one running job per Python server


def _folder(index):
    # D:\EncyKlopedia\30_working\wikidata\index.sqlite -> 30_working\skope-large-scopes
    p=Path(index).resolve(strict=True)
    if p.parent.name.lower()!='wikidata' or p.parent.parent.name.lower()!='30_working':
        raise ValueError('Batch inventory requires an index under 30_working/wikidata; no implicit external working folder')
    return p.parent.parent/'skope-large-scopes'


def _path(index,job_id):
    if not isinstance(job_id,str) or len(job_id)!=32 or any(c not in '0123456789abcdef' for c in job_id):
        raise ValueError('Invalid job ID')
    root=_folder(index)
    folder=root/job_id
    if not folder.is_dir() or folder.is_symlink():raise ValueError('Job not found')
    return folder


def _json(obj):return json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(',',':'))


def _status(folder):
    with sqlite3.connect(folder/'state.sqlite',timeout=20) as c:
        r=c.execute('SELECT state,selected,expanded,pending,created_at,updated_at,message FROM status').fetchone()
    spec=json.loads((folder/'recipe.json').read_text('utf8'))
    return {'job':folder.name,'state':r[0],'selected':r[1],'expanded':r[2],'pending':r[3],
            'created_at':r[4],'updated_at':r[5],'message':r[6],'requested_max_entities':spec['max_entities'],
            'root':spec['root'],'depth':spec['default_depth'],'geography_mode':spec['geography']['mode'],
            'output_ready':(folder/'selected-qids.jsonl').is_file() and r[0]=='completed',
            'result_zip_ready':(folder/'results.zip').is_file() and r[0]=='completed',
            'working_zone':'30_working/skope-large-scopes/'+folder.name,
            'scope_complete':r[0]=='completed',
            'limitations':['QID inventory from an aggregated index; no original Wikidata statements or references',
                           'Geography is a review preference, NOT a filter in the massive run',
                           'External convergence is NOT used in the massive QID run',
                           'Completed means traversal finished within the selected depth; not a global flora inventory',
                           'No publication or canonical Kristal changes']}


def status(index,job_id):return _status(_path(index,job_id))


def start(index,recipe,resume=None):
    spec=validate_recipe(recipe)
    if not spec['allowed_properties']:
        raise ValueError('Batch inventory requires explicit properties (e.g. P171); blank/all is not supported')
    if spec['direction']=='both':
        raise ValueError('Choose one relation direction for batch inventory')
    if spec['geography']['mode']=='documented_only':
        raise ValueError('Strict geography requires verified source evidence; choose Prioritize without excluding for this QID inventory.')
    if spec['convergence']['include']:
        raise ValueError('Review accepted external-convergence candidates separately before running the batch inventory.')
    folder=None
    with _lock:
        if _running:raise ValueError('Another Skope batch inventory is already running; pause it or wait.')
        if resume:
            folder=_path(index,resume)
            old=json.loads((folder/'recipe.json').read_text('utf8'))
            current=old.get('max_entities')
            next_max=spec.get('max_entities')
            unchanged={k:v for k,v in old.items() if k!='max_entities'}=={k:v for k,v in spec.items() if k!='max_entities'}
            growing=next_max==0 or (current!=0 and next_max>=current)
            if not unchanged or not growing:
                raise ValueError('Resuming requires the same recipe and an equal or larger QID target (0 = unlimited)')
            state=_status(folder)['state']
            if state not in ('paused','failed','interrupted','running','queued','limit_reached'):
                raise ValueError('A job can only resume if paused, interrupted, failed or target-limited')
            if old!=spec:
                tmp=folder/'recipe.json.part'
                tmp.write_text(_json(spec)+'\n',encoding='utf8')
                tmp.replace(folder/'recipe.json')
        else:
            root=_folder(index)
            free=shutil.disk_usage(root.parent).free
            if free<2*1024**3:raise ValueError('Less than 2 GiB of free space: cannot start the batch inventory')
            root.mkdir(parents=True,exist_ok=True)
            folder=root/uuid.uuid4().hex
            folder.mkdir()
            with closing(connect(index)) as check:
                if check.execute('SELECT 1 FROM entity WHERE id=?',(_eid(spec['root']),)).fetchone() is None:
                    raise ValueError('Root QID not found in the EncyK index')
            (folder/'recipe.json').write_text(_json(spec)+'\n',encoding='utf8')
            with sqlite3.connect(folder/'state.sqlite') as c:
                c.executescript('''PRAGMA journal_mode=DELETE;
                    CREATE TABLE selected(id INTEGER PRIMARY KEY);
                    CREATE TABLE queue(id INTEGER NOT NULL,branch TEXT NOT NULL,level INTEGER NOT NULL,maxdepth INTEGER NOT NULL,
                                       processed INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(id,branch));
                    CREATE INDEX queue_unprocessed ON queue(processed,level,id);
                    CREATE TABLE status(state TEXT NOT NULL,selected INTEGER NOT NULL,expanded INTEGER NOT NULL,
                                        pending INTEGER NOT NULL,created_at REAL NOT NULL,updated_at REAL NOT NULL,message TEXT NOT NULL);
                ''')
                initial=_eid(spec['root'])
                c.execute('INSERT INTO selected VALUES (?)',(initial,))
                c.execute('INSERT INTO queue VALUES (?, ?, ?, ?, 0)',(initial,'__root__',0,8))
                now=time.time()
                c.execute('INSERT INTO status VALUES (?,?,?,?,?,?,?)',('queued',1,0,1,now,now,'Ready'))
        with sqlite3.connect(folder/'state.sqlite') as c:
            c.execute('UPDATE status SET state=?,updated_at=?,message=?',('queued',time.time(),'Queued to start or resume'))
        flag=threading.Event()
        _running[folder.name]=flag
        thread=threading.Thread(target=_worker,args=(str(index),folder,flag),daemon=True,name='skope-scan-'+folder.name[:6])
        thread.start()
    return _status(folder)


def pause(index,job_id):
    _path(index,job_id)
    with _lock:
        flag=_running.get(job_id)
        if flag is None:raise ValueError('Job is not active; check status')
        flag.set()
    return {'job':job_id,'state':'pausing','message':'Pause requested; waiting for the current batch'}


def _update(c,state,message=''):
    count=c.execute('SELECT COUNT(*) FROM selected').fetchone()[0]
    pending=c.execute('SELECT COUNT(*) FROM queue WHERE processed=0').fetchone()[0]
    expanded=c.execute('SELECT COUNT(*) FROM queue WHERE processed=1').fetchone()[0]
    c.execute('UPDATE status SET state=?,selected=?,expanded=?,pending=?,updated_at=?,message=?',
              (state,count,expanded,pending,time.time(),message))


def _worker(index,folder,stop):
    spec=json.loads((folder/'recipe.json').read_text('utf8'))
    props=tuple(sorted(set(int(p[1:]) for p in spec['allowed_properties'])))
    marks=','.join('?' for _ in props)
    direction=spec['direction'];column='target_id' if direction=='in' else 'subject_id'
    other='subject_id' if direction=='in' else 'target_id'
    sql=f'SELECT {other},property_id FROM entity_edge WHERE {column}=? AND property_id IN ({marks})'
    try:
        with closing(connect(index)) as source,sqlite3.connect(folder/'state.sqlite',timeout=60) as state:
            state.execute('PRAGMA synchronous=NORMAL')
            _update(state,'running','Scanning the read-only index in batches');state.commit()
            while not stop.is_set():
                batch=state.execute('SELECT id,branch,level,maxdepth FROM queue WHERE processed=0 ORDER BY level,id LIMIT 150').fetchall()
                if not batch:break
                limit=spec['max_entities']
                hit_limit=False
                processed=0
                with state:
                    for eid,branch,level,maximum in batch:
                        if stop.is_set():break
                        if level<maximum:
                            for target,pid in source.execute(sql,(eid,*props)):
                                if target<1 or target>=1_000_000_000:continue # scope est QID uniquement
                                if branch=='__root__':
                                    b=f'P{pid}:{direction}'
                                    target_max=spec['branches'].get(b,spec['default_depth'])
                                    if target_max<=0:continue
                                else:b,target_max=branch,maximum
                                # Contient uniquement les QID réellement présents dans l'index.
                                exists=state.execute('SELECT 1 FROM selected WHERE id=?',(target,)).fetchone()
                                if not exists:
                                    if limit and state.execute('SELECT selected FROM status').fetchone()[0]>=limit:
                                        hit_limit=True;break
                                    if source.execute('SELECT 1 FROM entity WHERE id=?',(target,)).fetchone() is None:continue
                                    state.execute('INSERT INTO selected VALUES (?)',(target,))
                                    state.execute('UPDATE status SET selected=selected+1')
                                if level+1<target_max:
                                    state.execute('INSERT INTO queue VALUES (?,?,?,?,0) ON CONFLICT(id,branch) DO UPDATE SET level=MIN(level,excluded.level), processed=CASE WHEN excluded.level<level THEN 0 ELSE processed END',(target,b,level+1,target_max))
                        if hit_limit:break  # Garder la ligne non traitée pour une reprise sans perte
                        state.execute('UPDATE queue SET processed=1 WHERE id=? AND branch=?',(eid,branch))
                        processed+=1
                    state.execute('UPDATE status SET expanded=expanded+?, updated_at=?',(processed,time.time()))
                if hit_limit:break
                if shutil.disk_usage(folder).free<2*1024**3:
                    raise OSError('Batch inventory stopped: less than 2 GiB of free disk space')
            if stop.is_set():
                with state:_update(state,'paused','Paused; resume with the same settings')
            elif hit_limit:
                with state:_update(state,'limit_reached','Limit reached before traversal completed. Refine or use 0 for unlimited.')
            else:
                with state:_update(state,'completed','Traversal complete. QID inventory is ready.')
                # Un QID par ligne, sur disque. Pas de JSON source ni de justificatif inventé.
                output=folder/'selected-qids.jsonl';tmp=folder/'selected-qids.jsonl.part'
                with tmp.open('w',encoding='utf8',newline='\n') as f:
                    for (qid,) in state.execute('SELECT id FROM selected ORDER BY id'):
                        f.write(json.dumps({'wikidata_qid':_wid(qid)},ensure_ascii=False)+'\n')
                tmp.replace(output)
    except Exception as e:
        try:
            with sqlite3.connect(folder/'state.sqlite') as state:
                with state:_update(state,'failed',type(e).__name__+': '+str(e)[:300])
        except Exception:pass
    finally:
        with _lock:_running.pop(folder.name,None)


def latest(index):
    folder=_folder(index)
    if not folder.is_dir():return None
    candidates=(p for p in folder.iterdir() if p.is_dir() and not p.is_symlink() and len(p.name)==32 and (p/'state.sqlite').is_file())
    candidate=max(candidates,key=lambda p:p.stat().st_mtime,default=None)
    return _status(candidate) if candidate else None


RESULT_README = """Skope · Taxonomic QID inventory (working / non-canonical)

selected-qids.jsonl : one Wikidata QID per line (not original Wikidata records).
recipe.json         : exact traversal settings, including geographic priorities.
summary.json        : job statistics, warnings and limitations.

IMPORTANT
- Completion applies only to the selected root, properties and depth.
- Geography (Canada / North America) was NOT used as a filter for this mass run.
- External convergence was NOT performed during this mass run.
- This is NOT a collection of species occurrences or medicinal/morphological evidence.
- Original Wikidata statements, sources and qualifiers require subsequent extraction.
- No changes were made to the Kristal canon or the original SQLite index.
"""


def prepare_result_zip(index, job_id):
    folder=_path(index,job_id)
    info=_status(folder)
    if info['state']!='completed' or not info['output_ready']:
        raise ValueError('A completed inventory is required before exporting a result ZIP')
    result=folder/'results.zip'
    if result.is_file():
        return result
    tmp=folder/'results.zip.part'
    recipe=folder/'recipe.json'
    records=folder/'selected-qids.jsonl'
    if recipe.is_symlink() or records.is_symlink():
        raise ValueError('Unexpected symlink in result files')
    summary={
       'format':'skope.qid-inventory-result/1.0',
       'job':info['job'], 'state':info['state'], 'root':info['root'],
       'selected_qids':info['selected'], 'expanded':info['expanded'], 'pending':info['pending'],
       'depth':info['depth'], 'created_at':info['created_at'], 'updated_at':info['updated_at'],
       'working_non_canonical':True, 'contains_source_wikidata_json':False,
       'geographic_filter_applied':False, 'external_convergence_applied':False,
       'limitations':info['limitations'],
    }
    try:
        with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
            z.write(records,arcname='selected-qids.jsonl')
            z.write(recipe,arcname='recipe.json')
            z.writestr('summary.json',json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
            z.writestr('README.txt',RESULT_README)
        tmp.replace(result)
    finally:
        tmp.unlink(missing_ok=True)
    return result


def result_path(index,job_id):
    return str(prepare_result_zip(index,job_id).resolve())


def open_results_folder(index,job_id):
    folder=_path(index,job_id)
    prepare_result_zip(index,job_id)  # ensure results.zip appears in Explorer on first open
    if os.name!='nt':
        raise ValueError('Open in File Explorer is available on Windows only')
    os.startfile(str(folder))
    return {'opened':True,'folder':str(folder)}


def copy_zip_to_windows_clipboard(index,job_id):
    # CF_HDROP (15) represents a FILE, not its path as plain text.
    path=result_path(index,job_id)
    if os.name!='nt':
        raise ValueError('File clipboard is supported only when Skope runs on Windows')
    import ctypes
    import ctypes.wintypes
    shell=ctypes.WinDLL('shell32',use_last_error=True)
    user=ctypes.WinDLL('user32',use_last_error=True)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GlobalAlloc.argtypes=(ctypes.wintypes.UINT,ctypes.c_size_t)
    kernel.GlobalAlloc.restype=ctypes.c_void_p
    kernel.GlobalLock.argtypes=(ctypes.c_void_p,)
    kernel.GlobalLock.restype=ctypes.c_void_p
    kernel.GlobalUnlock.argtypes=(ctypes.c_void_p,)
    kernel.GlobalUnlock.restype=ctypes.wintypes.BOOL
    kernel.GlobalFree.argtypes=(ctypes.c_void_p,)
    kernel.GlobalFree.restype=ctypes.c_void_p
    user.OpenClipboard.argtypes=(ctypes.c_void_p,)
    user.OpenClipboard.restype=ctypes.wintypes.BOOL
    user.EmptyClipboard.restype=ctypes.wintypes.BOOL
    user.SetClipboardData.argtypes=(ctypes.wintypes.UINT,ctypes.c_void_p)
    user.SetClipboardData.restype=ctypes.c_void_p
    # DROPFILES: DWORD pFiles=20, POINT pt=(0,0), BOOL fNC=0, BOOL fWide=1
    contents=struct.pack('<IiiII',20,0,0,0,1)+(path+'\0\0').encode('utf-16le')
    h=kernel.GlobalAlloc(0x0042,len(contents))  # GMEM_MOVEABLE | GMEM_ZEROINIT
    if not h:raise OSError('Clipboard memory allocation failed')
    ownership=False
    try:
        ptr=kernel.GlobalLock(h)
        if not ptr:raise OSError('Cannot lock clipboard memory')
        ctypes.memmove(ptr,contents,len(contents))
        kernel.GlobalUnlock(h)
        opened=False
        for _ in range(8):
            if user.OpenClipboard(None):
                opened=True;break
            time.sleep(.08)
        if not opened:raise OSError('Windows clipboard is busy; try again')
        try:
            if not user.EmptyClipboard():raise OSError('Cannot clear Windows clipboard')
            if not user.SetClipboardData(15,h):raise OSError('Cannot place ZIP file on clipboard')
            ownership=True
        finally:user.CloseClipboard()
    finally:
        if not ownership:kernel.GlobalFree(h)
    return {'copied_file':True,'filename':Path(path).name,'message':'ZIP file copied. Paste with Ctrl+V in Windows Explorer.'}
