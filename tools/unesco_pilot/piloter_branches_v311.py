#!/usr/bin/env python3
"""Piloter le catalogue v25 multibranche + découvertes SQL v28 sur les index existants.

La station v30 demeure seule responsable de figer les tâches et d'importer
les décisions. Les manifestes UNESCO réels doivent être présents; aucune
nouvelle branche ou relation n'est fabriquée.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
from contextlib import closing
import subprocess
import sys

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
DEFAULT_ROOT=HERE/'v25_data'
DEFAULT_V28=Path(r'D:\EncyKlopedia\30_working\decouverte_articles_relies_v28')
DEFAULT_STATION=Path(r'D:\EncyKlopedia\30_working\poste_chatgpt_v30\station_v30.sqlite')

def readable_jobs(path):
    if not path.is_file():return 0
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        return db.execute("""SELECT COUNT(*) FROM jobs WHERE kind='v28' AND
              status IN ('WAITING','READY','SENT','ERROR','IMPORTING','NEEDS_CONFIRMATION')""").fetchone()[0]

def run(args):
    import catalogue_global_v25 as v25
    import decouverte_relationnelle_v311 as sql
    import routage_branches_v311 as routes
    manifests=sorted(args.branches.rglob('branche_*.json')) if args.branches.is_dir() else []
    if not manifests:raise ValueError('Aucun manifeste de branche disponible')
    branches=[v25.load_branch(x) for x in manifests]
    if len({b['id'] for b in branches})!=len(branches):raise ValueError('Branche dupliquée dans les manifestes')
    if readable_jobs(args.station)>0:
        raise ValueError('Des revues UNESCO sont distribuées. La découverte est gelée; importer les retours avant ce batch.')
    ledger={'status':'V311_BRANCHES_OK','manifests':len(manifests),'branches':[x['id'] for x in branches],
            'catalogue':None,'decouvertes':[],'canonical_admissions':0,'publication_authorized':False}
    if args.action in ('tout','catalogue'):
        cmd=[sys.executable,str(HERE/'catalogue_global_v25.py'),'run',
            '--source-db',str(args.source),'--catalogue-db',str(args.catalogue),
            '--max-batches',str(args.max_batches),'--batch-size',str(args.batch_size)]
        for m in manifests:cmd.extend(['--branch',str(m)])
        proc=subprocess.run(cmd,cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                            text=True,encoding='utf-8',errors='replace',timeout=14400)
        if proc.returncode:raise ValueError('Extension catalogue refusée : '+proc.stdout[-1500:])
        ledger['catalogue']='V25_RUN_OK'
    if args.action in ('tout','decouverte'):
        if not args.catalogue.is_file():raise ValueError('Catalogue v25 absent')
        with closing(sqlite3.connect(args.catalogue.resolve().as_uri()+'?mode=ro',uri=True)) as db:
            catalogued={r[0] for r in db.execute('SELECT branch_id FROM branches')}
        for path,branch in zip(manifests,branches):
            if branch['id'] not in catalogued:continue
            work=(args.stage if path.resolve()==v25.DEFAULT_BRANCH.resolve() else
                  args.stage/'branches'/routes.folder(branch['id']))
            report=sql.run(args.source,args.catalogue,path,work,max_seeds=args.max_seeds)
            ledger['decouvertes'].append(report)
    return ledger

def main(argv=None):
    from catalogue_global_v25 import DEFAULT_SOURCE,DEFAULT_CATALOG
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['tout','catalogue','decouverte'],nargs='?',default='tout')
    p.add_argument('--source',type=Path,default=DEFAULT_SOURCE)
    p.add_argument('--catalogue',type=Path,default=DEFAULT_CATALOG)
    p.add_argument('--branches',type=Path,default=DEFAULT_ROOT)
    p.add_argument('--stage',type=Path,default=DEFAULT_V28)
    p.add_argument('--station',type=Path,default=DEFAULT_STATION)
    p.add_argument('--max-batches',type=int,default=25)
    p.add_argument('--batch-size',type=int,default=500)
    p.add_argument('--max-seeds',type=int,default=3000)
    a=p.parse_args(argv)
    try:print(json.dumps(run(a),ensure_ascii=False,indent=2));return 0
    except (ValueError,OSError,sqlite3.Error,subprocess.TimeoutExpired) as ex:
        print(json.dumps({'status':'V311_BRANCHES_REFUS','reason':str(ex)},ensure_ascii=False),file=sys.stderr)
        return 2
if __name__=='__main__':raise SystemExit(main())
