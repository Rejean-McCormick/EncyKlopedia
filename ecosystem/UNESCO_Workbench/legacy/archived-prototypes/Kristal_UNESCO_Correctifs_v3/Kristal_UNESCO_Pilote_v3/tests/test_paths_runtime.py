from __future__ import annotations
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from project_paths import SEMANTIK_PROJECT, KRISTAL_ROOT, ENCYKLOPEDIA_ROOT, runtime_paths, resolve_semantik_project
from gf_setup import probe_existing_pgf, discover_gf


def test_defaults_match_verified_diagnostic_paths():
    assert str(KRISTAL_ROOT).endswith('Kristal')
    assert 'SemantiK_Architect' in str(SEMANTIK_PROJECT)
    assert str(ENCYKLOPEDIA_ROOT).endswith('EncyKlopedia')
    data = runtime_paths(SEMANTIK_PROJECT)
    assert data['pgf_fr'].replace('\\','/').endswith('/runtime/konstellation-fr-3/grammar.pgf')
    assert data['pgf_adapter'].replace('\\','/').endswith('/src/semantik_architect/adapters/realization/gf/pgf_runtime.py')


def test_workspace_or_project_resolve_same_existing_tree(tmp_path):
    ws = tmp_path / 'SemantiK_Architect'
    sa = ws / 'SemantiK_Architect'
    (sa / 'src/semantik_architect').mkdir(parents=True)
    assert resolve_semantik_project(ws) == sa
    assert resolve_semantik_project(sa) == sa
    assert runtime_paths(ws)['pgf_fr'] == runtime_paths(sa)['pgf_fr']


def test_existing_runtime_is_not_compiler(tmp_path):
    ws = tmp_path / 'SA'
    sa = ws / 'SemantiK_Architect'
    (sa / 'src/semantik_architect').mkdir(parents=True)
    artifact = sa / 'runtime/konstellation-fr-3/grammar.pgf'
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b'placeholder' * 30)
    # A PGF artifact is never offered as a gf.exe binary.
    exe, attempts = discover_gf(str(artifact), sa)
    assert exe is None
    assert attempts


def test_detect_compiler_in_local_gf_wordbench(tmp_path):
    ws = tmp_path / 'workspace'
    sa = ws / 'SemantiK_Architect'
    (sa / 'src/semantik_architect').mkdir(parents=True)
    wordbench = ws / 'GF_Wordbench/bin'
    wordbench.mkdir(parents=True)
    compiler = wordbench / 'gf.exe'
    compiler.write_bytes(b'fixture')
    actual, traces = discover_gf('', sa)
    assert actual == str(compiler.resolve())
    assert traces


def test_probe_reports_missing_binding_without_claiming_realization(tmp_path):
    python = tmp_path / 'python.exe'
    python.touch()
    artifact = tmp_path / 'grammar.pgf'
    artifact.write_bytes(b'A' * 150)
    with patch('gf_setup.subprocess.run', return_value=SimpleNamespace(returncode=1, stderr="ModuleNotFoundError: No module named 'pgf'", stdout='')):
        report = probe_existing_pgf(python, artifact)
    assert not report['loaded']
    assert report['scope'] == 'existing_konstellation_runtime_only'
    assert 'ModuleNotFoundError' in report['error']


def test_probe_success_proves_only_existing_pgf(tmp_path):
    python = tmp_path / 'python.exe'
    python.touch()
    artifact = tmp_path / 'grammar.pgf'
    artifact.write_bytes(b'A' * 150)
    with patch('gf_setup.subprocess.run', return_value=SimpleNamespace(returncode=0, stdout='{"loaded": true, "concrete_languages": ["KonstellationFre"]}\n', stderr='')) as mocked:
        report = probe_existing_pgf(python, artifact)
    assert report['loaded'] is True
    assert report['concrete_languages'] == ['KonstellationFre']
    assert report['scope'] == 'existing_konstellation_runtime_only'
    called = mocked.call_args.args[0]
    assert called[0] == str(python)
    assert called[1] == '-P'
    assert str(artifact) in called


def test_probe_times_out(tmp_path):
    python = tmp_path / 'python.exe'
    python.touch()
    artifact = tmp_path / 'grammar.pgf'
    artifact.write_bytes(b'A' * 150)
    with patch('gf_setup.subprocess.run', side_effect=subprocess.TimeoutExpired('python', 10)):
        report = probe_existing_pgf(python, artifact, timeout=10)
    assert not report['loaded']
    assert '10 secondes' in report['error']
