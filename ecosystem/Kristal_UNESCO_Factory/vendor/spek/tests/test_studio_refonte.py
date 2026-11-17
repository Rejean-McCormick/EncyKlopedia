"""The new operator UI remains read-only and never infers or approves templates."""
from pathlib import Path
from spek.ai_proposals import read_proposals
from spek.composition_registry import read_registry
from spek.studio_view_model import resolve_display, filter_catalog, template_label

ROOT = Path(__file__).resolve().parents[1]


def _catalog():
    return read_proposals(ROOT, read_registry(ROOT))


def test_catalog_exact_127_and_search_no_inference():
    proposals = _catalog()
    assert len(proposals) == 127
    assert 'agriculture' in filter_catalog(proposals, 'AgRiCuLtUrE')
    assert filter_catalog(proposals, 'a completely unknown kristal') == []


def test_browse_cannot_become_approved_or_local():
    model = resolve_display(_catalog(), 'anthropology')
    assert model['proposal'] is not None
    assert model['publication_approved'] is False
    assert model['has_local_source'] is False
    assert model['source_verified'] is False
    assert model['sections']


def test_local_snapshot_requires_review_and_exact_match():
    p = _catalog()
    raw = {'identity': 'agriculture', 'title': 'Kristal-Agriculture',
           'structure_review': {'ordered_structural_sections': [
               {'heading': 'Sol', 'planned_template_id': 'agroecosystem-network'}]},
           'source_snapshot_comparison': 'MISMATCH'}
    bad = resolve_display(p, 'agriculture', raw)
    assert bad['has_local_source']
    assert bad['source_verified'] is False
    assert bad['sections'][0]['title'] == 'Sol'
    raw['source_snapshot_comparison'] = 'MATCHES_UPLOADED_SNAPSHOT'
    good = resolve_display(p, 'agriculture', raw)
    assert good['source_verified'] is True
    assert good['publication_approved'] is False
    other = resolve_display(p, 'ai', raw)
    assert other['has_local_source'] is False
    assert other['source_verified'] is False


def test_label_is_display_only_and_does_not_change_template():
    assert template_label('concept-card') == 'Fiche conceptuelle'
    assert template_label('unknown-custom-id') == 'Unknown custom id'


def test_no_internal_hash_or_path_in_main_view_model():
    model = resolve_display(_catalog(), 'agriculture')
    assert 'source_hash' not in model
    assert 'raw_path' not in model
    assert 'canonical_approved' not in model
