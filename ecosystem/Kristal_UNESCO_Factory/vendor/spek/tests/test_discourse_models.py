"""Discourse contracts: determinism, privacy, no rhetorical inference.

All SemantiK words used here are manually supplied fixtures. This test module
never asserts that a relation or source is semantically verified.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import pytest
from spek.composition.engine import Library, resolve, render_html, render_markdown, materialize, dialogue_plan
from spek.composition.discourse import discourse_audit, validate_discourse
from spek.composition.source_binding import verify_v11_assertion_refs
from spek.core import ValidationError

ROOT = Path(__file__).resolve().parents[1]
EX = ROOT / 'docs' / 'COMPOSITION_RECURSIVE_VNEXT' / 'exemples'


def source(name):
    return json.loads((EX / name).read_text(encoding='utf-8'))


def test_all_62_templates_define_complete_discourse_models():
    lib=Library(ROOT / 'template_library')
    names=[n for n in lib.definitions if n.startswith('rhetorical.')]
    assert len(names)==62
    for ref in names:
        d=lib.get(ref)
        model=d['discourse_model']
        assert model['format']=='spek.discourse-model/1.0'
        assert [m['slot'] for m in model['moves']]==d['ordered_slots']
        assert validate_discourse(d)==tuple(d['presentation_policy'].get('paragraph_break_before_slots', [])) or d['presentation_policy']['layout_variant']!='flow'
        assert all(l['status']!='validated' for l in model['links'])
        assert model['cohesion']['rewrite_existing_phrases'] is False


def test_toulmin_roles_and_non_star_discourse_dag():
    lib=Library(ROOT / 'template_library')
    model=lib.get('rhetorical.toulmin-compact@1.0.0')['discourse_model']
    roles={m['slot']:m['function'] for m in model['moves']}
    assert roles['claim']=='position'
    assert roles['grounds']=='grounds'
    assert roles['bridge']=='explicit_semantik_transition'
    links={l['from_slot']:l for l in model['links']}
    assert links['backing']['to_slot']=='warrant'
    assert links['backing']['relation_function']=='supports'
    assert links['bridge']['to_slot']=='warrant'
    assert links['rebuttal']['relation_function']=='challenges'
    assert model['paragraph_groups']==[
        ['claim','grounds','bridge'],['warrant','backing'],['qualifier','rebuttal']]


def test_invalid_model_rejects_slot_omission_and_fake_connectives():
    lib=Library(ROOT/'template_library')
    original=lib.get('rhetorical.toulmin-compact@1.0.0')
    broken=copy.deepcopy(original)
    broken['discourse_model']['paragraph_groups'][0].remove('bridge')
    with pytest.raises(ValidationError):validate_discourse(broken)
    broken=copy.deepcopy(original)
    broken['discourse_model']['cohesion']['connectives']='auto_insert_en_effet'
    with pytest.raises(ValidationError):validate_discourse(broken)
    broken=copy.deepcopy(original)
    broken['discourse_model']['links'][0]['status']='verified'
    with pytest.raises(ValidationError):validate_discourse(broken)


def test_cyclic_discourse_relation_is_refused():
    lib=Library(ROOT/'template_library')
    d=copy.deepcopy(lib.get('rhetorical.toulmin-compact@1.0.0'))
    # Backing -> warrant; make warrant -> backing. Nothing may justify itself.
    link=next(l for l in d['discourse_model']['links'] if l['from_slot']=='warrant')
    link['to_slot']='backing'
    with pytest.raises(ValidationError, match='Cycle'):
        validate_discourse(d)


def test_explicit_transition_is_a_real_semantik_slot_not_auto_text():
    lib=Library(ROOT/'template_library')
    inst=source('toulmin-avec-liaison-FICTIVE.instance.json')
    r=resolve(inst,lib)
    assert len(r.leaves)==9
    plan=dialogue_plan(r,'fr')
    transition=next(x for x in plan['fields'] if x['realization_key']=='case.bridge')
    assert transition['discourse']['function']=='explicit_semantik_transition'
    assert transition['form']['force']=='PRESENT'
    assert transition['form']['block_kinds']==['utterance']
    assert transition['communication_request_ref']=='requests/case.bridge.json'
    assert transition['discourse']['connective_generated'] is False
    values=materialize(r, source('toulmin-avec-liaison-FICTIVE-realizations.json'),'fr')
    html=render_html(r,values)
    md=render_markdown(r,values)
    connective=values['case.bridge']
    assert html.count(connective)==1
    assert md.count(connective)==1
    assert html.count('<p>')==3
    assert html.index(values['case.proof.3']) < html.index(connective) < html.index(values['case.warrant'])
    assert 'toulmin.claim-grounds-warrant' not in html
    assert 'case.bridge' not in html
    assert '<h2>' not in html
    for value in values.values(): assert html.count(value)==1


def test_transition_missing_realization_fails_closed():
    inst=source('toulmin-avec-liaison-FICTIVE.instance.json')
    r=resolve(inst,Library(ROOT/'template_library'))
    bundle=source('toulmin-avec-liaison-FICTIVE-realizations.json')
    del bundle['entries']['case.bridge']
    with pytest.raises(ValidationError):materialize(r,bundle,'fr')


def test_private_disclosure_policy_no_ids_in_reader_output():
    inst=source('toulmin-avec-liaison-FICTIVE.instance.json')
    inst['bindings']['claim']['source_assertion_refs']=['KA1000603446628555400504199']
    r=resolve(inst,Library(ROOT/'template_library'))
    audit=discourse_audit(r)
    assert audit['connectors_generated']==0
    assert audit['content_selection_performed'] is False
    assert audit['declared_relations_unverified']>0
    assert 'KA1000603446628555400504199' not in json.dumps(audit)
    bundle=source('toulmin-avec-liaison-FICTIVE-realizations.json')
    html=render_html(r,materialize(r,bundle,'fr'))
    assert 'KA1000603446628555400504199' not in html
    assert 'requests/' not in html


def test_source_binding_existence_only_validated_on_explicit_v11_graph(tmp_path):
    lib=Library(ROOT/'template_library')
    inst=source('toulmin-avec-liaison-FICTIVE.instance.json')
    inst['bindings']['claim']['source_assertion_refs']=['KATEST100','KATEST101']
    r=resolve(inst,lib)
    graph=tmp_path/'v11.json'
    graph.write_text(json.dumps({'schema_version':'11.0','artifact_type':'kristal_semantic_graph',
        'assertions':[{'id':'KATEST100'},{'id':'KATEST101'}]}),encoding='utf-8')
    report=verify_v11_assertion_refs(r,graph)
    assert report['anchored_fields']==1 and report['anchored_references']==2
    assert report['meaning_or_relation_verified'] is False
    assert report['publication_authorized'] is False
    graph.write_text(json.dumps({'schema_version':'11.0','artifact_type':'kristal_semantic_graph',
        'assertions':[{'id':'KATEST100'}]}),encoding='utf-8')
    with pytest.raises(ValidationError,match='n’existent pas'):
        verify_v11_assertion_refs(r,graph)


def test_source_refs_reject_duplicate_and_invalid(tmp_path):
    original=source('toulmin-avec-liaison-FICTIVE.instance.json')
    leaf=original['bindings']['claim']
    leaf['source_assertion_refs']=['A','A']
    with pytest.raises(ValidationError):resolve(original,Library(ROOT/'template_library'))
    leaf['source_assertion_refs']=['C:\\private\\path']
    with pytest.raises(ValidationError):resolve(original,Library(ROOT/'template_library'))


def test_discourse_and_source_check_cli(capsys,tmp_path):
    from spek.cli import main
    instance=EX/'toulmin-avec-liaison-FICTIVE.instance.json'
    assert main(['discourse-audit','--instance',str(instance)])==0
    output=capsys.readouterr().out
    assert '0 connecteur créé' in output
    assert main(['discourse-audit','--instance',str(instance),'--format','json'])==0
    data=json.loads(capsys.readouterr().out)
    assert data['templates_with_discourse_model']==4
    assert all(x['semantic_truth_checked'] is False for x in data['nodes'])
