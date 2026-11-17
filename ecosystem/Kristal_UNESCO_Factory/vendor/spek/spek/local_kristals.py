"""Local, explicit identity lookup for Spek Studio (no template or fact inference).

The lookup reads ONLY top-level ``kristal.workspace.json`` identity files inside
an operator-controlled ``locals`` directory. It never edits the collection,
recursively crawls sources, authorizes publication, or chooses a template.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .core import ValidationError
from .kristal_identity import canonical_slug

MAX_WORKSPACE_BYTES = 2_000_000


def validate_locals_root(root: Path) -> Path:
    """A real directory; never follow a symlink supplied as the collection root."""
    p = Path(root).expanduser()
    if p.is_symlink() or not p.is_dir():
        raise ValidationError('Le dossier locals sélectionné est absent ou non admissible.')
    return p.resolve()


def _settings_file() -> Path:
    if os.name == 'nt' and os.environ.get('LOCALAPPDATA'):
        return Path(os.environ['LOCALAPPDATA']) / 'Spek' / 'studio-locals.json'
    return Path.home() / '.config' / 'Spek' / 'studio-locals.json'


def save_locals_root(root: Path, settings_file: Path | None = None) -> None:
    """Remember only the operator's chosen folder, outside canonical sources."""
    folder = validate_locals_root(root)
    dest = settings_file if settings_file is not None else _settings_file()
    dest = Path(dest)
    if dest.is_symlink():
        raise ValidationError('Le fichier de préférences Spek est un lien symbolique.')
    dest.parent.mkdir(parents=True, exist_ok=True)
    scratch = dest.with_suffix('.tmp')
    if scratch.is_symlink():
        raise ValidationError('Le fichier temporaire de préférences est un lien symbolique.')
    scratch.write_text(json.dumps({'locals_root': str(folder)}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    scratch.replace(dest)


def discover_locals_root(spek_root: Path, *, settings_file: Path | None = None,
                         env_root: str | None = None) -> Path | None:
    """Find an explicit or conventional collection path, not a Kristal template.

    Priority: environment variable, saved operator choice, common neighbour
    folders (including the Windows collection path used by Kristal-Manager).
    """
    repo = Path(spek_root).resolve()
    if env_root is None:
        env_root = os.environ.get('SPEK_LOCALS_ROOT')
    candidates: list[Path] = []
    if env_root:
        candidates.append(Path(env_root))
    config = settings_file if settings_file is not None else _settings_file()
    try:
        config = Path(config)
        if config.is_file() and not config.is_symlink() and config.stat().st_size < 4096:
            raw = json.loads(config.read_text(encoding='utf-8'))
            if isinstance(raw, dict) and isinstance(raw.get('locals_root'), str):
                candidates.append(Path(raw['locals_root']))
    except (OSError, ValueError, TypeError):
        pass
    candidates += [
        repo.parent / 'locals',
        repo.parent.parent / 'locals',
        repo.parent.parent / 'Kristal' / 'locals',
        Path('C:/mycode/Kristal/locals'),
    ]
    for candidate in candidates:
        try:
            return validate_locals_root(candidate)
        except (OSError, ValueError, ValidationError):
            continue
    return None


def _declared_slug(folder: Path) -> str | None:
    """Read metadata only. Never trust the folder name as proof of identity."""
    meta = folder / 'kristal.workspace.json'
    try:
        if meta.is_symlink() or not meta.is_file() or meta.stat().st_size > MAX_WORKSPACE_BYTES:
            return None
        obj = json.loads(meta.read_text(encoding='utf-8'))
        raw = obj.get('slug') if isinstance(obj, dict) else None
        return canonical_slug(raw) if isinstance(raw, str) else None
    except (OSError, ValueError, UnicodeError, ValidationError):
        return None


def find_local_kristal(locals_root: Path, slug: str) -> Path | None:
    """Return an EXACT identity match, without opening full canonical state.

    Searches direct child folders only. Ambiguity is rejected rather than
    silently preferring a match. Does not infer a recipe from paths or names.
    """
    root = validate_locals_root(locals_root)
    expected = canonical_slug(slug)
    matches: list[Path] = []
    try:
        children = sorted(root.iterdir(), key=lambda p: p.name.casefold())
    except OSError as exc:
        raise ValidationError('Impossible de consulter le dossier locals.') from exc
    for folder in children:
        if folder.is_symlink() or not folder.is_dir():
            continue
        if _declared_slug(folder) != expected:
            continue
        matches.append(folder.resolve())
        if len(matches) > 1:
            raise ValidationError('Plusieurs dossiers déclarent ce même Kristal dans locals. Choisis le dossier manuellement.')
    return matches[0] if matches else None
