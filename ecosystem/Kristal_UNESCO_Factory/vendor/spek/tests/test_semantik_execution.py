"""SemantiK execution never guesses requests or falls back to raw source content."""
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from spek.core import ValidationError
from spek.semantik_execution import realize_mapping
from test_semantik_transfer import make_fixture, dump


def fake_environment(tmp_path):
    architect = tmp_path / 'SemantiK-Architect'
    (architect / 'src' / 'semantik_architect' / 'adapters' / 'inbound' / 'cli').mkdir(parents=True)
    (architect / 'src' / 'semantik_architect' / 'adapters' / 'inbound' / 'cli' / 'main.py').write_text('# fixture', encoding='utf-8')
    runtime = architect / 'runtime'
    runtime.mkdir()
    return architect, runtime


def test_requests_only_semantik_results_are_accepted(tmp_path):
    article, mapping = make_fixture(tmp_path)
    architect, runtime = fake_environment(tmp_path)
    spec = json.loads(mapping.read_text(encoding='utf-8'))
    source_results = {}
    for pair in spec['bindings'].values():
        r = json.loads((mapping.parent / pair['request']).read_text())
        val = json.loads((mapping.parent / pair['result']).read_text())
        source_results[r['request_id']] = val

    def sa_render(command, **kwargs):
        assert 'semantik_architect.adapters.inbound.cli.main' in command
        assert str(runtime) in command
        req = json.loads(Path(command[-1]).read_text(encoding='utf-8'))
        return SimpleNamespace(returncode=0, stdout=json.dumps(source_results[req['request_id']]), stderr='')

    with patch('spek.semantik_execution.subprocess.run', side_effect=sa_render) as proc:
        result = realize_mapping(article, mapping, architect, runtime)
    assert proc.call_count == len(spec['bindings'])
    assert result['status'] == 'PRIVATE_IMPORTED_NOT_QUALIFIED'
    assert result['source'] == 'semantik_architect_runtime'
    data = json.loads(Path(result['realizations']).read_text(encoding='utf-8'))
    assert data['entries']['title']['fr']['text'].startswith('Phrase')
    assert not (mapping.parent / 'rendered').exists()


def test_missing_or_invalid_request_fails_closed(tmp_path):
    article, mapping = make_fixture(tmp_path)
    architect, runtime = fake_environment(tmp_path)
    spec = json.loads(mapping.read_text(encoding='utf-8'))
    key = next(iter(spec['bindings']))
    (mapping.parent / spec['bindings'][key]['request']).unlink()
    with patch('spek.semantik_execution.subprocess.run') as proc:
        with pytest.raises(ValidationError):
            realize_mapping(article, mapping, architect, runtime)
    proc.assert_not_called()


def test_runtime_error_does_not_create_raw_text_fallback(tmp_path):
    article, mapping = make_fixture(tmp_path)
    architect, runtime = fake_environment(tmp_path)
    with patch('spek.semantik_execution.subprocess.run',
               return_value=SimpleNamespace(returncode=2,stdout='',stderr='PGF missing')):
        with pytest.raises(ValidationError,match='Aucune phrase de remplacement créée'):
            realize_mapping(article, mapping, architect, runtime)


def test_no_request_guessing_from_kristal(tmp_path):
    architect, runtime = fake_environment(tmp_path)
    # A local Kristal is not a valid article or explicit SemantiK mapping.
    with pytest.raises((ValidationError, FileNotFoundError)):
        realize_mapping(tmp_path, tmp_path, architect, runtime)
