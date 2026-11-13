#!/usr/bin/env python3
"""Reproduce a rejected UNESCO v28 import on a CONSISTENT COPY of v25 only.

No changes to the original catalogue, station v30, v27, v28, or source SQLite.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import sys
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import decouvrir_articles_relies_v28 as v28
import catalogue_global_v25 as v25

CAT = Path(r'D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite')
RETURNS = Path(r'D:\EncyKlopedia\30_working\poste_chatgpt_v30\returns')
SOURCE = Path(r'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite')
WORK = Path(r'D:\EncyKlopedia\30_working\decouverte_articles_relies_v28')
BRANCH = HERE / 'v25_data' / 'branche_mt110.json'
SCRATCH_ROOT = Path(r'D:\EncyKlopedia\30_working\DIAGNOSTICS_IMPORT_V28')


def verify_integrity(p: Path, immutable=False):
    uri = p.resolve().as_uri() + ('?mode=ro&immutable=1' if immutable else '?mode=ro')
    c = sqlite3.connect(uri, uri=True, timeout=20)
    try:
        integrity = c.execute('PRAGMA integrity_check').fetchone()[0]
        articles = c.execute('SELECT count(*) FROM articles').fetchone()[0]
        assigns = c.execute('SELECT count(*) FROM assignments').fetchone()[0]
        seq = c.execute("SELECT value FROM meta WHERE key='sequence'").fetchone()
        return integrity, articles, assigns, seq[0] if seq else None
    finally:
        c.close()


def error_report(stage, err):
    print('\n=== ECHEC DETAILLE ===', flush=True)
    print('ETAPE :', stage, flush=True)
    print('ERREUR :', repr(err), flush=True)
    if isinstance(err, sqlite3.Error):
        print('CODE SQLITE :', getattr(err, 'sqlite_errorcode', '?'), flush=True)
        print('NOM SQLITE :', getattr(err, 'sqlite_errorname', '?'), flush=True)
    traceback.print_exception(type(err), err, err.__traceback__)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--task-id', default='v28_ac43a56fc32867_530dee66')
    args = ap.parse_args()
    if not args.task_id.startswith('v28_') or not args.task_id.replace('_', '').isalnum():
        print('ID de tache invalide')
        return 2
    matches = sorted(RETURNS.glob(args.task_id + '_*_COMPLET.csv'), key=lambda p:p.stat().st_mtime, reverse=True)
    if not matches:
        print('Aucun retour COMPLET conserve pour', args.task_id)
        print('Dossier :', RETURNS)
        return 2
    csv = matches[0]
    print('DECISIONS :', csv, flush=True)
    print('TAILLE CSV :', csv.stat().st_size, 'octets', flush=True)
    if not CAT.is_file():
        print('CATALOGUE ORIGINAL ABSENT :', CAT)
        return 2
    stage='INTEGRITE_ORIGINAL'
    try:
        original = verify_integrity(CAT)
        print('ORIGINAL integrity/articles/assignments/sequence :', original,flush=True)
        if original[0]!='ok':
            print('Catalogue original non integre : aucun test de mutation.')
            return 2
    except Exception as e:
        error_report(stage,e)
        return 2
    stage='TRANSACTION_IMMEDIATE_ORIGINAL (ROLLBACK uniquement)'
    try:
        con=sqlite3.connect(CAT,timeout=5)
        try:
            con.execute('PRAGMA busy_timeout=5000')
            con.execute('BEGIN IMMEDIATE')
            con.rollback()
            print('BEGIN IMMEDIATE original : OK (transaction annulee)',flush=True)
        finally:
            con.close()
    except Exception as e:
        error_report(stage,e)
        # Continue: the full test on a copy is still useful.
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    job=SCRATCH_ROOT / ('TEST_'+args.task_id+'_'+stamp)
    if job.exists():
        print('Collision dossier de diagnostic :', job)
        return 2
    job.mkdir(parents=True)
    copy=job/'catalogue_v25_TEST_SEULEMENT.sqlite'
    stage='SAUVEGARDE_SQLITE_VERS_COPIE_ISOLEE'
    try:
        source=sqlite3.connect(CAT.resolve().as_uri()+'?mode=ro',uri=True, timeout=30)
        try:
            dest=sqlite3.connect(copy,timeout=30)
            try:
                source.backup(dest)
            finally:
                dest.close()
        finally:
            source.close()
        clone=verify_integrity(copy, immutable=True)
        print('COPIE integrity/articles/assignments/sequence :',clone,flush=True)
        if clone!=original:
            print("ERREUR : copie differente de l'original ; test interrompu.",flush=True)
            return 2
    except Exception as e:
        error_report(stage,e)
        return 2
    stage='IMPORT_REEL_SUR_COPIE_ISOLEE'
    cfg=argparse.Namespace(branch=BRANCH, decisions=csv, catalogue_db=copy,
        source_db=SOURCE, work=WORK, catalogue_output=job/'snapshots_TEST',
        sample_limit=300, dry_run=False)
    # This hooks only the clone connection. It captures the SQL operation where a
    # read-only failure arises, without logging individual decision contents.
    last_sql=['none']
    old_open=v25.open_catalog
    def traced_open(path):
        conn=old_open(path)
        if Path(path).resolve()!=copy.resolve():
            raise RuntimeError('Securite : chemin inattendu pour une connexion ecriture')
        def trace(statement):
            last_sql[0]=statement.lstrip().split(None,1)[0][:40] if statement.strip() else '(vide)'
        conn.set_trace_callback(trace)
        return conn
    v25.open_catalog=traced_open
    try:
        print('TEST EN COURS : Apply v28 sur la COPIE, pas sur le catalogue original...',flush=True)
        result=v28.apply(cfg)
        print('TEST_IMPORT_COPIE : OK',flush=True)
        print('RESULTAT :',result,flush=True)
    except Exception as e:
        error_report(stage,e)
        print('DERNIERE OPERATION SQL :',last_sql[0],flush=True)
        return 2
    finally:
        v25.open_catalog=old_open
    stage='VERIFICATION_NON_MUTATION_ORIGINAL'
    try:
        final=verify_integrity(CAT)
        print('ORIGINAL APRES TEST :',final,flush=True)
        if final != original:
            print('ATTENTION : contenu original modifie par un autre processus durant le test.',flush=True)
            return 2
    except Exception as e:
        error_report(stage,e)
        return 2
    print('\nDIAGNOSTIC TERMINE. AUCUNE DECISION V28 IMPORTEE DANS LE CATALOGUE ORIGINAL.',flush=True)
    print('Copie de test :',job,flush=True)
    return 0

if __name__=='__main__':
    sys.exit(main())
