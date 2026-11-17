"""Local CLI/GUI adapter for vNext. Never publishes or selects facts."""
from __future__ import annotations
import json
from pathlib import Path

from spek.core import ValidationError
from .engine import Library, resolve, dialogue_plan, materialize, render_html, render_markdown


def read_instance(path: Path) -> dict:
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
        raise ValidationError('Instance absente, lien symbolique ou trop volumineuse')
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, OSError) as exc:
        raise ValidationError('Instance JSON invalide') from exc


def load(root: Path, instance_path: Path):
    return resolve(read_instance(instance_path), Library(Path(root) / 'template_library'))


def preview(root: Path, instance_path: Path, realizations_path: Path, language: str,
            out: Path, *, title: str='Composition — aperçu privé') -> dict:
    """Write private reading artifacts only to a NEW directory outside repo.

    This API never calls GitHub, validates C1/C2/C3, or asserts qualification.
    """
    root = Path(root).resolve()
    out = Path(out).absolute()
    if out.exists() or out.is_symlink() or out == root or out.is_relative_to(root):
        raise ValidationError('Sortie privée : nouveau dossier requis hors du dépôt Spek')
    bundle = read_instance(realizations_path)
    resolved = load(root, instance_path)
    values = materialize(resolved, bundle, language)
    html = render_html(resolved, values, title=title, language=language)
    md = render_markdown(resolved, values, title=title)
    # Do not include internal source keys or request refs in any output files.
    out.mkdir(parents=True, exist_ok=False)
    try:
        (out / 'index.html').write_text(html, encoding='utf-8')
        (out / 'Brouillon-prive.md').write_text(md, encoding='utf-8')
    except OSError:
        import shutil
        shutil.rmtree(out)
        raise
    return {'page': str(out/'index.html'), 'markdown': str(out/'Brouillon-prive.md'),
            'status':'private_not_approved', 'leaves':len(resolved.leaves)}


def prepare_dialogue(root: Path, instance_path: Path, language: str,
                     requests_dir: Path | None = None) -> dict:
    resolved = load(root, instance_path)
    requests = None
    if requests_dir is not None:
        directory = Path(requests_dir).resolve()
        if not directory.is_dir() or directory.is_symlink():
            raise ValidationError('Dossier de requêtes SemantiK absent')
        requests = {}
        for leaf in resolved.leaves:
            filename = Path(leaf.request_ref).name
            path = directory / filename
            if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(directory):
                raise ValidationError('Requête sémantique manquante')
            requests[leaf.request_ref] = read_instance(path)
    return dialogue_plan(resolved, language, requests=requests)
