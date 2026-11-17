"""Source-grounded editorial review is read-only and never a publication assignment."""
from __future__ import annotations
import json
import hashlib
from pathlib import Path
from spek.source_reviews import read_source_reviews,compare_raw_state_snapshot
from spek.ai_proposals import read_proposals
from spek.composition_registry import read_registry
from spek.studio_workflow import inspect_kristal

ROOT=Path(__file__).resolve().parents[1]
COUNTS={'ai':360,'accounting':581,'aerospace':717,'aging':228,'agriculture':391}

def test_all_127_proposals_and_five_real_source_reviews():
    registry=read_registry(ROOT)
    props=read_proposals(ROOT,registry)
    rev=read_source_reviews(ROOT,props)
    assert len(props)==127
    assert set(rev)==set(COUNTS)
    assert registry['assignments']=={}
    for slug,r in rev.items():
        assert r['source']['assertion_occurrences']==COUNTS[slug]
        assert all(p['selection_status']=='NOT_SELECTED' for p in r['ordered_structural_sections'])
        assert all(p['publication_status']=='NOT_AUTHORIZED' for p in r['ordered_structural_sections'])
        assert sum(p['source_observation']['observed_assertion_occurrences'] for p in r['ordered_structural_sections'])==COUNTS[slug]
        assert len(set(j for p in r['ordered_structural_sections'] for j in p['source_observation']['source_positions_zero_based']))==COUNTS[slug]
        assert props[slug]['canonical_review_status']=='DEEP_SOURCE_INSPECTION_NOT_APPROVED'
    assert sum(COUNTS.values())==2277
    assert sum(1 for p in props.values() if p['canonical_review_status']=='AWAITING_CANONICAL_CONTENT')==122

def test_specific_templates_not_confused():
    registry=read_registry(ROOT)
    props=read_proposals(ROOT,registry)
    reviews=read_source_reviews(ROOT,props)
    a=[s['planned_template_id'] for s in reviews['ai']['ordered_structural_sections']]
    ag=[s['planned_template_id'] for s in reviews['agriculture']['ordered_structural_sections']]
    assert a!=ag
    assert 'double-entry-ledger' in [s['planned_template_id'] for s in reviews['accounting']['ordered_structural_sections']]
    assert 'mission-phase-map' in [s['planned_template_id'] for s in reviews['aerospace']['ordered_structural_sections']]
    assert 'functional-trajectory-map' in [s['planned_template_id'] for s in reviews['aging']['ordered_structural_sections']]

def test_digest_match_is_not_assignment_or_semantic_inference(tmp_path):
    reg=read_registry(ROOT)
    props=read_proposals(ROOT,reg)
    review=read_source_reviews(ROOT,props)['ai']
    path=tmp_path/review['source']['portable_state_relative_path']
    path.parent.mkdir(parents=True)
    path.write_bytes(b'a different local state')
    assert compare_raw_state_snapshot(tmp_path,review)=='DIFFERS_FROM_UPLOADED_SNAPSHOT'
    path.unlink()
    assert compare_raw_state_snapshot(tmp_path,review)=='SOURCE_FILE_NOT_FOUND'
    (tmp_path/'kristal.workspace.json').write_text(json.dumps({'slug':'kristal-ai','native_model':{'kind':'sample'}}),encoding='utf-8')
    observed=inspect_kristal(tmp_path,ROOT)
    assert observed['structure_review']['kristal_identity']=='ai'
    assert observed['assignment'] is None
    assert observed['assignment_state_pin_verified'] is False


def test_review_full_source_reference_positions_are_disjoint():
    reg=read_registry(ROOT);props=read_proposals(ROOT,reg)
    reviews=read_source_reviews(ROOT,props)
    for slug,r in reviews.items():
        pos=sorted(j for s in r['ordered_structural_sections'] for j in s['source_observation']['source_positions_zero_based'])
        assert pos==list(range(r['source']['assertion_occurrences']))
