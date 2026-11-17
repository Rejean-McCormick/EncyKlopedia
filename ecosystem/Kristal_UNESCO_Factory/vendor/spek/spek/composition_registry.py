"""Read AI-authored wiki compositions, without choosing anything from Kristal content.

This module checks contracts and enables read-only presentation of explicit recipes.
It never assigns templates, invents assertions, invokes SemantiK, or publishes.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .core import ValidationError
from .kristal_identity import canonical_slug

FORMAT = 'spek.wiki-ai-composition/1.0'
INDEX_FORMAT = 'spek.wiki-ai-composition-registry/1.0'
ASSIGNMENTS_FORMAT = 'spek.wiki-kristal-composition-assignments/1.0'


def _plain_json(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
        raise ValidationError('Composition illisible, trop volumineuse ou lien symbolique : ' + str(path))
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        raise ValidationError(f'JSON de composition invalide: {path}: {e}') from e
    if not isinstance(data, dict):
        raise ValidationError('Objet JSON attendu : ' + path.name)
    return data


def read_registry(root: Path) -> dict[str, Any]:
    """Load and validate AI-authored recipes without inference or content matching."""
    root = Path(root).resolve()
    wiki = root / 'template_library' / 'wiki'
    if wiki.is_symlink() or (wiki / 'compositions').is_symlink():
        raise ValidationError('Dossier de compositions symbolique interdit')
    index = _plain_json(wiki / 'composition-registry.json')
    if index.get('format') != INDEX_FORMAT or index.get('allow_runtime_template_inference') is not False:
        raise ValidationError('Registre IA: format ou politique de non-inférence invalide')
    entries = index.get('compositions')
    if not isinstance(entries, dict) or not entries:
        raise ValidationError('Registre IA vide')
    from .wiki import load_profiles
    profiles = load_profiles(wiki / 'archetype-profiles.json')
    compositions: dict[str, dict] = {}
    for cid, row in entries.items():
        if not isinstance(row, dict) or not isinstance(row.get('file'), str):
            raise ValidationError('Entrée de composition invalide : ' + str(cid))
        path = Path(row['file'])
        if path.is_absolute() or len(path.parts) != 2 or path.parts[0] != 'compositions' or path.suffix != '.json' or path.stem != cid.removeprefix('arketype-'):
            raise ValidationError('Chemin de composition non autorisé : ' + str(cid))
        doc = _plain_json(wiki / path)
        if doc.get('format') != FORMAT or doc.get('composition_id') != cid:
            raise ValidationError('Identité incohérente : ' + cid)
        archetype = doc.get('archetype', {}).get('slug')
        if archetype not in profiles:
            raise ValidationError('Archétype de composition inconnu : '+cid)
        sections = doc.get('sections_in_order')
        if not isinstance(sections, list) or not sections:
            raise ValidationError('Sections manquantes : ' + cid)
        ids = set()
        for section in sections:
            if not isinstance(section, dict) or not isinstance(section.get('section_id'), str) or not isinstance(section.get('layout_id'), str):
                raise ValidationError('Section invalide : ' + cid)
            if section['section_id'] in ids:
                raise ValidationError('Section dupliquée : ' + cid)
            ids.add(section['section_id'])
            if section['layout_id'] not in profiles[archetype]['allowed_layouts']:
                raise ValidationError('Layout non permis par l’archétype : ' + cid)
            layout = root / 'layouts' / (section['layout_id'] + '.json')
            if not layout.is_file() or layout.is_symlink():
                raise ValidationError('Layout manquant : ' + section['layout_id'])
            obj = _plain_json(layout)
            if obj.get('id') != section['layout_id'] or obj.get('version') != section.get('layout_version'):
                raise ValidationError('Version du layout incompatible : ' + section['layout_id'])
            for slot, required in section.get('required_slots', {}).items():
                spec = obj.get('slots', {}).get(slot)
                if not isinstance(spec, dict) or not isinstance(required, int) or isinstance(required, bool) or required < spec.get('min', -1) or required > spec.get('max', -1):
                    raise ValidationError('Slot de composition incompatible : ' + cid + '/' + slot)
        if row.get('layout_sequence') != [s['layout_id'] for s in sections] or row.get('section_count') != len(sections):
            raise ValidationError('Séquence ou nombre de sections incohérents : ' + cid)
        compositions[cid] = doc
    assignments = _plain_json(wiki / 'kristal-assignments.json')
    if assignments.get('format') != ASSIGNMENTS_FORMAT or assignments.get('policy', {}).get('runtime_inference_allowed') is not False:
        raise ValidationError('Assignations IA invalides ou inférence activée')
    assigned = assignments.get('assignments')
    if not isinstance(assigned, dict):
        raise ValidationError('Assignations : objet attendu')
    for key, row in assigned.items():
        if not isinstance(row, dict) or row.get('composition_id') not in compositions:
            raise ValidationError('Assignation avec composition inconnue : ' + str(key))
        if row.get('kristal_identity') != key or canonical_slug(key) != key or not isinstance(row.get('state_sha256'), str) or not re.fullmatch(r'[a-f0-9]{64}', row['state_sha256']):
            raise ValidationError('Assignation incomplète pour ' + str(key))
    return {'index': index, 'compositions': compositions, 'assignments': assigned}


def assignment_for_identity(registry: dict, identity: str) -> dict | None:
    """Only exact registry IDs count: no heuristics, no title-based matching."""
    return registry['assignments'].get(canonical_slug(identity))
