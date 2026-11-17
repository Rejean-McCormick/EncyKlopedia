"""The locals finder must check declared identity, never infer templates or open data."""
import json
from pathlib import Path
import pytest

from spek.core import ValidationError
from spek.local_kristals import (
    discover_locals_root, find_local_kristal, save_locals_root,
    validate_locals_root,
)


def _make_kristal(locals_root: Path, name: str, slug: str, *, title: str = 'Example') -> Path:
    directory = locals_root / name
    directory.mkdir()
    (directory / 'kristal.workspace.json').write_text(
        json.dumps({'slug':slug, 'title': title}), encoding='utf-8')
    return directory


def test_lookup_matches_declared_normalized_slug(tmp_path):
    root = tmp_path / 'locals'
    root.mkdir()
    expected = _make_kristal(root, 'Kristal-Agriculture', 'agriculture')
    assert find_local_kristal(root, 'agriculture') == expected
    assert find_local_kristal(root, 'kristal-agriculture') == expected
    assert find_local_kristal(root, 'anthropology') is None


def test_lookup_does_not_trust_folder_name_or_infer(tmp_path):
    root = tmp_path / 'locals'
    root.mkdir()
    _make_kristal(root, 'Kristal-Agriculture', 'aerospace')
    assert find_local_kristal(root, 'agriculture') is None
    assert find_local_kristal(root, 'aerospace') == root / 'Kristal-Agriculture'


def test_lookup_does_not_enter_nested_folders(tmp_path):
    root = tmp_path / 'locals'
    root.mkdir()
    child = root / 'workspace' / 'Kristal-Agriculture'
    child.mkdir(parents=True)
    (child / 'kristal.workspace.json').write_text('{"slug":"agriculture"}', encoding='utf-8')
    assert find_local_kristal(root, 'agriculture') is None


def test_lookup_legacy_identity_and_ambiguous_duplicates(tmp_path):
    root = tmp_path / 'locals'
    root.mkdir()
    _make_kristal(root, 'Kristal-Agriculture', 'kristal-agriculture')
    assert find_local_kristal(root, 'agriculture') is not None
    _make_kristal(root, 'AgricultureBackup', 'agriculture')
    with pytest.raises(ValidationError, match='Plusieurs dossiers'):
        find_local_kristal(root, 'agriculture')


def test_missing_or_corrupt_workspace_is_not_accepted(tmp_path):
    root = tmp_path / 'locals'
    root.mkdir()
    empty = root / 'Kristal-Agriculture'
    empty.mkdir()
    assert find_local_kristal(root, 'agriculture') is None
    (empty / 'kristal.workspace.json').write_text('{not-json', encoding='utf-8')
    assert find_local_kristal(root, 'agriculture') is None


def test_symlink_folder_skipped(tmp_path):
    root = tmp_path / 'locals'
    root.mkdir()
    external = tmp_path / 'external'
    external.mkdir()
    _make_kristal(external, 'Kristal-Agriculture', 'agriculture')
    try:
        (root / 'Kristal-Agriculture').symlink_to(external / 'Kristal-Agriculture', target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip('Symlinks unavailable')
    assert find_local_kristal(root, 'agriculture') is None
    with pytest.raises(ValidationError):
        validate_locals_root(root / 'Kristal-Agriculture')


def test_configured_root_remembered_but_never_created_in_locals(tmp_path):
    repo = tmp_path / 'project' / 'Spek'
    repo.mkdir(parents=True)
    root = tmp_path / 'collection'
    root.mkdir()
    settings = tmp_path / 'private-settings.json'
    save_locals_root(root, settings)
    assert discover_locals_root(repo, settings_file=settings, env_root='') == root
    assert json.loads(settings.read_text(encoding='utf-8'))['locals_root'] == str(root)
    assert list(root.iterdir()) == []


def test_auto_neighbor_root_fallback(tmp_path):
    repo = tmp_path / 'Kristal' / 'Spek'
    repo.mkdir(parents=True)
    root = tmp_path / 'Kristal' / 'locals'
    root.mkdir()
    assert discover_locals_root(repo, settings_file=tmp_path/'missing.json', env_root='') == root


def test_invalid_slug_rejected_before_file_search(tmp_path):
    root = tmp_path / 'locals'
    root.mkdir()
    for bad in ('', '../agriculture', 'agriculture/../x', ' agriculture'):
        with pytest.raises(ValidationError):
            find_local_kristal(root, bad)
