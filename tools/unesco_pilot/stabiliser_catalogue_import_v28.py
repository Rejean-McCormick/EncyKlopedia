#!/usr/bin/env python3
"""Réparer conditionnellement l'état physique du catalogue restauré.

Aucune écriture de décisions v28, aucune canonisation. Les tests de DML
sont annulés par ROLLBACK. Sauvegarde SQLite cohérente et archive des anciens
fichiers avant tout remplacement.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import traceback
import uuid

SCHEMA = 'encyklopedia.global-article-catalogue.v25/1'
CAT = Path(r'D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite')
BACKUP = Path(r'D:\EncyKlopedia\30_working\SAUVEGARDE_CATALOGUE_V25_RESTAURE')


def say(*args):
    print(*args, flush=True)


def ro(path):
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f'Catalogue absent / lien symbolique : {path}')
    con = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=30)
    try:
        integrity = con.execute('PRAGMA integrity_check').fetchone()[0]
        schema = con.execute("SELECT value FROM meta WHERE key='schema'").fetchone()
        if integrity != 'ok' or not schema or schema[0] != SCHEMA:
            raise RuntimeError(f'Intégrité ou schéma inattendu : {integrity}, {schema}')
        articles = con.execute('SELECT COUNT(*) FROM articles').fetchone()[0]
        links = con.execute('SELECT COUNT(*) FROM assignments').fetchone()[0]
        seq = con.execute("SELECT value FROM meta WHERE key='sequence'").fetchone()
        return (articles, links, str(seq[0]) if seq else '?')
    finally:
        con.close()


CREATE_REVIEW = '''CREATE TABLE IF NOT EXISTS reviewed_article_links_v28(
    branch_id TEXT NOT NULL,concept_id TEXT NOT NULL,page_id INTEGER NOT NULL,
    candidate_id TEXT NOT NULL,evidence_sha256 TEXT NOT NULL,decision TEXT NOT NULL,
    reason TEXT NOT NULL,import_sha256 TEXT NOT NULL,imported_utc TEXT NOT NULL,
    PRIMARY KEY(branch_id,concept_id,page_id))'''


def write_probe(path):
    """Test exact de la première écriture d'Apply v28, suivi de ROLLBACK.

    Un BEGIN IMMEDIATE seul ne suffit PAS : c'était le faux positif du
    précédent outil. Ce probe force une vraie insertion dans main.
    """
    con = None
    try:
        con = sqlite3.connect(str(path), timeout=15)
        con.execute('PRAGMA busy_timeout=15000')
        con.execute('PRAGMA foreign_keys=ON')
        query_only = con.execute('PRAGMA query_only').fetchone()[0]
        mode = con.execute('PRAGMA journal_mode').fetchone()[0]
        say(f'TEST {path.name}: query_only={query_only}, journal={mode}')
        if query_only:
            raise RuntimeError('query_only est activé sur cette connexion')
        con.execute('BEGIN IMMEDIATE')
        con.execute(CREATE_REVIEW)
        marker = '__PROBE_' + uuid.uuid4().hex
        con.execute('INSERT INTO reviewed_article_links_v28 VALUES (?,?,?,?,?,?,?,?,?)',
                    (marker, marker, -1, marker, 'probe', 'REJECT', 'TEST ANNULE',
                     'probe', datetime.now(timezone.utc).isoformat()))
        # Toujours annuler : aucun candidat, aucune revue ni table d'essai persistante.
        con.rollback()
        return None
    except Exception as exc:
        if con is not None:
            try: con.rollback()
            except sqlite3.Error: pass
        return exc
    finally:
        if con is not None:
            con.close()


def error_message(exc):
    if isinstance(exc, sqlite3.Error):
        return f'{type(exc).__name__}: {exc} [{getattr(exc,"sqlite_errorname","?")}: {getattr(exc,"sqlite_errorcode","?")}]'
    return f'{type(exc).__name__}: {exc}'


def backup_sqlite(source, target):
    target.parent.mkdir(parents=True, exist_ok=False)
    src = sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True, timeout=60)
    try:
        dst = sqlite3.connect(str(target), timeout=60)
        try: src.backup(dst)
        finally: dst.close()
    finally: src.close()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sidecars(path):
    return [Path(str(path) + ext) for ext in ('-wal', '-shm')]


def physical_signature(path):
    return tuple((f.name, f.stat().st_size, sha256(f)) if f.exists() else (f.name, None, None)
                 for f in [path, *sidecars(path)])


def perform_swap(cat, staging, archive_dir, expected):
    """Archive l'ancien trio, installe la copie et fait le vrai probe.

    En cas de problème, remet les anciens fichiers en place. La sauvegarde
    faite avec sqlite3.backup est une seconde voie de récupération intacte.
    """
    old_files = [cat, *sidecars(cat)]
    moved = []
    installed = False
    try:
        for path in old_files:
            if path.is_file():
                archived = archive_dir / ('ORIGINAL_' + path.name)
                if archived.exists():
                    raise RuntimeError('Archive déjà présente : ' + str(archived))
                os.replace(str(path), str(archived))
                moved.append((archived, path))
        os.replace(str(staging), str(cat))
        installed = True
        if ro(cat) != expected:
            raise RuntimeError('La base réinstallée ne contient plus les mêmes données')
        err = write_probe(cat)
        if err is not None:
            raise RuntimeError('La nouvelle base ne peut pas recevoir de données : ' + error_message(err))
        if ro(cat) != expected:
            raise RuntimeError('Le test rollback a modifié le catalogue : arrêt')
        return True
    except BaseException:
        if installed and cat.exists():
            # Replacer la nouvelle copie sous son nom de staging avant rollback.
            for f in sidecars(cat):
                if f.exists():
                    try: os.replace(str(f), str(archive_dir / ('ECHEC_' + f.name)))
                    except OSError: pass
            try: os.replace(str(cat), str(staging))
            except OSError: say('ALERTE : déplacer manuellement la base nouvellement installée avant restauration.')
        for archived, original in reversed(moved):
            if not original.exists():
                try: os.replace(str(archived), str(original))
                except OSError: say('ALERTE : restauration manuelle requise :', archived, '->', original)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalogue', type=Path, default=CAT)
    parser.add_argument('--backup-root', type=Path, default=BACKUP)
    args = parser.parse_args(argv)
    cat = args.catalogue
    if not cat.is_file() or cat.is_symlink():
        raise RuntimeError('Fichier catalogue manquant ou symbolique : ' + str(cat))
    before = ro(cat)
    say('=== STABILISATION DU CATALOGUE V25 POUR LES IMPORTS V28 ===')
    say('CATALOGUE ORIGINAL :', cat)
    say('INTEGRITE : OK ; articles=%s ; rattachements=%s ; séquence=%s' % before)
    for f in [cat, *sidecars(cat)]:
        say('FICHIER:', f.name, 'octets=', f.stat().st_size if f.exists() else 'ABSENT')
    # Prévenir une intervention potentiellement dangereuse avec journal actif.
    wal = Path(str(cat) + '-wal')
    if wal.exists() and wal.stat().st_size != 0:
        raise RuntimeError('WAL non vide : ne pas remplacer un catalogue avec transactions non consolidées. Fermer toutes les applications.')

    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run = args.backup_root / ('STABILISATION_V28_' + stamp + '_' + uuid.uuid4().hex[:6])
    backup = run / cat.name
    say('SAUVEGARDE SQLITE COHERENTE :', backup)
    backup_sqlite(cat, backup)
    if ro(backup) != before:
        raise RuntimeError('La sauvegarde a des compteurs différents : aucune intervention')
    for path in sidecars(cat):
        if path.is_file():
            shutil.copy2(path, run / ('COPIE_' + path.name))
    say('SAUVEGARDE VERIFIEE :', before)

    say('TEST DE VRAIE INSERTION (ANNULEE) SUR ORIGINAL...')
    err = write_probe(cat)
    if err is None:
        say('INSERT SUR ORIGINAL : OK, ROLLBACK EFFECTUE')
        if ro(cat) != before:
            raise RuntimeError('Comptages inattendus après le test : arrêt')
        say('AUCUN REMPLACEMENT. Si v28 échoue encore, le problème est ailleurs dans l’import.')
        return 0
    say('INSERT SUR ORIGINAL : ECHEC ->', error_message(err))
    say('TEST D UNE COPIE SAINE DANS LE MEME DOSSIER...')
    staged = cat.parent / ('.' + cat.stem + '_V28_SAIN_' + uuid.uuid4().hex[:8] + '.sqlite')
    try:
        shutil.copyfile(backup, staged)  # Nouvelle identité NTFS/ACL, sans conserver les attributs restaurés.
        if ro(staged) != before:
            raise RuntimeError('Copie saine incohérente : intervention annulée')
        staged_err = write_probe(staged)
        if staged_err is not None:
            say('COPIE SAINE EN ECHEC :', error_message(staged_err))
            say('AUCUN REMPLACEMENT. Suspecter une protection ou un verrouillage externe.')
            return 3
        if ro(staged) != before:
            raise RuntimeError('Copie test modifiée malgré ROLLBACK : arrêt')
        say('INSERT SUR COPIE SAINE : OK, ROLLBACK EFFECTUE')
        stage_wal = Path(str(staged) + '-wal')
        if stage_wal.exists() and stage_wal.stat().st_size != 0:
            raise RuntimeError('Copie test avec WAL non vide : installation interdite')
        # Le -shm est une mémoire partagée volatile : son hash ne peut pas être
        # comparé après l'ouverture de connexions SQLite. Revérifier plutôt les
        # compteurs du catalogue et l'absence de transactions WAL persistantes.
        if ro(cat) != before:
            raise RuntimeError('Le catalogue a changé pendant le diagnostic : aucune réparation automatique')
        if wal.exists() and wal.stat().st_size != 0:
            raise RuntimeError('Un WAL non vide existe maintenant : remplacement interdit')
        say('REPARATION : conserver les anciens fichiers, remplacer uniquement le catalogue.')
        stage_sidecars = sidecars(staged)
        perform_swap(cat, staged, run, before)
        staged = None
        # Les sidecars appartiennent à notre nom de fichier temporaire, non au
        # catalogue installé. WAL confirmé vide juste avant le remplacement.
        for tmp in stage_sidecars:
            if tmp.exists():
                try: tmp.unlink()
                except OSError: say('Auxiliaire de test à nettoyer ultérieurement :', tmp)
        say('REPARATION EFFECTUEE ET VERIFIEE :', ro(cat))
        say('ANCIENS FICHIERS ET SAUVEGARDE CONSERVES :', run)
        say('REDEMARRER V30 PUIS REDEPOSER UN SEUL ZIP UNESCO V28 REFUSE.')
        return 0
    finally:
        # Ne supprimer que notre propre copie de test non installée.
        if staged is not None:
            for p in [staged, *sidecars(staged)]:
                if p.exists():
                    try: p.unlink()
                    except OSError: say('Copie de test à enlever plus tard :', p)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('STABILISATION INTERROMPUE : ' + error_message(exc), file=sys.stderr, flush=True)
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        sys.exit(2)
