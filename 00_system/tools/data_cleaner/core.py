# -*- coding: utf-8 -*-
"""EncyK v0.13.6 — nettoyer les seules copies exactes d'ancien outil.

NE SUPPRIME JAMAIS les extraits, handoffs, snapshots, catalogues Wikidata, dumps,
SQLite et lexiques. Aucun backup. Deux boutons: analyser puis déplacer/nettoyer.
Le programme fonctionne sans aucun autre fichier Python.
"""
from __future__ import annotations

import hashlib
import os
import stat
import threading
from dataclasses import dataclass
from pathlib import Path

# SHA-256 tirés de l'audit fourni. La présence de ces fichiers n'autorise PAS
# leur suppression, sauf copies identiques dans 20_evidence/legacy-ingest.
KNOWN_INGEST = {
    'README.md': '31ab467f9d3f47df596a6251c6c0292b568c338c5720046d7c1f27477650ebb9',
    'checkpoints/wikidata-index-state.json': 'd4bdb1b637ca0efbd566c8c214ae5b16ee801a0c340c9bbfdfa39403ab35fedc',
    'daat-handoff/catholic-intellectual-pilot/handoff-51e2536b0199a71b73c8.json': '4808c2a0440ab1c11472234f111debb6c5ce4dc0c9904684a5c13d199671b6c4',
    'daat-handoff/catholic-intellectual-pilot/latest.json': '3752867803f8a0709bb111fc1fd1e002f8eb317bfa622c0beb20979830323b63',
    'manifests/seeds.inventory.json': 'a2ae62ee7e6ca7d2b1dddf7088e25fd6dd7a9964228db6c5491d75b83e243a77',
    'manifests/wikidata-dump-verified.json': '8993ac8fcf5e90dd0ab94c619b42a03a153b7510d5aff242ea13c2e61d5a4016',
    'manifests/wikidata-lexemes-fr-en-sq.json': 'e341a3c7301cc2171669ca72f4ba655f4e2e295d239c57453cee7e3580b3a25a',
    'provenance/bootstrap.sources.json': 'a962a3eafd398a57b2b114c869c2762843ac7c991c1d26239c1baff8e892f516',
    'scope-snapshots/catholic-intellectual-pilot/wikidata-60c195a8624fc3ccaa1c/entities.manifest.jsonl': '0b051f41a62ede7654b0fa0b98cda47df0ed2dc3240a6e9ada96d5dd8a8b3fdb',
    'scope-snapshots/catholic-intellectual-pilot/wikidata-60c195a8624fc3ccaa1c/entities.wikidata.jsonl.gz': '7c9a90c163654a542d35ced9e8b74ba809c8a3fc2523267c430b0209c5f62fb2',
    'scope-snapshots/catholic-intellectual-pilot/wikidata-60c195a8624fc3ccaa1c/snapshot-manifest.json': 'b3ebd569d9f3e23ee91ea817489cbc3762be2a40b99c8d96a40afaad7f42930b',
    'snapshots/wikidata/latest.json': '641930a10e2404276cf258a7e4f81de5bfe7d65d23acf9523d67baf02e8508d1',
}
# SEULS ces quatre petits fichiers sont repositionnés. Les autres restent
# toujours au même chemin, y compris toutes les sorties Wikidata formatées.
ACTIVE_DEST = {
    'checkpoints/wikidata-index-state.json': '90_runtime/checkpoints/wikidata-index-state.json',
    'manifests/wikidata-dump-verified.json': '20_evidence/manifests/wikidata-dump-verified.json',
    'manifests/wikidata-lexemes-fr-en-sq.json': '20_evidence/manifests/wikidata-lexemes-fr-en-sq.json',
    'snapshots/wikidata/latest.json': '20_evidence/acquisition-snapshots/wikidata/latest.json',
}
PROTECTED_ROOTS = ('10_sources', '30_working', '40_kristal', '50_mediatheque')

class UnsafeOperation(RuntimeError):
    pass

@dataclass(frozen=True)
class Action:
    kind: str
    source: Path
    destination: Path | None
    sha256: str
    reason: str


def is_link(path: Path) -> bool:
    try:
        info=path.lstat()
    except FileNotFoundError:
        return False
    return path.is_symlink() or bool(getattr(info,'st_file_attributes',0) & getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400))


def secure_path(path: Path, root: Path) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise UnsafeOperation('Chemin hors données : '+str(path)) from exc
    for parent in (path, *path.parents):
        if is_link(parent):
            raise UnsafeOperation('Jonction ou lien non suivi : '+str(parent))
        if parent==root:
            return


def validate_root(root: str | Path) -> Path:
    data=Path(root).expanduser().absolute()
    if not data.is_dir() or not (data/'10_sources').is_dir() or not (data/'30_working').is_dir():
        raise UnsafeOperation('Dossier de données invalide : 10_sources et 30_working requis.')
    if (data/'.git').exists() or (data/'00_system').exists():
        raise UnsafeOperation('Ce chemin ressemble au dépôt de code. Choisir D:\\EncyKlopedia.')
    secure_path(data,data)
    for top in ('10_sources','20_ingest','20_evidence','30_working','40_kristal','50_mediatheque','90_runtime'):
        secure_path(data/top,data)
    return data


def digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def hash_status(path: Path, expected: str, root: Path) -> str:
    secure_path(path,root)
    if not path.exists():return 'absent'
    if not path.is_file() or is_link(path):return 'non-regulier'
    if digest(path)!=expected:return 'different'
    return 'conforme'


def make_plan(root: str | Path):
    """Plan conservateur. Ne crée/supprime jamais les productions Wikidata."""
    data=validate_root(root)
    actions=[]; alerts=[]
    for relative, expected in KNOWN_INGEST.items():
        main=data/'20_ingest'/relative
        dup=data/'20_evidence/legacy-ingest'/relative
        dest=data/ACTIVE_DEST[relative] if relative in ACTIVE_DEST else None
        ms=hash_status(main,expected,data)
        ds=hash_status(dup,expected,data)
        ts=hash_status(dest,expected,data) if dest else 'absent'
        if ms not in ('absent','conforme'):
            alerts.append('CONSERVER : fichier source non reconnu : '+main.relative_to(data).as_posix())
        if ds not in ('absent','conforme'):
            alerts.append('CONSERVER : copie modifiée / inconnue : '+dup.relative_to(data).as_posix())
        if ts not in ('absent','conforme'):
            alerts.append('CONFLIT à la destination : '+dest.relative_to(data).as_posix())
        if dest is None:
            # Conserver l'original même pour les extractions et handoffs anciens.
            # Supprimer UNIQUEMENT la copie strictement identique et dont
            # l'original existe ENCORE à son emplacement actuel.
            if ms=='conforme' and ds=='conforme':
                actions.append(Action('duplicate',dup,None,expected,
                         'Copie SHA-256 exacte ; original Wikidata conservé'))
            elif ms=='absent' and ds=='conforme':
                alerts.append('CONSERVER : seul exemplaire disponible : '+dup.relative_to(data).as_posix())
            continue
        if ts not in ('absent','conforme'):
            continue
        if ts=='absent':
            if ms=='conforme':
                actions.append(Action('move',main,dest,expected,'Replacer la métadonnée d’exécution'))
                # le futur fichier sera présent et identique après déplacement
                if ds=='conforme':
                    actions.append(Action('duplicate',dup,None,expected,'Copie de métadonnée redondante'))
            elif ms=='absent' and ds=='conforme':
                # Si l'ancien nettoyage a supprimé le fichier d'origine,
                # restaurer depuis sa seule copie sans en effacer le contenu.
                actions.append(Action('move',dup,dest,expected,'Replacer la seule métadonnée restante'))
        else:
            if ms=='conforme':
                actions.append(Action('duplicate',main,None,expected,'Métadonnée déjà présente à sa destination'))
            if ds=='conforme':
                actions.append(Action('duplicate',dup,None,expected,'Copie de métadonnée redondante'))
    return actions, alerts


def _protected_action(action: Action, root: Path) -> None:
    rel=action.source.relative_to(root).as_posix()
    if rel.startswith(tuple(x+'/' for x in PROTECTED_ROOTS)):
        raise UnsafeOperation('Protection permanente : '+rel)
    if action.kind=='duplicate':
        if rel.startswith('20_ingest/') and rel.removeprefix('20_ingest/') not in ACTIVE_DEST:
            raise UnsafeOperation('Suppression d’extraction Wikidata interdite : '+rel)
        if not (rel.startswith('20_evidence/legacy-ingest/') or
                rel.startswith('20_ingest/') and rel.removeprefix('20_ingest/') in ACTIVE_DEST):
            raise UnsafeOperation('Ce fichier ne peut pas être supprimé : '+rel)
    if action.kind=='move' and action.destination is not None:
        if rel.startswith('20_ingest/') and rel.removeprefix('20_ingest/') not in ACTIVE_DEST:
            raise UnsafeOperation('Déplacement non approuvé : '+rel)


def apply_plan(root: str | Path, confirm: bool = False):
    if not confirm:
        raise UnsafeOperation('Confirmation explicite obligatoire.')
    data=validate_root(root)
    actions, alerts=make_plan(data)
    # Bloquer les conflits de destination avant tout changement.
    if any(line.startswith('CONFLIT') for line in alerts):
        raise UnsafeOperation('Conflit de destination : aucune action.')
    for action in actions:
        _protected_action(action,data)
        secure_path(action.source,data)
        if action.destination is not None:secure_path(action.destination,data)
        if hash_status(action.source,action.sha256,data)!='conforme':
            raise UnsafeOperation('Fichier changé avant nettoyage : '+str(action.source))
    moved=0;removed=0;messages=[]
    # Faire passer les déplacements AVANT l’effacement de copies associées.
    for act in sorted(actions, key=lambda a: a.kind != 'move'):
        secure_path(act.source,data)
        if hash_status(act.source,act.sha256,data)!='conforme':
            raise UnsafeOperation('Fichier changé pendant nettoyage : '+str(act.source))
        if act.kind=='move':
            target=act.destination
            assert target is not None
            secure_path(target,data)
            if target.exists():
                if hash_status(target,act.sha256,data)!='conforme':
                    raise UnsafeOperation('Destination imprévue : '+str(target))
                # source identique déjà présente, seule la métadonnée est redondante
                act.source.unlink();removed+=1
                messages.append('EFFACER doublon métadonnée : '+str(act.source.relative_to(data)))
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                secure_path(target.parent,data)
                act.source.rename(target)
                if hash_status(target,act.sha256,data)!='conforme':
                    raise UnsafeOperation('Échec de vérification du déplacement : '+str(target))
                moved+=1
                messages.append('DÉPLACER : '+str(act.source.relative_to(data))+' -> '+str(target.relative_to(data)))
        else:
            # Revalider qu’une copie de référence existe encore, avec le même SHA.
            rel=act.source.relative_to(data).as_posix()
            if rel.startswith('20_evidence/legacy-ingest/'):
                relative=rel.removeprefix('20_evidence/legacy-ingest/')
                witness=(data/ACTIVE_DEST[relative]) if relative in ACTIVE_DEST else (data/'20_ingest'/relative)
            else:
                relative=rel.removeprefix('20_ingest/')
                witness=data/ACTIVE_DEST[relative]
            if hash_status(witness,act.sha256,data)!='conforme':
                raise UnsafeOperation('Copie de référence manquante : '+str(witness))
            act.source.unlink();removed+=1
            messages.append('EFFACER copie identique : '+str(act.source.relative_to(data)))
    # Jamais de rmtree : retirer uniquement les dossiers vides sous legacy-ingest.
    nfolders=0
    legacy=data/'20_evidence/legacy-ingest'
    if legacy.is_dir() and not is_link(legacy):
        for current,dirs,files in os.walk(legacy,topdown=False,followlinks=False):
            folder=Path(current);secure_path(folder,data)
            try: folder.rmdir();nfolders+=1
            except OSError:pass
    return {'moved':moved,'deleted_exact_duplicates':removed,'empty_directories':nfolders,'alerts':alerts,'operations':messages}


