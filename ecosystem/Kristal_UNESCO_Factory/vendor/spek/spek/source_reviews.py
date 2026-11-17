"""Read AI-authored offline structural reviews. No content classification in Spek.

Only inspect reviewed records and optionally compare a raw source-file digest to
warn that a local file differs from the editorial snapshot.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from .core import ValidationError
from .kristal_identity import canonical_slug

FORMAT = 'spek.wiki-kristal-source-reviews/1.0'
_SHA = re.compile(r'[0-9a-f]{64}\Z')


def read_source_reviews(root: Path, proposals: dict) -> dict:
    path = Path(root) / 'template_library' / 'wiki' / 'kristal-structure-reviews.json'
    if not path.exists():
        return {}
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
        raise ValidationError('Registre des revues structurelles non admissible')
    try:
        document = json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, OSError) as exc:
        raise ValidationError('Registre de revue illisible') from exc
    if document.get('format') != FORMAT or document.get('publication_eligible') is not False or document.get('automatic_inference_by_Spek_allowed') is not False:
        raise ValidationError('Le registre de revue doit être strictement non publiable')
    entries = document.get('reviews')
    if not isinstance(entries,dict) or len(entries) != document.get('reviewed_count'):
        raise ValidationError('Nombre de revues incohérent')
    for slug,entry in entries.items():
        if slug not in proposals or entry.get('kristal_identity') != slug or canonical_slug(slug) != slug:
            raise ValidationError('Revue non liée à une proposition : '+slug)
        source = entry.get('source',{})
        if not isinstance(source.get('portable_state_raw_sha256'),str) or not _SHA.fullmatch(source['portable_state_raw_sha256']):
            raise ValidationError('Empreinte de revue non conforme : '+slug)
        if source.get('file_hash_is_not_verified_canonical_commitment') is not True:
            raise ValidationError('Empreinte brute présentée à tort comme qualifiée')
        total = source.get('assertion_occurrences')
        positions = []
        for section in entry.get('ordered_structural_sections',[]):
            if section.get('publication_status') != 'NOT_AUTHORIZED' or section.get('selection_status') != 'NOT_SELECTED' or section.get('template_status') != 'TYPED_LAYOUT_AVAILABLE_UNREALIZED':
                raise ValidationError('Section de revue non autorisée : '+slug)
            observed = section.get('source_observation',{})
            group = observed.get('source_positions_zero_based')
            if not isinstance(group,list) or any(type(i) is not int or i < 0 or i >= total for i in group):
                raise ValidationError('Indices source invalides pour '+slug)
            if len(group) != observed.get('observed_assertion_occurrences'):
                raise ValidationError('Comptage de positions incohérent')
            positions.extend(group)
        if total != len(positions) or len(set(positions)) != total:
            raise ValidationError('Répartition des assertions incomplète ou dupliquée pour '+slug)
        if entry.get('approval',{}).get('editorial') is not False:
            raise ValidationError('La revue ne peut être considérée approuvée')
    return entries


def compare_raw_state_snapshot(folder: Path, review: dict) -> str:
    """Digest equality only. Never analyze or assign semantic templates."""
    rel = review['source'].get('portable_state_relative_path','')
    root = Path(folder).resolve()
    path = root / rel
    if not path.resolve(strict=False).is_relative_to(root) or path.is_symlink() or not path.is_file():
        return 'SOURCE_FILE_NOT_FOUND'
    if path.stat().st_size > 20_000_000:
        return 'SOURCE_TOO_LARGE'
    return ('MATCHES_UPLOADED_SNAPSHOT' if hashlib.sha256(path.read_bytes()).hexdigest() == review['source']['portable_state_raw_sha256'] else 'DIFFERS_FROM_UPLOADED_SNAPSHOT')
