"""Canonicalized catalog from the historical Manager report; no runtime editorial inference."""
from __future__ import annotations
import json
from pathlib import Path
import pytest
from spek.composition_registry import read_registry
from spek.ai_proposals import read_proposals, proposal_for_identity
from spek.source_reviews import read_source_reviews
from spek.studio_workflow import inspect_kristal
from spek.kristal_identity import canonical_slug
from spek.core import ValidationError

ROOT=Path(__file__).resolve().parents[1]


def test_all_127_canonical_ids_unique_and_grounded():
    p=read_proposals(ROOT,read_registry(ROOT))
    assert len(p)==127
    assert all(canonical_slug(k)==k for k in p)
    assert 'agriculture' in p and 'kristal-agriculture' not in p
    assert p['agriculture']['source_report_identity']=='kristal-agriculture'
    assert 'scolqc' in p and p['scolqc']['source_report_identity']=='Kristal-ScolQc'
    assert all(x['publication_eligible'] is False for x in p.values())


def test_legacy_prefix_is_read_only_compatibility_not_new_assignment():
    p=read_proposals(ROOT,read_registry(ROOT))
    assert proposal_for_identity(p,'agriculture') is p['agriculture']
    assert proposal_for_identity(p,'kristal-agriculture') is p['agriculture']
    assert proposal_for_identity(p,'not-registered') is None
    with pytest.raises(ValidationError):canonical_slug('kristal-')


def test_open_current_kristal_shows_proposal_and_review(tmp_path):
    (tmp_path/'kristal.workspace.json').write_text(json.dumps({
        'slug':'agriculture','title':'Kristal-Agriculture',
        'state_ref':'urn:kristal:agriculture:state',
        'native_model':{'kind':'agricultural_process_graph'}}),encoding='utf-8')
    result=inspect_kristal(tmp_path,ROOT)
    assert result['identity']=='agriculture'
    assert result['proposal']['kristal_identity']=='agriculture'
    assert result['structure_review']['kristal_identity']=='agriculture'
    assert result['assignment'] is None
    assert result['assignment_state_pin_verified'] is False


def test_legacy_workspace_does_not_rewrite_canonical_file(tmp_path):
    path=tmp_path/'kristal.workspace.json'
    path.write_text(json.dumps({'slug':'kristal-agriculture','title':'Kristal-Agriculture'}),encoding='utf-8')
    before=path.read_bytes()
    result=inspect_kristal(tmp_path,ROOT)
    assert result['identity']=='agriculture'
    assert result['declared_identity']=='kristal-agriculture'
    assert result['proposal'] is not None
    assert path.read_bytes()==before


def test_reviews_use_normalized_ids_without_changing_snapshot_fingerprints():
    p=read_proposals(ROOT,read_registry(ROOT))
    rev=read_source_reviews(ROOT,p)
    assert len(rev)==5 and set(rev)=={'ai','accounting','aerospace','aging','agriculture'}
    assert rev['agriculture']['source']['file_hash_is_not_verified_canonical_commitment'] is True


def test_ui_forces_preview_refresh_when_workspace_is_already_selected():
    text=(ROOT/'Spek_Template_Manager.pyw').read_text(encoding='utf-8')
    fn=text.split('    def _show_workspace(self):',1)[1].split('    def goto_assigned_recipe',1)[0]
    assert 'self.preview()' in fn
    assert "self.header_var.set('Mon travail · '" in fn
