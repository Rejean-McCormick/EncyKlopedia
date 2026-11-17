"""No-runtime proof that Spek accepts only complete, explicit SA transfer pairs."""
import hashlib
import json
from pathlib import Path

import pytest

from spek.core import ValidationError
from spek.semantik_transfer import _required_keys, transfer


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def make_fixture(tmp_path: Path):
    article = {
        'format': 'kristal.layout-article-source/0.1',
        'article': {'id': 'urn:spek:semantik-transfer-test', 'title_key': 'title',
                    'subtitle_key': 'subtitle', 'abstract_key': 'abstract'},
        'source': {'origin': 'external_projection', 'state_ref': None, 'state_commitment': None,
                   'artifact_refs': [], 'scientific_review': 'not_submitted', 'disclosure': 'local_demo_only',
                   'language_review': {'fr': 'not_submitted'}},
        'units': [
            {'id': 'u.def', 'kind': 'definition', 'realization_key': 'unit.def', 'epistemic_status': 'method', 'evidence_refs': []},
            {'id': 'u.ex', 'kind': 'example', 'realization_key': 'unit.ex', 'epistemic_status': 'method', 'evidence_refs': []},
            {'id': 'u.ctx', 'kind': 'context', 'realization_key': 'unit.ctx', 'epistemic_status': 'method', 'evidence_refs': []},
            {'id': 'u.limit', 'kind': 'qualification', 'realization_key': 'unit.limit', 'epistemic_status': 'limitation', 'evidence_refs': []},
        ],
        'evidence': [],
        'sections': [{'id': 'definition', 'layout': 'concept-card', 'heading_key': 'heading.def',
                      'slots': {'definition': 'u.def', 'examples': ['u.ex'], 'context': 'u.ctx', 'limits': 'u.limit'}}]
    }
    doc_dir = tmp_path / 'source'
    article_path = doc_dir / 'article.json'
    dump(article_path, article)
    mapping = {'format': 'spek.semantik-transfer/1.0', 'language': 'fr', 'bindings': {}}
    directory = tmp_path / 'inputs'
    for n, key in enumerate(sorted(_required_keys(article)), 1):
        rid = f'req:{n}'
        sid = f'statement:{n}'
        oid = f'obligation:{n}'
        req = {
            'schema_version': '1.0', 'request_id': rid,
            'semantic_graph': {'graph_id': f'graph:{n}', 'nodes': [],
                               'statements': [{'id': sid, 'predicate_ref': 'local-predicate:test', 'arguments': [],
                                               'polarity': 'positive', 'source_refs': [f'source:{n}']}]},
            'obligations': [{'obligation_id': oid, 'semantic_refs': [sid], 'force': 'PRESENT',
                             'ordering': 'FREE', 'source_refs': [f'source:{n}']}],
            'context': {'target_language': 'fr', 'target_locale': 'fr-CA'},
            'constraints': {'allowed_block_kinds': ['utterance'], 'output_format': 'structured'},
            'capability_profile': 'test-profile-1',
            'runtime_selector': {'runtime_set_id': 'runtime-qualified-outside-spek-1'},
        }
        res = {
            'schema_version': '1.0', 'language': 'fr', 'locale': 'fr-CA',
            'blocks': [{'block_id': f'block:{n}', 'kind': 'utterance', 'text': f'Phrase {n}.', 'obligation_ids': [oid]}],
            'plain_text': f'Phrase {n}.',
            'coverage': [{'obligation_id': oid, 'block_ids': [f'block:{n}'], 'realization_unit_ids': [f'unit:{n}']}],
            'source_refs': [f'source:{n}'],
            'runtime': {'sa_version': '1.3.0-alpha.2', 'runtime_set_id': 'runtime-qualified-outside-spek-1',
                        'sa_gf_contract_version': '1.0', 'capability_profile': 'test-profile-1'},
        }
        material = json.dumps(res, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
        res['deterministic_result_id'] = 'sha256:' + hashlib.sha256(material).hexdigest()
        res['operational'] = {'elapsed_ms': 1.5}
        req_name, res_name = f'requests/{n}.json', f'results/{n}.json'
        dump(directory / req_name, req)
        dump(directory / res_name, res)
        mapping['bindings'][key] = {'request': req_name, 'result': res_name}
    mapping_path = directory / 'mapping.json'
    dump(mapping_path, mapping)
    return article_path, mapping_path


def test_private_transfer_works(tmp_path):
    article, mapping = make_fixture(tmp_path)
    first_input = mapping.read_bytes()
    out = tmp_path / 'private-result'
    report = transfer(article, mapping, out)
    assert report['realization_count'] == 8
    assert report['status'] == 'PRIVATE_IMPORTED_NOT_QUALIFIED'
    saved = json.loads((out / 'realizations.json').read_text(encoding='utf-8'))
    assert len(saved['entries']) == 8
    assert all(entry['fr']['status'] == 'fixture' and entry['fr']['channel'] == 'semantik_architect'
               for entry in saved['entries'].values())
    assert json.loads((out / 'transfer-report.json').read_text(encoding='utf-8'))['publication_eligible'] is False
    assert mapping.read_bytes() == first_input
    with pytest.raises(ValidationError):
        transfer(article, mapping, out)  # no output overwrite


def test_missing_explicit_binding_refused(tmp_path):
    article, mapping = make_fixture(tmp_path)
    data = json.loads(mapping.read_text(encoding='utf-8'))
    del data['bindings']['title']
    dump(mapping, data)
    with pytest.raises(ValidationError, match='chaque clé'):
        transfer(article, mapping, tmp_path / 'out')


def test_result_tampering_refused(tmp_path):
    article, mapping = make_fixture(tmp_path)
    data = json.loads(mapping.read_text(encoding='utf-8'))
    p = mapping.parent / data['bindings']['title']['result']
    result = json.loads(p.read_text(encoding='utf-8'))
    result['plain_text'] = 'Texte inventé.'
    dump(p, result)
    with pytest.raises(ValidationError, match='texte ne correspond'):
        transfer(article, mapping, tmp_path / 'out')


def test_unbound_provenance_refused(tmp_path):
    article, mapping = make_fixture(tmp_path)
    data = json.loads(mapping.read_text(encoding='utf-8'))
    p = mapping.parent / data['bindings']['title']['result']
    result = json.loads(p.read_text(encoding='utf-8'))
    result['source_refs'] = ['unrelated:source']
    dump(p, result)
    with pytest.raises(ValidationError, match='traçabilité'):
        transfer(article, mapping, tmp_path / 'out')


def test_invalid_coverage_refused(tmp_path):
    article, mapping = make_fixture(tmp_path)
    data = json.loads(mapping.read_text(encoding='utf-8'))
    p = mapping.parent / data['bindings']['title']['result']
    result = json.loads(p.read_text(encoding='utf-8'))
    result['coverage'] = []
    dump(p, result)
    with pytest.raises(ValidationError, match='couverture'):
        transfer(article, mapping, tmp_path / 'out')


def test_path_traversal_refused(tmp_path):
    article, mapping = make_fixture(tmp_path)
    data = json.loads(mapping.read_text(encoding='utf-8'))
    data['bindings']['title']['result'] = '../outside.json'
    dump(mapping, data)
    with pytest.raises(ValidationError, match='chemin relatif'):
        transfer(article, mapping, tmp_path / 'out')


def test_prepare_mapping_only_explicit_keys(tmp_path):
    from spek.semantik_transfer import prepare_mapping
    article, _ = make_fixture(tmp_path)
    dest = tmp_path / 'mapping-skeleton.json'
    result = prepare_mapping(article, 'fr', dest)
    assert result['required_keys'] == 8
    doc = json.loads(dest.read_text(encoding='utf-8'))
    assert set(doc['bindings']) == _required_keys(json.loads(article.read_text(encoding='utf-8')))
    assert all(set(item) == {'request','result'} for item in doc['bindings'].values())
    assert not any((dest.parent / v['request']).exists() for v in doc['bindings'].values())
    with pytest.raises(ValidationError):
        prepare_mapping(article, 'fr', dest)
