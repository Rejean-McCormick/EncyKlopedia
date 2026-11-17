#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EncyKlopedia: sauvegarde des RESULTATS seulement, sans fichiers de travail.

Sauvegarde exclusivement une liste blanche de bases SQLite persistantes.
Aucune traversée de répertoire; pas de ZIP de packs, de retours, de code, ni de XML.
Sources ouvertes en lecture seule et capturées avec sqlite3.Connection.backup().
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import uuid

FORMAT = 'encyklopedia.backup-resultats.v2'
VERSION = '2026-11-15-resultats-2'
# v3: snapshots autonomes en mode journal DELETE ; verification strictement sans ecriture.
SQLITE_MAGIC = b'SQLite format 3\x00'
CHUNK = 4 * 1024 * 1024

# Chemins prouvés par les outils v27/v28/v30/v31.
# Les racines sont relatives à D:\EncyKlopedia, pas au dépôt source.
RESULTS = (
    ('STATION', '30_working/poste_chatgpt_v30/station_v30.sqlite', True),
    ('KRISTAL_PRIVE', '30_working/production_kristals_v27/KRISTAL_CUMULATIF_PRIVE_V27.sqlite', True),
    ('CATALOGUE_UNESCO', '80_search_indexes/EncyKlopedia/catalogue_global_unesco_wikipedia_v25.sqlite', True),
    ('DECOUVERTE_UNESCO', '30_working/decouverte_articles_relies_v28/DECOUVERTE_ARTICLES_RELIES_V28.sqlite', True),
    ('FILE_HISTORIQUE_V27', '30_working/production_kristals_v27/FILE_PACKS_V27.sqlite', False),
    ('QUALIFICATION_V31', '30_working/qualification_multibranche_v31/qualification_multibranche_v31.sqlite', False),
    ('PREUVES_XML_V31', '30_working/preuves_xml_cibles_v31/PREUVES_XML_CIBLES_V31.sqlite', False),
)
# Gros index calculé, non nécessaire au minimum restaurable ; inclusion explicite.
DERIVED_RESULTS = (
    ('INVENTAIRE_CATEGORIES_V26', '80_search_indexes/EncyKlopedia/inventaire_categories_wikipedia_v26.sqlite', False),
)

class BackupError(Exception):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(CHUNK), b''):
            digest.update(chunk)
    return digest.hexdigest()


def within(path: Path, root: Path) -> bool:
    try:
        return os.path.commonpath((os.path.normcase(str(path.resolve())),
                                   os.path.normcase(str(root.resolve())))) == os.path.normcase(str(root.resolve()))
    except ValueError:
        return False


def is_link(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction())


def secure_source(path: Path, root: Path) -> None:
    if not within(path, root):
        raise BackupError(f'Base hors de la racine autorisee : {path}')
    rel = path.relative_to(root)
    part = root
    if is_link(part):
        raise BackupError(f'Racine liee/jonction interdite : {part}')
    for component in rel.parts:
        part = part / component
        if is_link(part):
            raise BackupError(f'Lien/jonction interdit pour une base : {part}')


def selection(data_root: Path, include_derived: bool):
    chosen = RESULTS + (DERIVED_RESULTS if include_derived else ())
    items = []
    absent_optional = []
    absent_required = []
    for role, rel, required in chosen:
        path = data_root / Path(rel)
        secure_source(path, data_root)
        if not path.is_file():
            (absent_required if required else absent_optional).append((role, path))
            continue
        with path.open('rb') as f:
            if f.read(16) != SQLITE_MAGIC:
                raise BackupError(f'Base non SQLite (signature inattendue) : {path}')
        items.append(dict(role=role, source=path, rel=Path(rel), bytes=path.stat().st_size,
                          required=required))
    return items, absent_optional, absent_required


def check_destination(out: Path, data_root: Path) -> None:
    if within(out, data_root) or within(data_root, out):
        raise BackupError('Destination dangereuse : choisir un dossier distinct, hors de D:\\EncyKlopedia.')
    if is_link(out):
        raise BackupError('La destination ne peut pas etre un lien ou une jonction.')
    if out == Path(out.anchor):
        raise BackupError('Ne pas sauvegarder directement a la racine du disque.')


def db_quickcheck(path: Path) -> None:
    # Exiger dans l'en-tete SQLite les versions lecture/ecriture=1,1
    # (mode journal de rollback). En mode WAL, ce sont 2,2 et PRAGMA
    # journal_mode sous immutable=1 peut annoncer trompeusement 'delete'.
    # Refuser un SQLite WAL sans ses journaux, car il peut etre incomplet.
    with path.open('rb') as stream:
        header = stream.read(20)
    if len(header) < 20 or header[:16] != SQLITE_MAGIC or header[18:20] != b'\x01\x01':
        raise BackupError(f'Copie non autonome (en-tete WAL ou SQLite invalide) : {path}')
    # immutable=1 UNIQUEMENT sur les copies finales ; aucune creation -shm/-wal.
    # Ne jamais activer cette option sur la SOURCE : elle peut avoir un WAL actif.
    con = sqlite3.connect(path.resolve().as_uri()+'?mode=ro&immutable=1', uri=True, timeout=30)
    try:
        if con.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
            raise BackupError(f'Echec SQLite quick_check : {path}')
    finally:
        con.close()


def sqlite_backup(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(src.resolve().as_uri()+'?mode=ro',uri=True,timeout=30)
    try:
        con.execute('PRAGMA busy_timeout=30000')
        target = sqlite3.connect(dst, timeout=30)
        try:
            # La sauvegarde SQLite inclut les transactions WAL committees de la SOURCE.
            con.backup(target, pages=1024, sleep=.1)
            target.commit()
            # backup() peut conserver le mode WAL de la source. Une lecture
            # ulterieure recreerait un -shm dans le dossier de sauvegarde :
            # convertir ici la COPIE UNIQUEMENT vers un fichier SQLite autonome.
            mode = target.execute('PRAGMA journal_mode=DELETE').fetchone()[0].lower()
            if mode != 'delete':
                raise BackupError(f'Conversion du journal de copie impossible : {dst} ({mode})')
            target.commit()
        finally:
            target.close()
    finally:
        con.close()
    for suffix in ('-wal', '-shm'):
        sidecar = dst.with_name(dst.name + suffix)
        if sidecar.exists():
            raise BackupError(f'Copie non autonome, fichier journal residuel : {sidecar}')
    db_quickcheck(dst)


def metrics(folder: Path, entries: list[dict]):
    db_by_name = {Path(e['source_path']).name: folder/e['backup_path'] for e in entries}
    queries = {
        'station_v30.sqlite': {
            'taches_terminees': "SELECT COUNT(*) FROM jobs WHERE status='DONE'",
            'taches_ouvertes': "SELECT COUNT(*) FROM jobs WHERE status NOT IN ('DONE','SKIPPED')",
        },
        'KRISTAL_CUMULATIF_PRIVE_V27.sqlite': {
            'connaissances_privees': 'SELECT COUNT(*) FROM claims',
            'citations': 'SELECT COUNT(*) FROM citations',
        },
        'catalogue_global_unesco_wikipedia_v25.sqlite': {
            'articles': 'SELECT COUNT(*) FROM articles',
            'affectations': 'SELECT COUNT(*) FROM assignments',
        },
    }
    out = {}
    for name, statements in queries.items():
        path = db_by_name.get(name)
        if path is None:
            continue
        con = sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
        try:
            result = {}
            for key, sql in statements.items():
                try:
                    result[key] = con.execute(sql).fetchone()[0]
                except sqlite3.Error as exc:
                    result[key] = {'non_mesure': str(exc)}
            out[name] = result
        finally:
            con.close()
    return out


def verify(folder: Path) -> dict:
    root = folder.resolve()
    mf = root/'MANIFEST_RESULTATS.json'
    if not mf.is_file():
        raise BackupError('Manifeste introuvable : '+str(mf))
    obj = json.loads(mf.read_text(encoding='utf-8'))
    if obj.get('format') != FORMAT:
        raise BackupError('Format de sauvegarde inconnu')
    entries = obj.get('bases')
    if not isinstance(entries,list) or not entries:
        raise BackupError('Aucune base declaree dans le manifeste')
    manifest_paths=set(); roles=set(); total=0
    for item in entries:
        rel=Path(item['backup_path'])
        if rel.is_absolute() or '..' in rel.parts or len(rel.parts)<3 or rel.parts[0]!='resultats':
            raise BackupError(f'Chemin suspect dans le manifeste : {rel}')
        key=rel.as_posix().lower()
        if key in manifest_paths or item['role'] in roles:
            raise BackupError(f'Doublon de chemin ou role : {rel}')
        manifest_paths.add(key);roles.add(item['role'])
        path=root/rel
        if not within(path,root) or is_link(path) or not path.is_file():
            raise BackupError(f'Base absente ou lien : {path}')
        if path.stat().st_size != item['bytes']:
            raise BackupError(f'Taille invalide : {rel}')
        if sha256(path) != item['sha256']:
            raise BackupError(f'SHA-256 invalide : {rel}')
        db_quickcheck(path)
        total+=item['bytes']
    for base, dirs, filenames in os.walk(root/'resultats',followlinks=False):
        if any(is_link(Path(base)/d) for d in dirs):
            raise BackupError('Lien presente dans le dossier de sauvegarde.')
        for name in filenames:
            p=Path(base)/name
            if p.relative_to(root).as_posix().lower() not in manifest_paths:
                raise BackupError(f'Fichier supplementaire non declare : {p}')
    required = {role for role,_,need in RESULTS if need}
    if not required.issubset(roles):
        raise BackupError('Bases essentielles manquantes : '+', '.join(sorted(required-roles)))
    print(f'VERIFICATION REUSSIE : {len(entries)} bases SQLite, {total:,} octets, SHA-256 et quick_check conformes.')
    return {'databases':len(entries),'bytes':total}


def save(args) -> int:
    data_root = args.data_root.resolve()
    out = args.destination.resolve()
    if not data_root.is_dir():
        raise BackupError('Racine des donnees absente : '+str(data_root))
    check_destination(out,data_root)
    items, optional_missing, required_missing = selection(data_root,args.avec_index_derive)
    print('\n=== SAUVEGARDE DES RESULTATS ENCYKLOPEDIA ===')
    print('Dossier donnees :',data_root)
    print('Destination :',out)
    for it in items:
        print(f'  INCLUS {it["role"]}: {it["bytes"]/(1024**2):,.1f} Mio')
    for role,path in optional_missing:
        print('  FACULTATIF ABSENT :', role, path)
    for role,path in required_missing:
        print('  INDISPENSABLE ABSENT :', role, path)
    print('EXCLUS SANS EXCEPTION : code, corpus Wikipedia, packs, retours, deltas, autres fichiers de travail.')
    print('Les producteurs doivent etre arretes pour garantir la coherence entre les bases.')
    if required_missing:
        raise BackupError('Sauvegarde refusee : base(s) indispensables absente(s).')
    if args.command == 'preflight':
        print('PRECONTROLE OK (aucun fichier cree).')
        return 0
    if not args.station_fermee:
        raise BackupError('Fermer la station et les producteurs ; confirmer avec --station-fermee.')
    out.mkdir(parents=True,exist_ok=True)
    # backup() can expand a DB; use headroom even if source estimate seems small.
    estimate=sum(x['bytes'] for x in items)
    margin=max(512*1024*1024, int(estimate*.2))
    free=shutil.disk_usage(out).free
    if free<estimate+margin:
        raise BackupError(f'Espace insuffisant : disponible {free:,} ; requis environ {estimate+margin:,} octets.')
    name='ENCYK_RESULTATS_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    name+='_'+uuid.uuid4().hex[:6]
    partial=out/('_INCOMPLETE_'+name)
    final=out/name
    partial.mkdir()
    written=[]
    try:
        for i, item in enumerate(items,1):
            destination=partial/'resultats'/item['rel']
            print(f'  {i}/{len(items)} Sauvegarde {item["role"]}...',flush=True)
            sqlite_backup(item['source'],destination)
            digest=sha256(destination)
            written.append({'role':item['role'],'source_path':str(item['source']),
                            'backup_path':destination.relative_to(partial).as_posix(),
                            'bytes':destination.stat().st_size,'sha256':digest})
        manifest={'format':FORMAT,'version':VERSION,
                  'created_utc':datetime.now(timezone.utc).isoformat(),
                  'source_data_root':str(data_root),'station_confirmed_stopped':True,
                  'saved_only_results_sqlite':True,'includes_wikipedia_sources':False,
                  'includes_packs_returns_or_deltas':False,'includes_program_code':False,
                  'with_derived_index':args.avec_index_derive,
                  'missing_optional_databases':[{'role':role,'path':str(path)} for role,path in optional_missing],
                  'coherence_note':'Snapshots coherents par base; arret des producteurs requis pour coherence interbases.',
                  'metrics_from_copies':metrics(partial,written),'bases':written}
        (partial/'MANIFEST_RESULTATS.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (partial/'RESTAURATION_LIRE_AVANT.txt').write_text(
            'RESULTATS ENCYKLOPEDIA : SAUVEGARDE EN LECTURE SEULE, NON CANONIQUE.\n'
            'Aucune restauration automatique : sauvegarder les fichiers courants, fermer la station et les producteurs,\n'
            'verifier les empreintes puis restaurer manuellement les bases selon source_path dans MANIFEST_RESULTATS.json.\n'
            'Ne pas copier une base sur un processus actif. Les fichiers *-wal et *-shm ne sont pas necessaires :\n'
            'les bases de sauvegarde contiennent un instantane SQLite autonome.\n'
            'Le code, le corpus Wikipedia, les packs et les retours NE sont PAS dans cette sauvegarde.\n',encoding='utf-8')
        verify(partial)
        partial.rename(final)
        print('\nSUCCES :',final)
        print('Etat photographie depuis les copies :')
        print(json.dumps(manifest['metrics_from_copies'],ensure_ascii=False,indent=2))
        print('Aucun fichier de production modifie. Copiez le dossier sur un disque distinct.')
        return 0
    except Exception as exc:
        (partial/'ERREUR.txt').write_text(str(exc),encoding='utf-8')
        print('ECHEC : copie incomplete laissee dans '+str(partial),file=sys.stderr)
        raise


def main(argv=None):
    parser=argparse.ArgumentParser(description='Sauvegarde des resultats EncyKlopedia (bases SQLite uniquement).')
    sub=parser.add_subparsers(dest='command',required=True)
    for cmd in ('preflight','backup'):
        p=sub.add_parser(cmd)
        p.add_argument('--data-root',type=Path,default=Path(r'D:\EncyKlopedia'))
        p.add_argument('--destination',type=Path,default=Path(r'D:\EncyKlopedia_SAUVEGARDES'))
        p.add_argument('--avec-index-derive',action='store_true')
        p.add_argument('--station-fermee',action='store_true')
    sub.add_parser('verify').add_argument('--backup-dir',type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        if args.command=='verify':
            verify(args.backup_dir)
            return 0
        return save(args)
    except (BackupError,OSError,sqlite3.DatabaseError,ValueError,KeyError,TypeError) as exc:
        print('SAUVEGARDE REFUSEE :',exc,file=sys.stderr)
        return 2

if __name__=='__main__':
    sys.exit(main())
