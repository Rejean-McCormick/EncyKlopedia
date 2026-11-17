"""The launcher should diagnose an incomplete patch before importing the Studio."""
from __future__ import annotations
import importlib.machinery
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_launcher():
    path = ROOT / 'Spek_Template_Manager.pyw'
    loader = importlib.machinery.SourceFileLoader('spek_launcher_preflight', str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_complete_installation_passes_preflight():
    launcher = _load_launcher()
    assert launcher._verify_startup_files(ROOT) is True


def test_partial_semantik_patch_is_diagnosed(tmp_path):
    launcher = _load_launcher()
    pkg = tmp_path / 'spek'
    pkg.mkdir()
    for name in launcher._REQUIRED_STUDIO_MODULES:
        if name != 'local_kristals':
            (pkg / (name + '.py')).write_text('', encoding='utf-8')
    with pytest.raises(RuntimeError, match='spek/local_kristals.py'):
        launcher._verify_startup_files(tmp_path)


def test_diagnostic_check_valid_and_missing(tmp_path):
    loader = importlib.machinery.SourceFileLoader('spek_install_check', str(ROOT/'VERIFIER_INSTALLATION_SPEK.py'))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    assert module.check(ROOT) == []
    assert 'spek/local_kristals.py' in module.check(tmp_path)
