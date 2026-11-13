#!/usr/bin/env python3
"""Diagnostic + optional guarded recovery of v25 writable SQLite file.

Does not alter source Wikipedia, v27, v28, v30, or return ZIPs.
A confirmed replacement is only offered after testing a clean SQLite backup.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import uuid

EXPECTED_SCHEMA = 'encyklopedia.global-article-catalogue.v25/1'


def say(text):
    print(text, flush=True)


def get_error(e):
    return f'{type(e).__name__}: {e} / {getattr(e, "sqlite_errorname", "? ")} ({getattr(e, "sqlite_errorcode", "?")})'


def read_uri(p):
    return p.resolve().as_uri() + '?mode=ro'


def info(path):
    with closing(sqlite3.connect(read_uri(path), uri=True, timeout=15)) as con:
        con.row_factory = sqlite3.Row
        integrity = con.execute('PRAGMA integrity_check').fetchone()[0]
        schema = con.execute("SELECT value FROM meta WHERE key='schema'").fetchone()
        if integrity != 'ok' or not schema or schema[0] != EXPECTED_SCHEMA:
            raise RuntimeError(f'Base invalide : integrity={integrity}, schema={schema}')
        articles = con.execute('SELECT count(*) FROM articles').fetchone()[0]
        assign = con.execute('SELECT count(*) FROM assignments').fetchone()[0]
        seq = con.execute("SELECT value FROM meta WHERE key='sequence'").fetchone()
        return {'articles': articles, 'assignments': assign, 'sequence': str(seq[0]) if seq else '?'}


def sqlite_backup(source, target):
    """SQLite online-backup, includes committed WAL changes (unlike raw file copy)."""
    with closing(sqlite3.connect(read_uri(source), uri=True, timeout=30)) as src:
        with closing(sqlite3.connect(str(target), timeout=30)) as dst:
            src.backup(dst)


def writable_probe(path):
    """Same writable open strategy as v25; acquire+release writer, no DML commits."""
    con = None
    try:
        con = sqlite3.connect(str(path), timeout=10)
        con.execute('PRAGMA busy_timeout=10000')
        only = con.execute('PRAGMA query_only').fetchone()[0]
        mode = con.execute('PRAGMA journal_mode').fetchone()[0]
        say(f'  query_only={only} ; journal_mode={mode}')
        if only:
            raise RuntimeError('query_only=ON inattendu pour une nouvelle connexion')
        con.execute('BEGIN IMMEDIATE')
        con.rollback()
        return None
    except (sqlite3.Error, RuntimeError) as exc:
        if con is not None:
            try: con.rollback()
            except sqlite3.Error: pass
        return exc
    finally:
        if con is not None:
            con.close()


def matches(first, second):
    return first == second


def move_originals(path, backup_dir, replacement):
    """Careful rename with recovery; WAL and SHM saved together with the original."""
    names = [path, Path(str(path)+'-wal'), Path(str(path)+'-shm')]
    preserved = []
    staged_placed = False
    try:
        for item in names:
            if item.exists():
                dest = backup_dir / ('ORIGINAL_' + item.name)
                if dest.exists():
                    raise RuntimeError('Nom de sauvegarde deja present : ' + str(dest))
                os.replace(str(item), str(dest))
                preserved.append((dest, item))
        os.replace(str(replacement), str(path))
        staged_placed = True
        result = writable_probe(path)
        if result is not None:
            raise RuntimeError('Le catalogue remplace reste non modifiable : ' + get_error(result))
        return True
    except BaseException:
        # Roll back the filesystem transaction if feasible. Keep all backups.
        if staged_placed and path.exists():
            try: os.replace(str(path), str(replacement))
            except OSError: say('ATTENTION: impossible de deplacer le fichier de remplacement; restauration manuelle requise.')
        for saved, original in reversed(preserved):
            if not original.exists():
                try: os.replace(str(saved), str(original))
                except OSError: say(f'ATTENTION: fichier original a remettre manuellement : {saved} -> {original}')
        raise


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--catalogue', type=Path, required=True)
    ap.add_argument('--backup-root', type=Path, required=True)
    ap.add_argument('--no-confirm', action='store_true', help='Test et sauvegarde uniquement; jamais de remplacement')
    args = ap.parse_args(argv)
    path = args.catalogue
    if not path.is_file() or path.is_symlink():
        raise RuntimeError('Catalogue absent ou chemin symbolique : ' + str(path))
    if path.stat().st_size < 100000:
        raise RuntimeError('Taille inattendue; aucun changement')
    before = info(path)
    say(f'CATALOGUE : {path} ({path.stat().st_size} octets)')
    say(f'INTEGRITE : OK ; articles={before["articles"]}, rattachements={before["assignments"]}, sequence={before["sequence"]}')
    for suffix in ['', '-wal', '-shm']:
        x = Path(str(path)+suffix)
        say(f'FICHIER {x.name} : {x.stat().st_size} octets' if x.exists() else f'ABSENT {x.name}')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    folder=args.backup_root/('AVANT_REPRISE_V28_'+stamp+'_'+uuid.uuid4().hex[:6])
    folder.mkdir(parents=True,exist_ok=False)
    backup=folder/path.name
    say(f'SAUVEGARDE SQLITE : {backup}')
    sqlite_backup(path,backup)
    if not matches(info(backup),before):
        raise RuntimeError('La sauvegarde ne correspond pas au catalogue ; aucune modification')
    # Retain physical-sidecar copies, but SQLite backup above is authoritative.
    for suffix in ('-wal','-shm'):
        side=Path(str(path)+suffix)
        if side.is_file():
            shutil.copy2(side, folder/('AVANT_TEST_'+side.name))
    say('SAUVEGARDE COHERENTE : OK')
    err=writable_probe(path)
    if err is None:
        say('RESULTAT : ECRITURE SQLITE OK. Pas de remplacement du catalogue.')
        say('Action suivante : reimporter UN retour UNESCO v28 depuis le poste v30.')
        return 0
    say('ECRITURE ORIGINALE REFUSEE : ' + get_error(err))
    # Test new database in the same directory, with fresh WAL/SHM and inherited ACL.
    replacement=path.parent/('.'+path.stem+'.test-reprise-'+uuid.uuid4().hex[:10]+'.sqlite')
    try:
        shutil.copyfile(backup,replacement)
        if info(replacement)!=before:
            raise RuntimeError('Copie locale incoherente ; aucune modification')
        test=writable_probe(replacement)
        if test is not None:
            say('REPARATION NON PROPOSEE : la copie locale ne peut pas etre modifiee non plus.')
            say('CAUSE POSSIBLE : securite Windows/Bitdefender ou droits sur le dossier.')
            say('DETAIL : '+get_error(test))
            return 3
        say('COPIE LOCALE ECRITURE OK : le fichier restaure ou les anciens fichiers SQLite auxiliaires sont suspects.')
        if args.no_confirm:
            say('MODE DIAGNOSTIC : aucun remplacement effectue.')
            return 4
        say('Une sauvegarde SQLite verifiee est deja creee. Les originaux et leurs fichiers WAL/SHM seront archives.')
        try:
            response=input('Pour remplacer uniquement le catalogue v25 par cette copie saine, saisir REPARER : ').strip()
        except EOFError:
            response=''
        if response != 'REPARER':
            say('Operation annulee. Les bases originales restent intactes.')
            return 4
        move_originals(path,folder,replacement)
        replacement=None
        if info(path)!=before:
            raise RuntimeError('Alerte : le catalogue repare a change de contenu; conserver sauvegarde et ne pas lancer v30')
        say('REPARATION OK : catalogue v25 de nouveau modifiable, sans perte de donnees constatees.')
        say(f'ORIGINAUX ARCHIVES : {folder}')
        say('Action suivante : relancer v30 et reimporter UN retour UNESCO v28 refuse.')
        return 0
    finally:
        if replacement is not None and replacement.exists():
            try: replacement.unlink()
            except OSError: say('Copie de test a nettoyer ulterieurement : ' + str(replacement))
        if replacement is not None:
            for suffix in ('-wal','-shm'):
                side=Path(str(replacement)+suffix)
                if side.exists():
                    try: side.unlink()
                    except OSError: pass


if __name__=='__main__':
    try: sys.exit(main())
    except Exception as e:
        print('REPARATION INTERROMPUE : '+get_error(e),file=sys.stderr,flush=True)
        sys.exit(2)
