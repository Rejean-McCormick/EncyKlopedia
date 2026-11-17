"""Interface de commande de référence pour automatisation et tests locaux."""
from __future__ import annotations
import argparse
import sqlite3
import zipfile
import json
from contextlib import closing
from pathlib import Path
from .config import Settings
from .sql import open_work
from .sources import import_unesco,discover,discover_fallback
from .pipeline import make_wave,import_for_job,jobs_overview,export_proposals,retry_candidates,cancel_job,recovery_report
from .federation import scan_islands,list_islands,describe_island,export_federated_read_view,admit_proposals,choose_island_location
from .doctor import run as doctor_run


def run(argv=None):
    p=argparse.ArgumentParser(description='EncyKlopedia V32 — manager local privé')
    p.add_argument('--config',type=Path,help='Fichier config/settings.json')
    subs=p.add_subparsers(dest='action',required=True)
    subs.add_parser('doctor')
    sub=subs.add_parser('index-unesco');sub.add_argument('--max-branches',type=int)
    sub=subs.add_parser('discover');sub.add_argument('--branch');sub.add_argument('--budget',type=int,default=10000);sub.add_argument('--no-graph',action='store_true')
    sub=subs.add_parser('fallback');sub.add_argument('--branch');sub.add_argument('--budget',type=int,default=2500)
    sub=subs.add_parser('prepare');sub.add_argument('--branch');sub.add_argument('--kind',choices=['both','select','enrich'],default='both')
    sub=subs.add_parser('import');sub.add_argument('path',type=Path);sub.add_argument('--job-id',required=True);sub.add_argument('--correction',action='store_true');sub.add_argument('--strict',action='store_true')
    subs.add_parser('jobs')
    subs.add_parser('recover')
    sub=subs.add_parser('retry');sub.add_argument('candidate_ids',nargs='+');sub.add_argument('--reason',required=True)
    sub=subs.add_parser('cancel-job');sub.add_argument('job_id');sub.add_argument('--reason',required=True)

    sub=subs.add_parser('branches');sub.add_argument('--limit',type=int,default=100)
    sub=subs.add_parser('candidates');sub.add_argument('--branch');sub.add_argument('--limit',type=int,default=100)
    subs.add_parser('islands-scan')
    sub=subs.add_parser('islands');sub.add_argument('--branch');sub.add_argument('--limit',type=int,default=150)
    sub=subs.add_parser('island');sub.add_argument('island_key')
    sub=subs.add_parser('island-use');sub.add_argument('island_key');sub.add_argument('root',type=Path)
    sub=subs.add_parser('export');sub.add_argument('path',type=Path);sub.add_argument('--branch')
    sub=subs.add_parser('read-view');sub.add_argument('path',type=Path);sub.add_argument('island_keys',nargs='+')
    subs.add_parser('admit')
    args=p.parse_args(argv);settings=Settings.load(args.config)
    if args.action=='doctor':value=doctor_run(settings)
    elif args.action=='admit':value=admit_proposals()
    else:
        db=open_work(settings.db_path)
        try:
            if args.action=='index-unesco':value=import_unesco(db,settings.unesco_root,args.max_branches)
            elif args.action=='discover':value=discover(db,settings,args.branch,not args.no_graph,args.budget)
            elif args.action=='fallback':value=discover_fallback(db,settings,args.branch,args.budget)
            elif args.action=='prepare':value=make_wave(db,settings,args.branch,args.kind)
            elif args.action=='import':value=import_for_job(db,args.path,args.job_id,correction=args.correction,allow_partial=not args.strict)
            elif args.action=='retry':value=retry_candidates(db,args.candidate_ids,args.reason)
            elif args.action=='cancel-job':value=cancel_job(db,args.job_id,args.reason)
            elif args.action=='recover':value=recovery_report(db)
            elif args.action=='jobs':value=jobs_overview(db)
            elif args.action=='branches':value=[dict(x) for x in db.execute('''SELECT b.branch_id,b.title,
                        (SELECT COUNT(*) FROM branch_concepts WHERE branch_id=b.branch_id) AS concepts,
                        (SELECT COUNT(*) FROM candidates WHERE branch_id=b.branch_id) AS candidates
                        FROM branches b ORDER BY branch_id LIMIT ?''',(args.limit,))]
            elif args.action=='candidates':
                sql='SELECT * FROM candidates WHERE branch_id=? ORDER BY priority DESC LIMIT ?' if args.branch else 'SELECT * FROM candidates ORDER BY priority DESC LIMIT ?'
                params=(args.branch,args.limit) if args.branch else (args.limit,)
                value=[dict(x) for x in db.execute(sql,params)]
            elif args.action=='islands-scan':value=scan_islands(db,settings.kristal_roots)
            elif args.action=='islands':value=list_islands(db,args.branch,args.limit)
            elif args.action=='island':value=describe_island(db,args.island_key)
            elif args.action=='island-use':value=choose_island_location(db,args.island_key,args.root)
            elif args.action=='export':value=export_proposals(db,args.path,args.branch)
            elif args.action=='read-view':value=export_federated_read_view(db,args.island_keys,args.path)
            else:raise ValueError('Action inconnue')
        finally:db.close()
    print(json.dumps(value,ensure_ascii=False,indent=2,default=str))
    return value


def main():
    try:run()
    except (OSError,ValueError,RuntimeError,sqlite3.Error,zipfile.BadZipFile) as exc:
        import sys
        print(json.dumps({'status':'ERROR','reason':str(exc)},ensure_ascii=False),file=sys.stderr)
        sys.exit(2)

if __name__=='__main__':main()
