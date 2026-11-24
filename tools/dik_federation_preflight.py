#!/usr/bin/env python3
"""Explicit, read-only DIK federated registry preflight for ecosystem consumers.

This tool does not give a candidate registry publication authority. It never
edits a Kristal, reads EncyK lexical data, starts a runtime, or contacts a URL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

PROFILE = 'dik.federated-semantic-registry/0.1-candidate'
LANGS = ['en','fr','es','de','nl','sv','da','nn','fi','et','af','it','pt']


def digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as source:
        for part in iter(lambda: source.read(1048576), b''):
            h.update(part)
    return h.hexdigest()


def preflight(directory: Path) -> dict:
    """Check a local diK snapshot without granting lexical/gate acceptance."""
    directory=Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('missing directory or symlinked diK registry')
    mf=directory/'manifest.json'
    if mf.is_symlink() or not mf.is_file() or mf.stat().st_size>128*1024:
        raise ValueError('missing or oversized diK manifest')
    manifest=json.loads(mf.read_text(encoding='utf-8'))
    if (manifest.get('profile')!=PROFILE or manifest.get('purpose')!='read_only_derived_index_not_canonical'
        or manifest.get('status')!='CANDIDATE_FEDERATED_VIEW'
        or manifest.get('sqlite_file')!='registry.sqlite3'
        or manifest.get('languages_target')!=LANGS
        or manifest.get('automatic_approvals')!=0
        or manifest.get('published_dictionaries')!=0
        or manifest.get('new_semantic_authority_created') is not False):
        raise ValueError('diK candidate contract mismatch or false authority claim')
    dbfile=directory/'registry.sqlite3'
    if not dbfile.is_file() or dbfile.is_symlink() or digest(dbfile)!=manifest.get('sqlite_sha256'):
        raise ValueError('diK registry digest mismatch')
    with sqlite3.connect(f'{dbfile.resolve().as_uri()}?mode=ro&immutable=1',uri=True) as db:
        if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':
            raise ValueError('diK registry SQLite integrity failure')
        required={'identities':{'kristal','namespace_id','semantic_id'},
                  'crosswalk':{'namespace_id','semantic_id','wikidata_id','decision'},
                  'kristals':{'kristal','state'}}
        for table,columns in required.items():
            actual={row[1] for row in db.execute(f'PRAGMA table_info({table})')}
            if not columns<=actual:
                raise ValueError('diK schema mismatch: '+table)
        rows=db.execute('SELECT COUNT(*) FROM kristals').fetchone()[0]
        if rows!=manifest['statistics']['official_kristals']:
            raise ValueError('diK manifest count mismatch')
    return {'profile':PROFILE,'validation':'INTEGRITY_ONLY',
            'candidate_registry_seen':True,'publication_authorized':False,
            'new_runtime_set_authorized':False,'new_kristal_identity_authorized':False,
            'source_read_only':True,'local_kq_kp_occurrences':manifest['statistics']['local_kq_kp_occurrences'],
            'official_kristals':manifest['statistics']['official_kristals'],
            'legacy_no_preserved':manifest.get('legacy_no_retained') is True}


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description='Verify read-only diK registry, never approve or publish')
    p.add_argument('--dir',type=Path,required=True)
    args=p.parse_args(argv)
    print(json.dumps(preflight(args.dir),ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
