"""Import preconstructed AI sentences without using SemantiK or a network API.

AI phrases are NOT GF realizations. Claimed human review is metadata provided
by the operator and is not authenticated by this importer.
"""
from __future__ import annotations
import copy
from .core import REALIZATION_FORMAT, ValidationError, expect, safe_id, LANGS, SHA256

AI_FORMAT='spek.ai-phrases/0.1'


def import_ai(input_data: dict, base: dict | None = None) -> dict:
    expect(input_data.get('format') == AI_FORMAT, 'Expected spek.ai-phrases/0.1')
    rows=input_data.get('phrases')
    expect(isinstance(rows,list) and bool(rows), 'No AI phrases')
    result=copy.deepcopy(base) if base else {'format':REALIZATION_FORMAT,'entries':{}}
    expect(result.get('format') == REALIZATION_FORMAT and isinstance(result.get('entries'),dict),
           'Invalid base realization bundle')
    for r in rows:
        key=safe_id(r.get('realization_key'),'AI key')
        lang=r.get('language')
        expect(lang in LANGS, 'Unsupported AI language')
        expect(isinstance(r.get('text'),str) and 0<len(r['text'].strip())<=5000, 'Invalid AI phrase')
        expect(isinstance(r.get('model_id'),str) and bool(r['model_id'].strip()),'AI model ID required')
        expect(isinstance(r.get('generation_ref'),str) and bool(r['generation_ref'].strip()), 'Generation ref required')
        expect(SHA256.fullmatch(str(r.get('prompt_sha256',''))) is not None, 'AI prompt digest required')
        review=r.get('human_review',{})
        expect(isinstance(review,dict) and review.get('status') in {'pending','approved'},
               'Human review status required')
        if review['status'] == 'approved':
            expect(isinstance(review.get('review_ref'),str) and bool(review['review_ref'].strip()),
                   'Human review reference required')
        expect(not any(x in r for x in ('runtime_set_id','gf_function','semantik_request_id')),
               'AI input cannot claim SemantiK runtime or GF provenance')
        dest=result['entries'].setdefault(key,{})
        expect(lang not in dest, f'Duplicate realization forbidden: {key}/{lang}')
        dest[lang] = {
            'text':r['text'], 'status':'reviewed' if review['status']=='approved' else 'fixture',
            'provider':'ai_preconstructed', 'channel':'ai_preconstructed',
            'model_id':r['model_id'], 'generation_ref':r['generation_ref'],
            'prompt_sha256':r['prompt_sha256'], 'human_review':review,
        }
    result['note']='Imported, preconstructed AI sentences; no SemantiK execution or language certification. Human review metadata is operator-supplied.'
    return result
