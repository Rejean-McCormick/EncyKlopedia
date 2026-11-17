"""Display AI-authored provisional compositions; never promote them to publishable assignments.

The proposals are authored off-line from a Manager report. No Spek code chooses,
classifies or derives a template based on a Kristal at runtime.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core import ValidationError
from .kristal_identity import canonical_slug

PROPOSAL_FORMAT = 'spek.wiki-ai-kristal-proposals/1.0'


def read_proposals(root: Path, registry: dict[str, Any]) -> dict[str, dict]:
    path = Path(root) / 'template_library' / 'wiki' / 'kristal-ai-proposals.json'
    if not path.exists():
        return {}  # compatibility with repositories that have no proposal catalog yet
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
        raise ValidationError('Registre des propositions IA illisible, lié ou trop volumineux')
    try:
        document = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ValidationError('Registre des propositions IA invalide : ' + str(exc)) from exc
    if not isinstance(document, dict) or document.get('format') != PROPOSAL_FORMAT:
        raise ValidationError('Format de propositions IA inconnu')
    policy = document.get('policy', {})
    if (not isinstance(policy, dict) or policy.get('runtime_template_inference_allowed') is not False
            or policy.get('AI_editorial_proposals_not_approved_assignments') is not True
            or policy.get('no_publication_authority') is not True):
        raise ValidationError('La séparation propositions / autorisations est obligatoire')
    proposals = document.get('proposals')
    if not isinstance(proposals, dict) or len(proposals) != document.get('count'):
        raise ValidationError('Nombre de propositions IA incohérent')
    compositions = registry.get('compositions', {})
    for key, p in proposals.items():
        if (not isinstance(p, dict) or p.get('kristal_identity') != key
                or canonical_slug(key) != key):
            raise ValidationError('Identité canonique de proposition IA invalide')
        if (p.get('editorial_status') != 'AI_PROPOSED_FROM_MANAGER_METADATA_NOT_APPROVED'
                or p.get('publication_eligible') is not False):
            raise ValidationError('La proposition ne peut être une autorisation de publication')
        cids = [p.get('primary_composition_id')] + p.get('supplementary_composition_ids', [])
        if not all(isinstance(c, str) and c in compositions for c in cids) or len(cids) != len(set(cids)):
            raise ValidationError('Composition non reconnue pour '+key)
        sections = p.get('ordered_sections')
        if not isinstance(sections, list) or not sections:
            raise ValidationError('Sections proposées absentes pour '+key)
        for s in sections:
            if not isinstance(s, dict) or s.get('composition_id') not in cids:
                raise ValidationError('Section de composition étrangère pour '+key)
            source = compositions[s['composition_id']]['sections_in_order']
            if not any(r['section_id'] == s.get('section_id') and r['layout_id'] == s.get('layout_id') for r in source):
                raise ValidationError('Section / layout absent dans la recette de '+key)
            if s.get('selected_assertion_ids') != [] or s.get('required_slots_fulfilled') is not False:
                raise ValidationError('Contenu insuffisamment vérifié pour '+key)
    return proposals


def proposal_for_identity(proposals: dict[str, dict], identity: str) -> dict | None:
    """Exact identity lookup only; no runtime semantic matching or inference."""
    return proposals.get(canonical_slug(identity))
