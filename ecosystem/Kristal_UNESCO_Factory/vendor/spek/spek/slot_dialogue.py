"""Spek -> SemantiK: contrat de FORMULATION par emplacement de template.

Spek choisit le rôle discursif et la forme demandée, jamais les faits.
Les graphes, obligations, références, modes épistémiques et choix de contenu
proviennent uniquement d'une CommunicationRequest explicitement fournie.

Cette couche exploite seulement les paramètres du contrat SemantiK 1.0:
obligation.force, context, constraints.allowed_block_kinds, list_policy,
opening_policy, closing_policy, max_length. Pas de champ inventé dans la requête.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .core import ValidationError, SEMANTIC_FORMAT, LAYOUT_FORMAT

PLAN_FORMAT = 'spek.slot-dialogue/1.0'

# Toutes les catégories proviennent des contrats de layout existants (27).
# Le profil n'est jamais déduit du contenu du Kristal.
KIND_POLICY: dict[str, tuple[str, str, list[str], int]] = {
    'question': ('question', 'ASK', ['question'], 500),
    'definition': ('definition', 'ASSERT', ['utterance'], 1800),
    'qualification': ('precaution', 'PRESENT', ['notice', 'utterance'], 1600),
    'evidence': ('source_documentaire', 'PRESENT', ['utterance', 'label_value'], 1200),
    'criterion': ('critere', 'PRESENT', ['utterance', 'label_value'], 500),
    'concept': ('designation_conceptuelle', 'PRESENT', ['utterance', 'label_value'], 1000),
    'entity': ('designation_entite', 'PRESENT', ['utterance', 'label_value'], 1000),
    'example': ('exemple', 'ASSERT', ['utterance'], 1400),
    'counterexample': ('contre_exemple', 'ASSERT', ['utterance'], 1400),
    'context': ('mise_en_contexte', 'PRESENT', ['utterance'], 1800),
    'event': ('fait_evenementiel', 'PRESENT', ['utterance', 'list'], 1800),
    'method': ('methode', 'PRESENT', ['utterance', 'list'], 1800),
    'process': ('etape_processus', 'PRESENT', ['utterance', 'list'], 1800),
    'step': ('etape_pedagogique', 'PRESENT', ['utterance', 'list'], 1800),
    'relation': ('relation', 'PRESENT', ['utterance'], 1800),
    'observation': ('observation', 'ASSERT', ['utterance'], 1800),
    'interpretation': ('interpretation', 'PRESENT', ['utterance'], 1800),
    'perspective': ('point_de_vue', 'PRESENT', ['utterance'], 1800),
    'thesis': ('these', 'ASSERT', ['utterance'], 1800),
    'premise': ('premisse', 'ASSERT', ['utterance'], 1800),
    'inference': ('inference', 'PRESENT', ['utterance'], 1800),
    'objection': ('objection', 'PRESENT', ['utterance'], 1800),
    'conclusion': ('conclusion', 'ASSERT', ['utterance'], 1800),
    'claim': ('enonce', 'ASSERT', ['utterance'], 1800),
    'scope': ('portee', 'PRESENT', ['utterance'], 1200),
    'implication': ('implication', 'PRESENT', ['utterance'], 1800),
    'objective': ('objectif', 'PRESENT', ['utterance'], 1200),
    'prerequisite': ('prerequis', 'PRESENT', ['utterance', 'list'], 1200),
    'reflection': ('questionnement', 'PRESENT', ['utterance', 'question'], 1200),
    'entry': ('entree_registre', 'PRESENT', ['utterance', 'label_value'], 1000),
    'approach': ('approche', 'PRESENT', ['utterance'], 1800),
}

TITLE_SPEC = {'intent': 'titre_court', 'force': 'PRESENT',
              'block_kinds': ['heading', 'utterance'], 'max_length': 240}
SUBTITLE_SPEC = {'intent': 'sous_titre', 'force': 'PRESENT',
                 'block_kinds': ['utterance', 'heading'], 'max_length': 400}
ABSTRACT_SPEC = {'intent': 'resume_des_obligations_selectionnees', 'force': 'PRESENT',
                 'block_kinds': ['utterance'], 'max_length': 2400}
SECTION_SPEC = {'intent': 'titre_de_section', 'force': 'PRESENT',
                'block_kinds': ['heading', 'utterance'], 'max_length': 240}


def _set(fields: dict, key: str, spec: dict, *, location: dict) -> None:
    if not isinstance(key, str) or not key.strip():
        raise ValidationError('Clé de réalisation invalide')
    if key not in fields:
        fields[key] = {**spec, 'locations': [location]}
    else:
        previous = {k: v for k, v in fields[key].items() if k != 'locations'}
        if previous != spec:
            raise ValidationError(
                f'Clé « {key} » utilisée pour des formes contradictoires : '
                'utilise des realization_key distinctes pour les champs concernés.')
        fields[key]['locations'].append(location)


def _slot_spec(layout: str, slot: str, kinds: list[str]) -> dict[str, Any]:
    if not isinstance(kinds, list) or not kinds or not all(k in KIND_POLICY for k in kinds):
        raise ValidationError(f'Forme non définie pour {layout}.{slot} ({kinds})')
    if 'question' in kinds:
        if len(kinds) != 1:
            raise ValidationError(f'{layout}.{slot}: question mêlée à une autre catégorie')
        label, force, blocks, length = KIND_POLICY['question']
    elif len(kinds) == 1:
        label, force, blocks, length = KIND_POLICY[kinds[0]]
    else:
        # Des règles de layout pouvant recevoir plusieurs catégories ne
        # permettent pas d'inférer quelle catégorie est présente. Employer
        # une forme de présentation neutre, sans changer les faits.
        label, force, blocks, length = ('presentation_mixte', 'PRESENT', ['utterance'], 1800)
    return {'intent': label, 'force': force, 'block_kinds': list(blocks), 'max_length': length}


def build_dialogue(article: dict[str, Any], layouts: list[dict[str, Any]], *,
                   language: str) -> dict[str, Any]:
    """Prescrit la forme de chaque clé UTILISÉE, sans consulter les assertions.

    Le plan n'est PAS une requête SemantiK et ne constitue pas une approbation.
    """
    if language not in ('fr', 'en', 'it'):
        raise ValidationError('Langue de dialogue non disponible')
    if article.get('format') != SEMANTIC_FORMAT:
        raise ValidationError('article.json Spek invalide')
    defs = {d['id']: d for d in layouts if d.get('format') == LAYOUT_FORMAT}
    if len(defs) != len(layouts):
        raise ValidationError('Layouts dupliqués ou invalides')
    fields: dict[str, dict] = {}
    meta = article.get('article', {})
    if not isinstance(meta, dict):
        raise ValidationError('Article invalide')
    for name, spec in [('title_key', TITLE_SPEC), ('subtitle_key', SUBTITLE_SPEC),
                       ('abstract_key', ABSTRACT_SPEC)]:
        _set(fields, meta.get(name), spec, location={'scope': 'article', 'field': name})
    units = {}
    for kind in ('units', 'evidence'):
        if not isinstance(article.get(kind), list):
            raise ValidationError(f'{kind} invalide')
        for unit in article[kind]:
            if not isinstance(unit, dict) or not isinstance(unit.get('id'), str):
                raise ValidationError('Unité de l’article invalide')
            if unit['id'] in units:
                raise ValidationError('Unités/évidences dupliquées')
            units[unit['id']] = unit
    if not isinstance(article.get('sections'), list) or not article['sections']:
        raise ValidationError('Sections manquantes')
    for section in article['sections']:
        lid = section.get('layout')
        if lid not in defs:
            raise ValidationError(f'Layout introuvable : {lid}')
        sid = section.get('id')
        _set(fields, section.get('heading_key'), SECTION_SPEC,
             location={'scope': 'section', 'section': sid, 'field': 'heading_key'})
        slots = section.get('slots', {})
        if not isinstance(slots, dict) or set(slots) - set(defs[lid]['slots']):
            raise ValidationError(f'Slots invalides pour {lid}')
        for slot, rule in defs[lid]['slots'].items():
            refs = slots.get(slot, [])
            refs = [refs] if isinstance(refs, str) else refs
            if not isinstance(refs, list) or not rule['min'] <= len(refs) <= rule['max']:
                raise ValidationError(f'Cardinalité invalide : {lid}.{slot}')
            for ref in refs:
                obj = units.get(ref)
                if obj is None:
                    raise ValidationError(f'Référence d’unité inconnue : {ref}')
                kind = obj.get('kind', 'evidence')
                if kind not in rule['allowed_kinds']:
                    raise ValidationError(f'Type non admis : {lid}.{slot} ({kind})')
                # Employer le KIND effectif de l'unité, PAS une supposition
                # tirée des seuls allowed_kinds du slot.
                spec = _slot_spec(lid, slot, [kind])
                _set(fields, obj.get('realization_key'), spec,
                     location={'scope': 'slot', 'section': sid, 'layout': lid,
                               'slot': slot, 'unit_ref': ref})
    return {'format': PLAN_FORMAT, 'language': language,
            'status': 'PREPARATION_PRIVEE_NON_APPROUVEE',
            'policy': 'forme_deterministe_par_slot_sans_choix_de_faits',
            'fields': fields}


def compose_request(request: dict[str, Any], field: dict[str, Any], *, language: str) -> dict[str, Any]:
    """Fait la demande de forme à SA sans modifier le graphe ni les obligations.

    Refuse les incompatibilités au lieu de convertir silencieusement une
    question en assertion ou une incertitude en affirmation.
    """
    if request.get('schema_version') != '1.0' or not isinstance(request.get('semantic_graph'), dict):
        raise ValidationError('CommunicationRequest sémantique incomplète')
    if not isinstance(request.get('obligations'), list) or not request['obligations']:
        raise ValidationError('Obligations sémantiques requises')
    if request.get('context', {}).get('target_language') != language:
        raise ValidationError('Langue de réalisation différente de la demande')
    expected = field['force']
    forces = [o.get('force') for o in request['obligations']]
    if expected == 'ASK':
        if any(force != 'ASK' for force in forces):
            raise ValidationError('Ce champ exige une question (force ASK) : corrige la requête SemantiK autorisée')
    elif any(force == 'ASK' for force in forces):
        raise ValidationError('Une question est fournie pour un champ non interrogatif')
    # Les autres forces ASSERT/PRESENT/DIRECT sont conservées : Spek n'invente
    # pas de force sémantique à partir d'un type de template.
    out = copy.deepcopy(request)
    constraints = out.setdefault('constraints', {})
    if not isinstance(constraints, dict):
        raise ValidationError('Contraintes SemantiK invalides')
    kinds = field['block_kinds']
    current = constraints.get('allowed_block_kinds')
    if current is not None:
        if not isinstance(current, list):
            raise ValidationError('Blocs autorisés invalides')
        kinds = [k for k in kinds if k in current]
        if not kinds:
            raise ValidationError('Le type de phrase requis est interdit par la requête SemantiK')
    constraints['allowed_block_kinds'] = kinds
    prior_length = constraints.get('max_length')
    constraints['max_length'] = min(field['max_length'], prior_length) if isinstance(prior_length, int) and prior_length > 0 else field['max_length']
    # Une réalisation de champ n'est pas un message complet : éviter les
    # saluts et conclusions hors contenu. Si explicitement requis, refuser.
    for name in ('opening_policy', 'closing_policy'):
        if constraints.get(name) == 'required':
            raise ValidationError('Ouverture/clôture obligatoire incompatible avec un champ Spek')
        constraints[name] = 'forbidden'
    constraints.setdefault('output_format', 'structured')
    if 'list' in kinds and constraints.get('list_policy') != 'forbidden':
        constraints['list_policy'] = 'preferred'
    return out


def verify_result_shape(result: dict[str, Any], field: dict[str, Any], *, request: dict) -> None:
    """Contrôle la forme EN PLUS des contrôles de provenance existants."""
    blocks = result.get('blocks')
    if not isinstance(blocks, list) or not blocks:
        raise ValidationError('SemantiK : blocs manquants')
    allowed = set(request['constraints']['allowed_block_kinds'])
    if any(b.get('kind') not in allowed for b in blocks if isinstance(b, dict)) or any(not isinstance(b, dict) for b in blocks):
        raise ValidationError('SemantiK : forme de phrase non conforme au champ Spek')


def from_files(article: Path, layouts: Path, language: str) -> dict[str, Any]:
    article = Path(article)
    layouts = Path(layouts)
    if not article.is_file() or article.is_symlink() or not layouts.is_dir() or layouts.is_symlink():
        raise ValidationError('Article ou répertoire des layouts invalide')
    source = json.loads(article.read_text(encoding='utf-8'))
    definitions = [json.loads(p.read_text(encoding='utf-8')) for p in sorted(layouts.glob('*.json'))
                   if p.is_file() and not p.is_symlink()]
    return build_dialogue(source, definitions, language=language)


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description='Préparer les formes de phrases par champ (sans faits)')
    parser.add_argument('--article', required=True, type=Path)
    parser.add_argument('--layouts', required=True, type=Path)
    parser.add_argument('--language', default='fr', choices=['fr','en','it'])
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.is_symlink():
        parser.error('Sortie déjà existante : pas de remplacement')
    plan = from_files(args.article, args.layouts, args.language)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('OK -', len(plan['fields']), 'champs; aucune requête sémantique ni aucun fait créé')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
