"""Explicit, local Spek Studio workflow. Does not discover templates from Kristals.

Preview reuses the existing Spek compiler; input validation never publishes.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .core import ValidationError
from .kristal_identity import canonical_slug
from .composition_registry import assignment_for_identity, read_registry
from .ai_proposals import proposal_for_identity, read_proposals
from .source_reviews import read_source_reviews, compare_raw_state_snapshot


def _read_small_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    if path.is_symlink() or path.stat().st_size > 2_000_000:
        raise ValidationError('Fichier non admissible (lien symbolique ou trop volumineux) : ' + str(path))
    try:
        obj = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ValidationError(f'JSON illisible dans {path}: {exc}') from exc
    if not isinstance(obj, dict):
        raise ValidationError(f'Objet JSON attendu : {path}')
    return obj


def inspect_kristal(folder: Path, spek_root: Path) -> dict[str, Any]:
    """Explicit metadata only: no recursive scan, archetype matching, or selection."""
    folder = Path(folder).resolve()
    if not folder.is_dir():
        raise ValidationError('Dossier Kristal introuvable')
    workspace = _read_small_json(folder/'kristal.workspace.json')
    state_index = _read_small_json(folder/'canon'/'state.index.json')
    if workspace is None and state_index is None:
        raise ValidationError('Dossier non identifié : ni kristal.workspace.json ni canon/state.index.json')
    declared_identity = workspace.get('slug') if workspace else None
    identity = canonical_slug(declared_identity) if isinstance(declared_identity,str) else None
    registry = read_registry(spek_root)
    assignment = assignment_for_identity(registry, identity) if isinstance(identity,str) else None
    proposals = read_proposals(spek_root,registry)
    proposal = proposal_for_identity(proposals, identity) if isinstance(identity, str) else None
    review = read_source_reviews(spek_root,proposals).get(identity) if isinstance(identity,str) else None
    snapshot_check = compare_raw_state_snapshot(folder,review) if review else 'NOT_REVIEWED'
    return {
        'folder': str(folder), 'identity': identity, 'declared_identity': declared_identity, 'title': workspace.get('title') if workspace else None,
        'state_ref': workspace.get('state_ref') if workspace else None,
        'workspace_format': workspace.get('format') if workspace else None,
        'native_model': workspace.get('native_model', {}).get('kind') if workspace and isinstance(workspace.get('native_model'),dict) else None,
        'has_state_index': state_index is not None,
        'assignment': assignment, 'proposal': proposal, 'structure_review': review, 'source_snapshot_comparison': snapshot_check, 'assignment_state_pin_verified': False,
        'composition': registry['compositions'].get(assignment['composition_id']) if assignment else None,
        'mode': 'inspection_metadata_only_no_inference',
    }


def project_pair(article: Path, realizations: Path) -> tuple[Path, Path]:
    article, realizations = Path(article).expanduser().absolute(), Path(realizations).expanduser().absolute()
    for p in (article, realizations):
        if not p.is_file() or p.is_symlink() or p.suffix != '.json':
            raise ValidationError('Fichier JSON de projet introuvable ou non sûr : ' + str(p))
    return article, realizations


def command_for_preview(spek_root: Path, article: Path, realizations: Path, language: str, output: Path, *, build: bool = True) -> list[str]:
    if language not in {'fr','en','it'}:
        raise ValidationError('Langue de prévisualisation non prise en charge')
    article, realizations = project_pair(article, realizations)
    root = Path(spek_root).resolve()
    if not (root/'spek'/'core.py').is_file():
        raise ValidationError('Racine Spek invalide')
    cmd = [sys.executable, '-m', 'spek', 'build' if build else 'check',
           '--source', str(article), '--realizations', str(realizations),
           '--layouts', str(root/'layouts'), '--languages', language]
    if build:
        cmd.extend(['--formats', 'html', '--out', str(output)])
    return cmd


def execute_preview(spek_root: Path, article: Path, realizations: Path, language: str, *, build: bool) -> dict[str, Any]:
    """Run current Spek CLI; output is private temporary directory outside repo."""
    root = Path(spek_root).resolve()
    out = Path(tempfile.mkdtemp(prefix='spek-preview-prive-')) if build else None
    cmd = command_for_preview(root, article, realizations, language, out or root, build=build)
    try:
        result = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=120, check=False)
    except subprocess.TimeoutExpired as exc:
        raise ValidationError('Prévisualisation trop longue (120 s), opération arrêtée') from exc
    if result.returncode:
        raise ValidationError('Compilateur Spek : ' + (result.stderr or result.stdout or 'échec').strip()[-2500:])
    if build:
        page = out / language / 'index.html'
        if not page.is_file():
            raise ValidationError('Spek a terminé mais aucune page HTML valide n’a été produite')
        return {'status': 'built_private_not_published', 'page': str(page), 'directory': str(out), 'output':result.stdout}
    return {'status': 'checked_only_not_published', 'output':result.stdout}
