#!/usr/bin/env python3
"""Reset targeted editorial HOLD status in a stopped EncyKlopedia v30 station.

No catalogue, V27, V28, original job source/bundle or decision ZIP is changed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

DEFAULT_WORK=Path(r'D:\EncyKlopedia\30_working\poste_chatgpt_v30')


def fingerprint(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):
            h.update(chunk)
    return h.hexdigest()


def run(work:Path, preview=False):
    work=work.resolve()
    path=work/'station_v30.sqlite'
    if not path.is_file():raise ValueError('Base du poste v30 absente : '+str(path))
    con=sqlite3.connect(path.as_uri()+'?mode=rw',uri=True,timeout=6)
    con.row_factory=sqlite3.Row
    try:
        con.execute('PRAGMA busy_timeout=6000')
        if con.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
            raise ValueError('Integrite SQLite NON valide. Aucune operation.')
        jobs_columns={r['name'] for r in con.execute('PRAGMA table_info(jobs)')}
        reviews_columns={r['name'] for r in con.execute('PRAGMA table_info(review_index)')}
        needed_jobs={'id','kind','status','source_path','source_sha256','bundle_path','bundle_sha256',
                     'review_approved','review_rejected','review_hold','review_return_path',
                     'sent_utc','finished_utc','return_sha256','error'}
        needed_rev={'candidate_id','state','task_id','evidence_sha256'}
        if not needed_jobs.issubset(jobs_columns) or not needed_rev.issubset(reviews_columns):
            raise ValueError('Schema de la station v30 incompatible : aucune modification')
        if con.execute("SELECT 1 FROM jobs WHERE status='IMPORTING' LIMIT 1").fetchone():
            raise ValueError('Import en cours ou interrompu : aucune modification sans verification.')
        waiting=list(con.execute('''SELECT j.*,l.lane AS lane
            FROM jobs j LEFT JOIN lanes l ON l.job_id=j.id
            WHERE j.kind='v28' AND j.status='NEEDS_CONFIRMATION'
            AND j.review_approved=0 AND j.review_rejected=0
            ORDER BY j.created_utc,j.id'''))
        available=[];unavailable=[]
        for row in waiting:
            try:
                csvfile=Path(row['source_path'])
                bundle=Path(row['bundle_path'])
                if not csvfile.is_file():raise ValueError('CSV source local absent')
                if fingerprint(csvfile)!=row['source_sha256']:raise ValueError('CSV source SHA incorrect')
                if not bundle.is_file():raise ValueError('ZIP source local absent')
                if fingerprint(bundle)!=row['bundle_sha256']:raise ValueError('ZIP source SHA incorrect')
                available.append(dict(row))
            except (OSError,ValueError) as exc:
                unavailable.append({'id':row['id'],'cause':str(exc)})
        hold_rows=list(con.execute("SELECT candidate_id,task_id FROM review_index WHERE state='HOLD' ORDER BY candidate_id"))
        protected=con.execute("SELECT count(*) FROM review_index WHERE state='DECIDED'").fetchone()[0]
        partial=con.execute("SELECT count(*) FROM jobs WHERE kind='v28' AND status='NEEDS_CONFIRMATION' AND (review_approved>0 OR review_rejected>0)").fetchone()[0]
        summary={'operation':'RESET_HOLD_CIBLE_V30', 'work':str(work),
            'revues_tout_hold_rearmables':len(available),
            'revues_tout_hold_sources_manquantes':unavailable,
            'anciens_candidats_hold_a_reprogrammer':len(hold_rows),
            'decisions_approve_reject_preservees':protected,
            'revues_partielles_avec_decisions_preservees':partial,
            'taches_v27_modifiees':0,'catalogue_v25_modifie':False,
            'bases_v27_v28_modifiees':False}
        if preview:
            print(json.dumps({'mode':'APERÇU','resultat':summary},ensure_ascii=False,indent=2))
            return summary
        if not available and not hold_rows:
            print(json.dumps({'mode':'RIEN_A_MODIFIER','resultat':summary},ensure_ascii=False,indent=2))
            return summary
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        backupdir=work/'SAUVEGARDES_RESET_HOLD_V30'/stamp
        if backupdir.exists():raise ValueError('Conflit de repertoire de sauvegarde : '+str(backupdir))
        backupdir.mkdir(parents=True)
        backup=backupdir/'station_v30_AVANT_RESET.sqlite'
        with sqlite3.connect(backup) as out:
            con.backup(out)
            if out.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                raise ValueError('Sauvegarde SQLite non valide, aucun reset')
        summary['sauvegarde_sqlite']=str(backup)
        summary['sauvegarde_sha256']=fingerprint(backup)
        (backupdir/'PLAN_ET_STATS_AVANT_RESET.json').write_text(
            json.dumps({'date_utc':stamp,'resume':summary,
                        'taches_rearmees':[x['id'] for x in available],
                        'candidats_reinitialises':[x['candidate_id'] for x in hold_rows]},
                       ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        # All state changes occur inside a single transaction. Never modify the
        # catalogue or the discovery database, and never recycle DECIDED rows.
        con.execute('BEGIN IMMEDIATE')
        try:
            for j in available:
                new_status='READY' if j['lane'] is not None else 'WAITING'
                con.execute('''UPDATE jobs SET status=?,sent_utc=NULL,finished_utc=NULL,
                    return_sha256=NULL,review_return_path=NULL,review_approved=0,
                    review_rejected=0,review_hold=0,error=''
                    WHERE id=? AND kind='v28' AND status='NEEDS_CONFIRMATION'
                    AND review_approved=0 AND review_rejected=0''',(new_status,j['id']))
                if con.total_changes<0:raise RuntimeError('Erreur SQL inattendue')
                con.execute('''UPDATE review_index SET state='QUEUED'
                    WHERE task_id=? AND state IN ('HOLD','QUEUED')''',(j['id'],))
            # Candidate-level HOLD entries from prior completed reviews are
            # deliberately rediscovered as NEW future tasks, not retroactively
            # modified in their original immutable jobs.
            con.execute("UPDATE review_index SET state='PENDING',task_id=NULL,evidence_sha256=NULL WHERE state='HOLD'")
            if 'events' in {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}:
                con.execute('INSERT INTO events(at_utc,message) VALUES(?,?)',(
                    datetime.now(timezone.utc).isoformat(timespec='seconds'),
                    f'RESET HOLD V30 : {len(available)} revues tout-HOLD réarmées, {len(hold_rows)} candidats HOLD remis PENDING. Sauvegarde : {backup}'))
            con.commit()
        except BaseException:
            con.rollback()
            raise
        summary['statut']='RESET_EFFECTUE'
        print(json.dumps(summary,ensure_ascii=False,indent=2))
        return summary
    finally:
        con.close()


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--work',type=Path,default=DEFAULT_WORK)
    p.add_argument('--preview',action='store_true')
    args=p.parse_args()
    try:run(args.work,args.preview)
    except Exception as ex:
        print('RESET_HOLD_REFUSE : '+str(ex),file=sys.stderr)
        raise SystemExit(2)
