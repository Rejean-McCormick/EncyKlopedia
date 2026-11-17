"""Small, non-destructive EncyK discovery helpers. No large data is read."""
from __future__ import annotations
import json
import os
import re
from pathlib import Path
from urllib import request,parse,error

QID=re.compile(r'^Q[1-9][0-9]*$')

def data_root(cfg):
    return Path(cfg.get('encyk',{}).get('data_root','D:/EncyKlopedia'))

def project_root(cfg):
    return Path(cfg['_target_root'])

def bounded_json(path, size=512_000):
    p=Path(path)
    if not p.is_file() or p.is_symlink():return None
    if p.stat().st_size > size:raise ValueError('metadata too large')
    return json.loads(p.read_text(encoding='utf-8-sig'))

def safe_children(parent,limit=16):
    p=Path(parent)
    if not p.is_dir() or p.is_symlink():return []
    return sorted((i for i in p.iterdir() if i.is_dir() and not i.is_symlink()),
                  key=lambda p:p.stat().st_mtime, reverse=True)[:limit]

def checked_api(cfg):
    u=cfg.get('encyk',{}).get('skope_api','http://127.0.0.1:8767')
    p=parse.urlparse(u)
    if p.scheme!='http' or p.hostname not in ('127.0.0.1','localhost','::1') or p.username or p.password or p.path not in ('','/') or p.query or p.fragment:
        raise ValueError('Only a loopback Skope API is allowed')
    return u.rstrip('/')

class _NoExternalRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Diagnostic HTTP redirects are not permitted")

def api_json(cfg,path,payload=None):
    base=checked_api(cfg)
    if not path.startswith('/api/') or '//' in path or '..' in path:
        raise ValueError('Unsafe diagnostic API path')
    t=float(cfg.get('encyk',{}).get('skope_connection_timeout_seconds',3))
    if payload is not None:
        b=json.dumps(payload).encode('utf-8')
        req=request.Request(base+path,data=b,headers={'Content-Type':'application/json'},method='POST')
    else:req=request.Request(base+path,method='GET')
    opener=request.build_opener(_NoExternalRedirect())
    with opener.open(req,timeout=max(.2,min(t,12))) as resp:
        raw=resp.read(70_000)
        if len(raw)>65_536:raise ValueError('HTTP payload exceeds diagnostics limit')
        return json.loads(raw)

def add(report,ident,status,description,evidence=None,recommendation=None):
    report.add(ident,status,'encyk',description,evidence=evidence,recommendation=recommendation)
