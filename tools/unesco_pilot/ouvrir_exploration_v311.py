#!/usr/bin/env python3
"""Libérer explicitement une partie de la réserve sans perdre un candidat."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

def run(station,count,branch=''):
    if not 1<=count<=5000:raise ValueError('Limite de 1 à 5000 propositions')
    if not station.is_file():raise ValueError('Base station absente')
    db=sqlite3.connect(station,timeout=30)
    try:
        db.execute('PRAGMA busy_timeout=30000')
        rows=list(db.execute('''SELECT candidate_id FROM review_index WHERE state='DEFERRED'
          AND (?='' OR branch_id=?) ORDER BY priority DESC LIMIT ?''',(branch,branch,count*20)))
        rows.sort(key=lambda r:hashlib.sha256(r[0].encode()).digest())
        ids=rows[:count]
        with db:
            db.executemany("UPDATE review_index SET state='PENDING' WHERE candidate_id=? AND state='DEFERRED'",ids)
        return {'status':'EXPLORATION_V311_OK','reopened':len(ids),'branch':branch or 'toutes',
                'note':'Relancer la préparation des postes; aucune décision REJECT créée.'}
    finally:db.close()

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--station',type=Path,required=True)
    p.add_argument('--count',type=int,default=300)
    p.add_argument('--branch',default='')
    args=p.parse_args(argv)
    try:print(json.dumps(run(args.station,args.count,args.branch),ensure_ascii=False));return 0
    except (OSError,sqlite3.Error,ValueError) as ex:
        print(json.dumps({'status':'EXPLORATION_V311_REFUS','reason':str(ex)},ensure_ascii=False),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
