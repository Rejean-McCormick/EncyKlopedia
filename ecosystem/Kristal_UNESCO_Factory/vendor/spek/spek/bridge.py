"""Offline interoperability boundary: external selections -> derived Spek source.

No upstream data is interpreted as a canonical Kristal commitment or a
publication authorization. Bindings require operator-supplied payload hashes.
"""
from __future__ import annotations
import copy
from pathlib import Path
from urllib.parse import quote, urlsplit
from .core import ValidationError, expect, digest, read_json, safe_id, SEMANTIC_FORMAT

MAP_FORMAT = 'spek.bridge-map/0.1'
EXCHANGE_FORMAT = 'spek.exchange/0.1'


def safe_navigation(template: str, ref: str) -> str:
    expect(isinstance(template, str) and template.count('{id}') == 1,
           'Navigation template must contain exactly one {id}')
    url = template.replace('{id}', quote(ref, safe=''))
    parsed = urlsplit(url)
    expect(parsed.scheme == 'https' or
           (parsed.scheme == 'http' and parsed.hostname in {'localhost', '127.0.0.1', '::1'}),
           'Navigation link must be HTTPS or loopback HTTP')
    expect(bool(parsed.hostname) and not parsed.username and not parsed.password and not parsed.fragment,
           'Unsafe navigation link')
    return url


def _select_konstellation(data: dict) -> tuple[dict, dict, str, str]:
    expect(data.get('schemaVersion') == '0.2' and data.get('evaluation') == 'complete',
           'Expected Konstellation ResultSet 0.2, complete')
    expect(data.get('nextCursor') is None and data.get('total',{}).get('kind') == 'exact',
           'Paged or non-exhaustive ResultSet refused')
    context = data.get('context', {})
    dataset = context.get('datasetRef')
    policy = context.get('readerPolicyRef')
    expect(isinstance(dataset,str) and bool(dataset) and isinstance(policy,str) and bool(policy),
           'Dataset and reader policy references required')
    assertions = {}
    for row in data.get('assertions', []):
        ref = safe_id(row.get('assertionRef'), 'Konstellation assertionRef')
        expect(ref not in assertions and isinstance(row.get('payload'),dict), 'Duplicate/invalid assertion payload')
        assertions[ref] = row['payload']
    visible_assertions, sources = set(), set()
    rows = data.get('rows')
    expect(isinstance(rows,list) and bool(rows), 'No selected rows')
    for row in rows:
        expect(row.get('witnessesComplete') is True, 'Incomplete witnesses refused')
        for witness in row.get('witnesses', []):
            if witness.get('kind') == 'absence_in_view':
                continue
            visible_assertions.update(witness.get('assertionRefs', []))
            sources.update(witness.get('sourceRefs', []))
    expect(visible_assertions <= set(assertions), 'Referenced assertion payload missing from ResultSet')
    return {x: assertions[x] for x in visible_assertions}, {x: {'source_ref':x} for x in sources}, dataset, policy


def _select_exchange(data: dict) -> tuple[dict, dict, str, str]:
    expect(data.get('format') == EXCHANGE_FORMAT and data.get('complete') is True,
           'Expected complete spek.exchange/0.1')
    context = data.get('context',{})
    expect(context.get('export_status') == 'authorized_local_preview',
           'Exchange export is not approved for local preview')
    dataset, policy = context.get('dataset_ref'), context.get('reader_policy_ref')
    expect(isinstance(dataset,str) and bool(dataset) and isinstance(policy,str) and bool(policy),
           'Explicit dataset and reader-policy references required')
    claims, sources = {}, {}
    for item in data.get('assertions',[]):
        ref = safe_id(item.get('id'), 'exchange assertion id')
        expect(ref not in claims and isinstance(item.get('payload'),dict), 'Duplicate/invalid exchange assertion')
        claims[ref] = item['payload']
    for item in data.get('sources',[]):
        ref = safe_id(item.get('id'), 'exchange source id')
        expect(ref not in sources and isinstance(item.get('payload'),dict), 'Duplicate/invalid exchange source')
        sources[ref] = item['payload']
    return claims, sources, dataset, policy


def bridge_import(adapter: str, incoming: dict, template: dict, mapping: dict) -> dict:
    """Require explicit, SHA-256-pinned semantic bindings and reader scope."""
    expect(adapter in {'konstellation','exchange'}, 'Unknown bridge adapter')
    expect(mapping.get('format') == MAP_FORMAT, 'Invalid bridge mapping format')
    expect(template.get('format') == SEMANTIC_FORMAT, 'Template must be a Spek article source')
    if adapter == 'konstellation':
        assertions, sources, dataset, policy = _select_konstellation(incoming)
    else:
        assertions, sources, dataset, policy = _select_exchange(incoming)
    context = mapping.get('expected_context',{})
    expect(dataset == context.get('dataset_ref') and policy == context.get('reader_policy_ref'),
           'Dataset or reader policy differs from pinned mapping')
    unit_bindings = mapping.get('unit_bindings',{})
    evidence_bindings = mapping.get('evidence_bindings',{})
    expect(isinstance(unit_bindings,dict) and isinstance(evidence_bindings,dict), 'Invalid bindings')
    expect(set(unit_bindings) == {x['id'] for x in template['units']}, 'Every template unit must be explicitly bound')
    expect(set(evidence_bindings) == {x['id'] for x in template['evidence']}, 'Every evidence unit must be explicitly bound')
    result = copy.deepcopy(template)
    for unit in result['units']:
        b=unit_bindings[unit['id']]
        expect(isinstance(b,dict), 'Malformed unit binding')
        ref=safe_id(b.get('ref'), 'unit ref')
        expect(ref in assertions and b.get('payload_sha256') == digest(assertions[ref]),
               f'Assertion absent or payload changed: {ref}')
        unit['external_ref'] = ref
        if mapping.get('navigation_template'):
            unit['navigation_url'] = safe_navigation(mapping['navigation_template'],ref)
    for ev in result['evidence']:
        b=evidence_bindings[ev['id']]
        expect(isinstance(b,dict), 'Malformed evidence binding')
        ref=safe_id(b.get('ref'), 'source ref')
        expect(ref in sources, f'Source not visible in selected reader scope: {ref}')
        # Source refs from Konstellation witnesses are opaque; do not assert
        # the source's integrity or change its scientific status to verified.
        if adapter == 'exchange':
            expect(b.get('payload_sha256') == digest(sources[ref]), f'Source changed: {ref}')
        ev['external_ref'] = ref
        ev['status'] = 'external_unverified'
        ev['locator'] = f'{adapter}:{ref}'
        if mapping.get('navigation_template'):
            ev['navigation_url'] = safe_navigation(mapping['navigation_template'],ref)
    result['source'] = {
        'origin':'external_projection',
        'external_system':adapter if adapter == 'konstellation' else mapping.get('system_name','external'),
        'dataset_ref':dataset,
        'reader_policy_ref':policy,
        'projection_sha256':digest(incoming),
        'state_ref':None,
        'state_commitment':None,
        'artifact_refs':[],
        'scientific_review':'not_submitted',
        'disclosure':'local_demo_only',
        'language_review':{'fr':'fixture','en':'fixture','it':'fixture'},
    }
    return result


def fetch_konstellation(base_url: str, query: dict, *, token: str = '', timeout: int = 15) -> dict:
    """Explicit, read-only POST /api/query. Never sends source data to other endpoints.

    Callers are responsible for supplying a Reader Policy-scoped QuerySpec.
    The fetched ResultSet must still be validated by bridge_import, including
    complete witnesses and pinned dataset/reader-policy refs.
    """
    import json
    from urllib.request import Request, urlopen
    from urllib.parse import urlsplit
    from urllib.error import HTTPError, URLError
    url = base_url.rstrip('/') + '/api/query'
    parsed = urlsplit(url)
    expect((parsed.scheme == 'https' or (parsed.scheme == 'http' and parsed.hostname in
            {'localhost','127.0.0.1','::1'})) and parsed.hostname and not parsed.username
            and not parsed.password and not parsed.query and not parsed.fragment,
           'Konstellation endpoint must be HTTPS or local loopback HTTP')
    expect(isinstance(query,dict), 'QuerySpec must be JSON object')
    raw=json.dumps(query,ensure_ascii=False).encode('utf-8')
    expect(len(raw)<=256000, 'Query too large')
    headers={'Content-Type':'application/json', 'Accept':'application/json'}
    if token: headers['Authorization']='Bearer '+token
    req=Request(url,raw,headers,method='POST')
    # Disable redirects: never forward bearer tokens to a different origin.
    from urllib.request import build_opener, HTTPRedirectHandler
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):return None
    try:
        with build_opener(NoRedirect()).open(req,timeout=timeout) as response:
            expect(response.status==200, 'Konstellation query failed')
            expect('application/json' in response.headers.get('Content-Type',''), 'Expected JSON response')
            content=response.read(5_000_001)
            expect(len(content)<=5_000_000, 'ResultSet too large')
    except (HTTPError, URLError) as e:
        raise ValidationError(f'Konstellation query failed (HTTP/network): {type(e).__name__}') from None
    try:result=json.loads(content)
    except ValueError:raise ValidationError('Malformed Konstellation JSON response') from None
    expect(isinstance(result,dict),'ResultSet must be object')
    _select_konstellation(result)
    return result
