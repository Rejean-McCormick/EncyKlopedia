"""Canonical Kristal slug normalization; does NOT classify content or select templates.

Latest local slugs omit the historical 'kristal-' namespace prefix. The legacy
Manager report still contains it. Existing source paths/state_refs are untouched.
"""
from __future__ import annotations
import re
from .core import ValidationError

_VALID = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')


def canonical_slug(raw: str) -> str:
    if not isinstance(raw, str) or not raw or raw != raw.strip():
        raise ValidationError('Slug Kristal vide ou invalide')
    value = raw[8:] if raw[:8].lower() == 'kristal-' else raw
    value = value.lower()
    if not _VALID.fullmatch(value):
        raise ValidationError('Slug Kristal invalide : ' + raw)
    return value
