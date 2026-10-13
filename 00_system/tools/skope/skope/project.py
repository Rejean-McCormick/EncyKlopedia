"""Sélection non canonique d'un Kristal destinataire pour Skope intégré.

Jamais d'écriture dans le Kristal : discovery et classification sont pilotés par le Kit.
"""
from pathlib import Path
import json
import os
import re

TOOL = Path(__file__).resolve().parents[1]
ROOT = TOOL.parents[2]
BOTANY_GUIDE = TOOL / 'config/arketype/botany.scope-guidance.json'
DEFAULT_LOCALS = Path(os.environ.get('KRISTAL_LOCALS_ROOT') or r'C:\mycode\Kristal\locals')
DEFAULT_DB_ON_D = Path(r'D:\EncyKlopedia\30_working\wikidata\wikidata.compact.sqlite')


def default_database():
    if DEFAULT_DB_ON_D.is_file():
        return DEFAULT_DB_ON_D
    return ROOT/'30_working/wikidata/wikidata.compact.sqlite'


def read_kristal(folder):
    folder=Path(folder)
    if not folder.is_dir():
        raise ValueError('Dossier Kristal introuvable')
    manifest=folder/'kristal.workspace.json'
    if not manifest.is_file() or manifest.is_symlink():
        raise ValueError('Un dossier contenant kristal.workspace.json est requis')
    if manifest.stat().st_size>1024*1024:
        raise ValueError('Manifeste Kristal anormalement volumineux')
    info=json.loads(manifest.read_text(encoding='utf-8-sig'))
    if not isinstance(info,dict) or not str(info.get('format','')).startswith('kristal.local-workspace/'):
        raise ValueError('Format de workspace Kristal non reconnu')
    slug=info.get('slug')
    if not isinstance(slug,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,120}',slug):
        raise ValueError('Slug de Kristal non conforme')
    scope=info.get('state_scope') or {}
    if not isinstance(scope,dict):scope={}
    def label(v):return str(v)[:256] if v is not None else ''
    return {
        'slug':slug,
        'title':label(info.get('title') or folder.name),
        'state_ref':label(info.get('state_ref')),
        'domain':label(scope.get('domain')),
        'state_architecture':label((info.get('target') or {}).get('state_architecture')),
    }


def find_kristals(locals_root=DEFAULT_LOCALS):
    folder=Path(locals_root)
    if not folder.is_dir():return []
    results=[]
    for candidate in sorted(folder.iterdir(),key=lambda p:p.name.casefold()):
        if candidate.is_dir() and not candidate.is_symlink() and (candidate/'kristal.workspace.json').is_file():
            try: results.append((candidate,read_kristal(candidate)))
            except (ValueError, OSError, json.JSONDecodeError):pass
    return results


def default_guidance(target):
    if target and target.get('slug','').casefold()=='kristal-botany' and BOTANY_GUIDE.is_file():
        return BOTANY_GUIDE
    return None


def seed_search(target):
    if target and target.get('slug','').casefold()=='kristal-botany':
        return 'Embryophyta'
    return ''


def safe_target(target):
    """Seuls identifiants et descriptifs déclarés; aucun chemin local ni autorisation."""
    if not target:return None
    return {'format':'skope.target-kristal/1.0', 'status':'proposal_requires_review',
            'slug':target['slug'], 'title':target['title'],
            'state_ref':target['state_ref'], 'domain':target['domain'],
            'state_architecture':target['state_architecture'],
            'canonical_write_authorized':False,
            'publication_authorized':False, 'activation_authorized':False}
