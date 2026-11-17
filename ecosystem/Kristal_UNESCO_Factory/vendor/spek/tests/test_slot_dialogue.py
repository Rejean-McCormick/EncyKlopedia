"""Spek décide le type de formulation par slot; SA reste seul réalisateur."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from spek.core import ValidationError
from spek.slot_dialogue import build_dialogue, compose_request, from_files, verify_result_shape
from spek.semantik_execution import realize_mapping
from test_semantik_execution import fake_environment
from test_semantik_transfer import make_fixture

ROOT = Path(__file__).resolve().parents[1]


def test_real_layout_contracts_cover_existing_articles():
    for filename in ['examples/article.json', 'bridge-article.json',
                     'examples/specialized/double-entry-ledger-article.json',
                     'examples/specialized/relation-network-article.json',
                     'examples/specialized/taxonomy-tree-article.json']:
        plan = from_files(ROOT / filename, ROOT / 'layouts', 'fr')
        assert plan['format'] == 'spek.slot-dialogue/1.0'
        assert plan['fields']
        assert all(x['locations'] and x['block_kinds'] for x in plan['fields'].values())
        assert plan['status'] == 'PREPARATION_PRIVEE_NON_APPROUVEE'


def test_field_forms_are_driven_by_layout_and_actual_kind(tmp_path):
    article, _ = make_fixture(tmp_path)
    plan = from_files(article, ROOT / 'layouts', 'fr')
    assert set(plan['fields']) == {'title','subtitle','abstract','heading.def',
                                    'unit.def','unit.ex','unit.ctx','unit.limit'}
    assert plan['fields']['unit.def']['intent'] == 'definition'
    assert plan['fields']['unit.limit']['intent'] == 'precaution'
    assert plan['fields']['heading.def']['intent'] == 'titre_de_section'


def test_request_adds_only_surface_constraints_and_keeps_facts(tmp_path):
    article, mapping = make_fixture(tmp_path)
    plan = from_files(article, ROOT / 'layouts', 'fr')
    pairs = json.loads(mapping.read_text())['bindings']
    req = json.loads((mapping.parent / pairs['unit.limit']['request']).read_text())
    original = copy.deepcopy(req)
    updated = compose_request(req, plan['fields']['unit.limit'], language='fr')
    assert req == original
    assert updated['semantic_graph'] == req['semantic_graph']
    assert updated['obligations'] == req['obligations']
    assert updated['runtime_selector'] == req['runtime_selector']
    assert updated['constraints']['opening_policy'] == 'forbidden'
    assert updated['constraints']['closing_policy'] == 'forbidden'
    assert updated['constraints']['allowed_block_kinds'] == ['utterance']


def test_question_requires_explicit_ask_not_assert():
    field = {'intent': 'question', 'force': 'ASK', 'block_kinds': ['question'], 'max_length': 500}
    req = {'schema_version':'1.0', 'semantic_graph':{},
           'obligations':[{'obligation_id':'o1', 'semantic_refs':['s1'], 'force':'ASSERT'}],
           'context':{'target_language':'fr'}, 'constraints':{'allowed_block_kinds':['question']}}
    with pytest.raises(ValidationError, match='ASK'):
        compose_request(req, field, language='fr')
    req['obligations'][0]['force'] = 'ASK'
    updated = compose_request(req, field, language='fr')
    assert updated['obligations'][0]['force'] == 'ASK'
    assert updated['constraints']['allowed_block_kinds'] == ['question']


def test_contradictory_force_or_block_rejected():
    field = {'force':'PRESENT','block_kinds':['utterance'], 'max_length':1000}
    req = {'schema_version':'1.0', 'semantic_graph':{},
           'obligations':[{'force':'ASK'}], 'context':{'target_language':'fr'},
           'constraints':{'allowed_block_kinds':['utterance']}}
    with pytest.raises(ValidationError, match='question'):
        compose_request(req, field, language='fr')
    req['obligations'][0]['force']='PRESENT'
    req['constraints']['allowed_block_kinds']=['question']
    with pytest.raises(ValidationError, match='interdit'):
        compose_request(req, field, language='fr')
    req['constraints']['allowed_block_kinds']=['utterance']
    req['constraints']['opening_policy']='required'
    with pytest.raises(ValidationError, match='Ouverture'):
        compose_request(req, field, language='fr')


def test_reused_key_for_incompatible_shapes_is_rejected(tmp_path):
    article, _ = make_fixture(tmp_path)
    obj = json.loads(article.read_text())
    obj['units'][0]['realization_key'] = obj['article']['title_key']
    layouts = [json.loads(p.read_text()) for p in sorted((ROOT / 'layouts').glob('*.json'))]
    with pytest.raises(ValidationError, match='contradictoires'):
        build_dialogue(obj, layouts, language='fr')


def test_semantik_wrong_kind_refused_even_if_text_present():
    field = {'block_kinds':['question']}
    req = {'constraints':{'allowed_block_kinds':['question']}}
    with pytest.raises(ValidationError, match='non conforme'):
        verify_result_shape({'blocks':[{'kind':'utterance','text':'Texte.'}]}, field, request=req)


def test_execution_passes_slot_constraints_to_semantik_without_changing_sources(tmp_path):
    article, mapping = make_fixture(tmp_path)
    architect, runtime = fake_environment(tmp_path)
    bindings = json.loads(mapping.read_text())['bindings']
    old_requests = {k:(mapping.parent / v['request']).read_bytes() for k,v in bindings.items()}
    source_results = {}
    for key, pair in bindings.items():
        request = json.loads((mapping.parent / pair['request']).read_text())
        result = json.loads((mapping.parent / pair['result']).read_text())
        source_results[request['request_id']] = result

    def fake_renderer(cmd, **kwargs):
        req = json.loads(Path(cmd[-1]).read_text())
        assert req['constraints']['opening_policy'] == 'forbidden'
        assert req['constraints']['closing_policy'] == 'forbidden'
        assert req['constraints']['allowed_block_kinds'] == ['utterance']
        return SimpleNamespace(returncode=0, stdout=json.dumps(source_results[req['request_id']]), stderr='')

    with patch('spek.semantik_execution.subprocess.run', side_effect=fake_renderer):
        result = realize_mapping(article, mapping, architect, runtime, layouts=ROOT/'layouts')
    assert result['status'] == 'PRIVATE_IMPORTED_NOT_QUALIFIED'
    for key, value in bindings.items():
        assert (mapping.parent / value['request']).read_bytes() == old_requests[key]
