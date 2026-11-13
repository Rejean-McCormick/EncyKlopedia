#!/usr/bin/env python3
"""Reprise contrôlée d'UN retour v28 sur le catalogue original.

Préservation : sauvegarde SQLite cohérente avant mutation, état de la station
inchangé. Aucune reconstruction de base, pas d'accès d'écriture aux sources.
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
import catalogue_global_v25 as v25
import decouvrir_articles_relies_v28 as v28

CAT = Path(r'D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite')
SOURCE = Path(r'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite')
WORK = Path(r'D:\EncyKlopedia\30_working\decouverte_articles_relies_v28')
RETURNS = Path(r'D:\EncyKlopedia\30_working\poste_chatgpt_v30\returns')
BRANCH = HERE / 'v25_data' / 'branche_mt110.json'
OUT = Path(r'D:\EncyKlopedia\30_working\catalogue_global_unesco_wikipedia_v25')
BACKUP = Path(r'D:\EncyKlopedia\30_working\SAUVEGARDE_CATALOGUE_V25_RESTAURE')
DEFAULT_TASK = 'v28_ac43a56fc32867_530dee66'


def ro_info(path):
    con = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=60)
    try:
        result = con.execute('PRAGMA integrity_check').fetchone()[0]
        article_count = con.execute('SELECT count(*) FROM articles').fetchone()[0]
        assigned_count = con.execute('SELECT count(*) FROM assignments').fetchone()[0]
        seqrow = con.execute("SELECT value FROM meta WHERE key='sequence'").fetchone()
        return (result, article_count, assigned_count, seqrow[0] if seqrow else '?')
    finally:
        con.close()


def saved_copy(source, target, expected):
    target.parent.mkdir(parents=True, exist_ok=False)
    src = sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True, timeout=60)
    try:
        dst = sqlite3.connect(target, timeout=60)
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()
    actual = ro_info(target)
    if actual != expected:
        raise RuntimeError(f'Sauvegarde incoherente. attendu={expected}, obtenu={actual}')
    return actual


def fail(phase, exc, last_sql=None):
    print('\n=== ERREUR CIBLEE ===', flush=True)
    print('ETAPE :', phase, flush=True)
    print('ERREUR :', repr(exc), flush=True)
    if isinstance(exc, sqlite3.Error):
        print('SQLITE CODE :', getattr(exc, 'sqlite_errorcode', 'indisponible'), flush=True)
        print('SQLITE NOM  :', getattr(exc, 'sqlite_errorname', 'indisponible'), flush=True)
    if last_sql:
        print('DERNIERE INSTRUCTION :', last_sql[0], flush=True)
    traceback.print_exception(type(exc), exc, exc.__traceback__)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--task-id', default=DEFAULT_TASK)
    opt = ap.parse_args()
    tid = opt.task_id
    if not (tid.startswith('v28_') and tid.replace('_', '').isalnum()):
        raise ValueError('Identifiant de tâche incorrect')
    matches = sorted(RETURNS.glob(tid + '_*_COMPLET.csv'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise RuntimeError('CSV v28 COMPLET introuvable pour '+tid)
    decisions = matches[0]
    print('TACHE :', tid, flush=True)
    print('DECISIONS :', decisions, flush=True)
    for path in (CAT, SOURCE, WORK / 'DECOUVERTE_ARTICLES_RELIES_V28.sqlite', BRANCH):
        if not path.is_file():
            raise RuntimeError('Fichier indispensable absent : '+str(path))
    before = ro_info(CAT)
    print('CATALOGUE AVANT :', before, flush=True)
    if before[0] != 'ok':
        raise RuntimeError('Catalogue non integre : import refuse, aucune mutation')
    config = argparse.Namespace(
        branch=BRANCH, decisions=decisions, catalogue_db=CAT,
        source_db=SOURCE, work=WORK, catalogue_output=OUT,
        sample_limit=300, dry_run=True,
    )
    print('VALIDATION PREALABLE EN LECTURE SEULE...', flush=True)
    dry = v28.apply(config)
    print('DRY RUN :', dry, flush=True)
    if dry.get('status') != 'V28_APPLY_PREFLIGHT_OK':
        raise RuntimeError('Preflight v28 inattendu : '+str(dry))

    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    dest = BACKUP / ('AVANT_IMPORT_DIRECT_'+tid+'_'+stamp) / CAT.name
    print('SAUVEGARDE AVANT IMPORT...', flush=True)
    saved_copy(CAT, dest, before)
    print('SAUVEGARDE SQLITE COHERENTE :', dest, flush=True)
    # Refuser de commencer si un autre traitement modifie le catalogue pendant le preflight.
    if ro_info(CAT) != before:
        raise RuntimeError('Catalogue modifie pendant la validation : abandon')

    # Instrumentation non invasive : les operations SQL sont etiquetees sans
    # recopier les decisions ou les citations dans les journaux.
    old_open = v25.open_catalog
    last_sql = ['(aucune)']
    def traced_open(path):
        if Path(path).resolve() != CAT.resolve():
            raise RuntimeError('Chemin du catalogue inattendu')
        db = old_open(path)
        def trace(sql):
            first = sql.lstrip().split(None, 2)
            last_sql[0] = ' '.join(first[:2])[:110] if first else '(vide)'
        db.set_trace_callback(trace)
        return db

    print('IMPORT SUR LE CATALOGUE ORIGINAL...', flush=True)
    config.dry_run = False
    v25.open_catalog = traced_open
    phase = 'IMPORT ORIGINAL'
    try:
        result = v28.apply(config)
        print('V28_APPLY_OK :', result, flush=True)
        phase = 'INTEGRITE APRES IMPORT'
        after = ro_info(CAT)
        print('CATALOGUE APRES :', after, flush=True)
        if after[0] != 'ok' or after[1] < before[1] or after[2] < before[2]:
            raise RuntimeError('Integrite ou compteurs inattendus apres import : REQUIERT INSPECTION')
        print('\nREPRISE REUSSIE. Redemarrer v30 puis redeposer LE MEME ZIP pour que le poste enregistre le resultat.', flush=True)
        print('NE PAS reimporter plusieurs ZIP en bloc sans confirmer le fonctionnement de la station.', flush=True)
        return 0
    except Exception as exc:
        fail(phase, exc, last_sql)
        print('SAUVEGARDE CONSERVEE :', dest, flush=True)
        try:
            print('ETAT ACTUEL ORIGINAL :', ro_info(CAT), flush=True)
        except Exception as other:
            print('ETAT ACTUEL NON LISIBLE :', repr(other), flush=True)
        print('NE PAS RESTAURER AUTOMATIQUEMENT LA SAUVEGARDE : aucun fichier original n a ete efface.', flush=True)
        return 2
    finally:
        v25.open_catalog = old_open


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        fail('PREPARATION', exc)
        sys.exit(2)
