"""Loopback HTTP checks: no start, pause, export, extraction or write."""
import json
import os
import re
import subprocess
import sys
from urllib.error import URLError,HTTPError
from ._encyk_common import add,api_json,checked_api

def win_server_process(port):
    if os.name!='nt':return None
    # Pure inspection, only PID and executable. Never execute user-provided commands.
    script=("$c=Get-NetTCPConnection -LocalPort "+str(port)+" -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1; "
            "if($c){$p=Get-CimInstance Win32_Process -Filter ('ProcessId='+$c.OwningProcess) -ErrorAction SilentlyContinue; "
            "@{ pid=$c.OwningProcess; executable=$p.ExecutablePath; name=$p.Name } | ConvertTo-Json -Compress}")
    try:
        cp=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],
                          text=True,capture_output=True,timeout=5,check=False)
        return json.loads(cp.stdout) if cp.returncode==0 and cp.stdout.strip() else None
    except (FileNotFoundError,ValueError,subprocess.TimeoutExpired):return None

def collect(cfg,with_preflight=True):
    from urllib.parse import urlparse
    checked=checked_api(cfg)
    port=urlparse(checked).port or 80
    out={'url':checked,'pid':win_server_process(port),'up':False}
    for route,key in [('/api/meta','meta'),('/api/config','config'),('/api/extract/profiles','profiles'),('/api/diagnostics/reader','process_reader'),('/api/large/latest','latest_qid')]:
        try:
            obj=api_json(cfg,route)
            out[key]=obj
            out['up']=True
        except Exception as ex:
            out[key+'_error']=type(ex).__name__+': '+str(ex)[:240]
    if with_preflight and isinstance(out.get('profiles'),list) and out['profiles']:
        profile=next((p['id'] for p in out['profiles'] if p.get('id')=='botany-canada-full-wikidata'),None)
        if profile:
            try:
                # Preflight is a read-only API action. Never POST /start.
                out['preflight']=api_json(cfg,'/api/extract/preflight',{'profile':profile})
            except Exception as ex:out['preflight_error']=type(ex).__name__+': '+str(ex)[:240]
    return out

def run(cfg,report):
    try:out=collect(cfg,True)
    except ValueError as ex:
        add(report,'encyk.skope.loopback_only','CONFIG_ERROR','Skope API must be local loopback.',{'error':str(ex)});return
    if not out['up']:
        add(report,'encyk.skope.server.available','BLOCKED','Skope server is not currently reachable; its live reader cannot be assessed.',
            {'api':out['url'],'errors':{k:v for k,v in out.items() if k.endswith('_error')}},
            'Start independent Skope with C:\\mycode\\Skope\\Start_Skope.cmd if a live check is needed.');return
    add(report,'encyk.skope.server.available','PASS','Independent Skope loopback server responds to bounded read-only endpoints.',{'api':out['url'],'server_process':out['pid']})
    config=out.get('config') or {}
    release=str(config.get('server_release') or '')
    add(report,'encyk.skope.standalone_release','PASS' if release.startswith('0.14.') else 'WARN',
        'Standalone Skope version reported by API.', {'release':release or 'unknown'})
    if 'process_reader' in out:
        r=out['process_reader']
        add(report,'encyk.skope.reader.process','PASS','Standalone server Python, owned module origins and reader cache were inspected.',
            {k:r.get(k) for k in ('python_executable','python_version','scope_common_file','fastio_file','fastio_reader_cached','reader_importable','reader_module_file','reader_import_error')})
    else:
        add(report,'encyk.skope.reader.process','WARN','Live Skope server has no reader introspection route (outdated backend?).',
            {'error':out.get('process_reader_error')})
    if 'meta' in out:
        add(report,'encyk.skope.api.meta','PASS' if str(out['meta'].get('complete'))=='1' else 'FAIL',
            'Standalone Skope reported SQLite completion.',{'complete':out['meta'].get('complete'),'entity_count':out['meta'].get('entity_count')})
    else:add(report,'encyk.skope.api.meta','FAIL','Skope metadata route unavailable.',out.get('meta_error'))
    profiles=out.get('profiles')
    add(report,'encyk.skope.api.extraction_profiles','PASS' if isinstance(profiles,list) else 'FAIL',
        'Skope extraction profile route responds.',{'profile_count':len(profiles) if isinstance(profiles,list) else None,
            'error':out.get('profiles_error')})
    if 'preflight' in out:
        p=out['preflight']
        compact={k:p.get(k) for k in ('ready','state','status','issues','blockers','source','details') if k in p}
        if isinstance(compact.get('source'),dict):
            compact['source']={k:v for k,v in compact['source'].items() if k in ('random_access_ready','fast_backend','reader_probe','fast_access_details','verified')}
        add(report,'encyk.skope.api.preflight','PASS' if p.get('ready') else 'WARN',
            'Real server preflight returned without starting extraction.',compact)
    elif out.get('preflight_error'):
        add(report,'encyk.skope.api.preflight','PARTIAL','Preflight could not be completed from the diagnostic client.',
            {'error':out['preflight_error']})
    report.metrics.update({'api_up':out['up'],'server_executable':(out['pid'] or {}).get('executable'),
                           'server_preflight_ready':(out.get('preflight') or {}).get('ready')})
