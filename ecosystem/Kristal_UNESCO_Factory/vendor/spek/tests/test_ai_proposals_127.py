"""Read-only AI editorial proposal catalog from Manager's 127-Kristal report."""
import json
from pathlib import Path

import pytest

from spek.ai_proposals import proposal_for_identity, read_proposals
from spek.composition_registry import read_registry
from spek.core import ValidationError
from spek.studio_workflow import inspect_kristal

ROOT = Path(__file__).resolve().parents[1]


def test_127_proposals_are_real_registry_references_and_not_approvals():
    registry = read_registry(ROOT)
    proposals = read_proposals(ROOT, registry)
    assert len(proposals) == 127
    assert registry['assignments'] == {}
    assert all(p['publication_eligible'] is False for p in proposals.values())
    assert all(p['editorial_status'].endswith('_NOT_APPROVED') for p in proposals.values())
    assert all(s['selected_assertion_ids'] == [] and not s['required_slots_fulfilled']
               for p in proposals.values() for s in p['ordered_sections'])


def test_exact_identity_lookup_only():
    proposals = read_proposals(ROOT, read_registry(ROOT))
    assert proposal_for_identity(proposals, 'ai')['kristal_identity'] == 'ai'
    assert proposal_for_identity(proposals, 'kristal-ai')['kristal_identity'] == 'ai'
    assert proposal_for_identity(proposals, 'Kristal-AI')['kristal_identity'] == 'ai'
    assert proposal_for_identity(proposals, 'missing') is None


def test_inspect_kristal_shows_proposal_without_creating_assignment(tmp_path):
    workspace = tmp_path / 'kristal.workspace.json'
    workspace.write_text(json.dumps({'slug':'kristal-ai','title':'Kristal-AI','state_ref':'urn:kristal:ai:state',
                                     'native_model':{'kind':'test-model'}}),encoding='utf-8')
    observed = inspect_kristal(tmp_path, ROOT)
    assert observed['proposal']['primary_composition_id'] == 'arketype-modele-multiplexe'
    assert observed['identity'] == 'ai'
    assert observed['declared_identity'] == 'kristal-ai'
    assert observed['assignment'] is None
    assert observed['assignment_state_pin_verified'] is False


def test_catalog_fail_closed_if_proposal_claims_publication(tmp_path):
    registry = read_registry(ROOT)
    src = ROOT / 'template_library' / 'wiki' / 'kristal-ai-proposals.json'
    dest = tmp_path / 'template_library' / 'wiki' / 'kristal-ai-proposals.json'
    dest.parent.mkdir(parents=True)
    obj=json.loads(src.read_text(encoding='utf-8'))
    obj['proposals']['ai']['publication_eligible']=True
    dest.write_text(json.dumps(obj),encoding='utf-8')
    with pytest.raises(ValidationError):
        read_proposals(tmp_path,registry)
