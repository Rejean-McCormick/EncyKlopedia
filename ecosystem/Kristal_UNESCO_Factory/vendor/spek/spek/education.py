"""Strict, offline educational presentation boundary (Spek v0.5).

Consumes only pre-filtered, operator-supplied public/demo projections. This is
NOT an Ekole raw-repository crawler or a Kompose access-control implementation.
It cannot authorize classroom use, distribute private data, or publish a site.
"""
from __future__ import annotations
import copy
from .core import ValidationError, digest, expect, safe_id, SEMANTIC_FORMAT, REALIZATION_FORMAT

FORMAT = 'spek.educational-projection/1'
ALLOWED_DATA_CLASS = {'public_demo', 'public_released_excerpt'}


def exact(obj: object, required: set[str], allowed: set[str], location: str) -> dict:
    expect(isinstance(obj, dict), f'{location} must be an object')
    expect(required <= set(obj), f'Missing fields at {location}: {sorted(required-set(obj))}')
    expect(set(obj) <= allowed, f'Forbidden/unrecognized fields at {location}: {sorted(set(obj)-allowed)}')
    return obj


def _text(value, label, max_length=5000):
    expect(isinstance(value, str) and 0 < len(value.strip()) <= max_length, f'Missing/invalid {label}')
    return value


def import_educational(data: dict, adapter: str) -> tuple[dict, dict]:
    """Return normal Spek article + realizations, without ever treating upstream
    display permissions as publication rights or canon validation.

    Input MUST be intentionally prepared for this boundary; unfiltered upstream
    JSON and unrestricted/teacher/session/learner records are rejected.
    """
    expect(adapter in {'ekole', 'kompose'}, 'Unsupported educational source')
    exact(data, {'format', 'producer', 'complete', 'scope', 'document', 'realizations'},
          {'format', 'producer', 'complete', 'scope', 'document', 'realizations', 'selection'}, 'projection')
    expect(data['format'] == FORMAT and data['producer'] == adapter and data['complete'] is True,
           'Wrong producer, version or incomplete projection')
    scope = exact(data['scope'],
        {'audience', 'data_classification', 'export_status', 'dataset_ref', 'reader_policy_ref', 'pedagogical_review'},
        {'audience', 'data_classification', 'export_status', 'dataset_ref', 'reader_policy_ref', 'pedagogical_review'},
        'scope')
    expect(scope['audience'] in {'student','general'}, 'Teacher-only or private audience refused')
    expect(scope['data_classification'] in ALLOWED_DATA_CLASS,
           'Private/sensitive educational data may not enter a static Spek export')
    expect(scope['export_status'] == 'authorized_local_preview',
           'Only explicit, prefiltered, local-preview exports are accepted')
    expect(scope['pedagogical_review'] in {'not_submitted', 'reviewed'}, 'Unknown pedagogical review status')
    if scope['data_classification'] == 'public_released_excerpt':
        expect(scope['pedagogical_review'] == 'reviewed', 'Public excerpts need upstream pedagogical review')
    dataset = _text(scope['dataset_ref'], 'dataset_ref', 256)
    policy = _text(scope['reader_policy_ref'], 'reader_policy_ref', 256)
    if adapter == 'kompose':
        sel=exact(data.get('selection'), {'kristal_id','topic_id','question_id','version','access_scope'},
                  {'kristal_id','topic_id','question_id','version','access_scope'}, 'Kompose selection')
        for k in ('kristal_id','topic_id','question_id','version'):
            _text(sel[k], 'selection.'+k, 256)
        expect(sel['access_scope']=='preauthorized_public_excerpt',
               'Kompose session-only content cannot be statically exported')
    else:
        expect('selection' not in data, 'Ekole projection does not use Kompose selection')
    doc=exact(data['document'], {'article','units','evidence','sections'},
              {'article','units','evidence','sections'}, 'document')
    exact(doc['article'], {'id','title_key','subtitle_key','abstract_key'},
          {'id','title_key','subtitle_key','abstract_key'}, 'article')
    for k in ('id','title_key','subtitle_key','abstract_key'):
        safe_id(doc['article'][k], 'article.'+k)
    expect(isinstance(doc['units'],list) and isinstance(doc['evidence'],list) and
           isinstance(doc['sections'],list) and bool(doc['sections']), 'Invalid document arrays')
    for i,unit in enumerate(doc['units']):
        exact(unit, {'id','kind','realization_key','epistemic_status','evidence_refs','external_ref'},
              {'id','kind','realization_key','epistemic_status','evidence_refs','external_ref'}, f'unit[{i}]')
        for k in ('id','kind','realization_key'): safe_id(unit[k],f'unit[{i}].{k}')
        _text(unit['external_ref'], f'unit[{i}].external_ref', 256)
        expect(isinstance(unit['evidence_refs'],list), 'Bad unit evidence_refs')
    for i,ev in enumerate(doc['evidence']):
        exact(ev, {'id','realization_key','status','locator','external_ref'},
              {'id','realization_key','status','locator','external_ref'},f'evidence[{i}]')
        safe_id(ev['id'],f'evidence[{i}].id');safe_id(ev['realization_key'],f'evidence[{i}].key')
        _text(ev['external_ref'],f'evidence[{i}].external_ref',256)
        locator=_text(ev['locator'],f'evidence[{i}].locator',256).lower()
        expect(not any(x in locator for x in ('teacher-only','vault://','private_teacher',
                     'learner_ref','corrige-enseignant','/session/','answer-key')),
               'Restricted evidence locator cannot be exported')
    for i,sec in enumerate(doc['sections']):
        exact(sec, {'id','layout','heading_key','slots'},
              {'id','layout','heading_key','slots'},f'section[{i}]')
        for k in ('id','layout','heading_key'):safe_id(sec[k],f'section[{i}].{k}')
        expect(isinstance(sec['slots'],dict), 'Invalid section slots')
    realiz=exact(data['realizations'],{'format','entries'}, {'format','entries','note'},'realizations')
    expect(realiz['format']==REALIZATION_FORMAT and isinstance(realiz['entries'],dict),
           'Unsupported realization bundle')
    # Explicitly reject arbitrary keys: unfiltered upstream personal records do not
    # travel into sidecar JSON, even if they are ignored by the rendering code.
    phrases_allowed={'text','status','provider','channel','request_id','runtime_set_id',
        'model_id','generation_ref','prompt_sha256','human_review','tokens','qualification','case'}
    keys={doc['article'][x] for x in ('title_key','subtitle_key','abstract_key')}
    keys.update(sec['heading_key'] for sec in doc['sections'])
    keys.update(x['realization_key'] for x in doc['units']+doc['evidence'])
    expect(set(realiz['entries']) == keys, 'Unreferenced phrase data refused (possible private content)')
    for key, entry in realiz['entries'].items():
        safe_id(key, 'realization key')
        exact(entry,set(),{'fr','en','it'}, 'realization '+key)
        for language, phrase in entry.items():
            exact(phrase, {'text','status','provider'}, phrases_allowed, f'phrase {key}/{language}')
            _text(phrase['text'],f'phrase {key}/{language}')
            if 'human_review' in phrase:
                exact(phrase['human_review'], {'status'}, {'status','review_ref'},'human_review')
            for token in phrase.get('tokens',[]):
                exact(token,{'start','end','surface','annotation_status'},
                      {'start','end','surface','annotation_status','lemma','pos','features','lexeme_ref','semantic_ref','gf_function'},
                      'token')
    source={'format':SEMANTIC_FORMAT, 'article':copy.deepcopy(doc['article']),
        'source':{'origin':'external_projection','external_system':adapter,
            'dataset_ref':dataset,'reader_policy_ref':policy,
            'projection_sha256':digest(data),'state_ref':None,'state_commitment':None,
            'artifact_refs':[],'scientific_review':'not_submitted',
            'disclosure':'local_demo_only',
            'language_review':{'fr':'fixture','en':'fixture','it':'fixture'}},
        'units':copy.deepcopy(doc['units']), 'evidence':copy.deepcopy(doc['evidence']),
        'sections':copy.deepcopy(doc['sections'])}
    # Keep source identity, never fabricate authority or verification.
    return source,copy.deepcopy(realiz)
