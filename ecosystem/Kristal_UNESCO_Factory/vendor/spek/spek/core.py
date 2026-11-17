"""Deterministic, read-only editorial composition over typed semantic references.

This is an experimental derived renderer. It does not validate Kristal logical
commitments, endorse epistemic claims, or perform publication/activation.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any

LANGS = ("fr", "en", "it")
SAFE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,120}$")
SHA256 = re.compile(r"^sha256:[a-f0-9]{64}$")
SEMANTIC_FORMAT = "kristal.layout-article-source/0.1"
REALIZATION_FORMAT = "kristal.layout-realizations/0.1"
LAYOUT_FORMAT = "kristal.editorial-layout/0.1"

class ValidationError(ValueError):
    pass


def expect(ok: bool, message: str) -> None:
    if not ok:
        raise ValidationError(message)


def read_json(path: Path) -> dict[str, Any]:
    with path.open('r', encoding='utf-8') as fp:
        data = json.load(fp)
    expect(isinstance(data, dict), f"JSON object expected: {path}")
    return data


def canonical(obj: Any) -> bytes:
    # Internal input/build fingerprint only; NOT the Framework's JCS logical commitment.
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def digest(obj: Any) -> str:
    return 'sha256:' + hashlib.sha256(canonical(obj)).hexdigest()


def safe_id(value: Any, where: str) -> str:
    expect(isinstance(value, str) and SAFE_ID.fullmatch(value) is not None, f"Invalid identifier at {where}")
    return value


def no_extra_keys(obj: dict, allowed: set[str], where: str) -> None:
    expect(not (set(obj) - allowed), f"Unexpected keys at {where}: {sorted(set(obj)-allowed)}")


@dataclass
class Compiled:
    source: dict
    realizations: dict
    layouts: dict
    units: dict
    evidence: dict
    sections: list
    languages: tuple
    source_hash: str
    realization_hash: str
    layout_hash: str
    source_verified: bool
    demo: bool

    def text(self, key: str, lang: str) -> str:
        return self.realizations['entries'][key][lang]['text']

    def item(self, ref: str, lang: str) -> dict:
        if ref in self.units:
            item = self.units[ref]
            return {'id': ref, 'kind': item['kind'], 'text': self.text(item['realization_key'], lang),
                    'epistemic_status': item.get('epistemic_status'), 'evidence_refs': item.get('evidence_refs', [])}
        item = self.evidence[ref]
        return {'id': ref, 'kind': 'evidence', 'text': self.text(item['realization_key'], lang),
                'epistemic_status': item.get('status'), 'locator': item['locator']}

    def slot_items(self, section: dict, slot: str, lang: str) -> list[dict]:
        refs = section['slots'].get(slot)
        if refs is None:
            return []
        if isinstance(refs, str):
            refs = [refs]
        return [self.item(ref, lang) for ref in refs]


def compile_inputs(source: dict, realizations: dict, layout_defs: list[dict], *,
                   languages=LANGS, state_snapshot: dict | None = None,
                   production=False) -> Compiled:
    languages = tuple(languages)
    expect(bool(languages) and len(set(languages)) == len(languages) and all(l in LANGS for l in languages), 'Unsupported/duplicate language')
    expect(source.get('format') == SEMANTIC_FORMAT, 'Unsupported semantic source format')
    expect(realizations.get('format') == REALIZATION_FORMAT, 'Unsupported realization format')
    for x in ('article', 'source', 'units', 'evidence', 'sections'):
        expect(x in source, f"Source missing {x}")
    article = source['article']
    for x in ('id', 'title_key', 'subtitle_key', 'abstract_key'):
        safe_id(article.get(x), f'article.{x}')
    expect(isinstance(source['units'], list) and isinstance(source['evidence'], list)
           and isinstance(source['sections'], list) and bool(source['sections']), 'Source lists invalid')
    units, evidence = {}, {}
    for item in source['units']:
        expect(isinstance(item, dict), 'Unit must be object')
        uid = safe_id(item.get('id'), 'unit.id')
        expect(uid not in units, f'Duplicate unit {uid}')
        safe_id(item.get('kind'), f'unit {uid}.kind')
        safe_id(item.get('realization_key'), f'unit {uid}.realization_key')
        expect(item.get('epistemic_status') in {'design_proposal', 'hypothesis', 'observation', 'method', 'limitation', 'test_result'}, f'Unknown status in {uid}')
        expect(isinstance(item.get('evidence_refs', []), list), f'Invalid evidence_refs in {uid}')
        for extra in ('external_ref','navigation_url'):
            if extra in item:
                expect(isinstance(item[extra],str) and len(item[extra]) <= 2048, f'Invalid {extra} for {uid}')
                if extra == 'navigation_url':
                    parsed=urlsplit(item[extra])
                    expect((parsed.scheme == 'https' or (parsed.scheme == 'http' and
                        parsed.hostname in {'localhost','127.0.0.1','::1'})) and parsed.hostname
                        and not parsed.username and not parsed.password and not parsed.fragment,
                        f'Unsafe navigation URL for {uid}')
        units[uid] = item
    for item in source['evidence']:
        expect(isinstance(item, dict), 'Evidence must be object')
        uid = safe_id(item.get('id'), 'evidence.id')
        expect(uid not in evidence and uid not in units, f'Duplicate evidence {uid}')
        safe_id(item.get('realization_key'), f'evidence {uid}.realization_key')
        expect(item.get('status') in {'illustrative_fixture', 'local_artifact', 'external_unverified', 'independently_verified'}, f'Evidence status missing at {uid}')
        expect(isinstance(item.get('locator'), str) and bool(item['locator'].strip()), f'Invalid locator for {uid}')
        for extra in ('external_ref','navigation_url'):
            if extra in item:
                expect(isinstance(item[extra],str) and len(item[extra]) <= 2048, f'Invalid {extra} for {uid}')
                if extra == 'navigation_url':
                    parsed=urlsplit(item[extra])
                    expect((parsed.scheme == 'https' or (parsed.scheme == 'http' and
                        parsed.hostname in {'localhost','127.0.0.1','::1'})) and parsed.hostname
                        and not parsed.username and not parsed.password and not parsed.fragment,
                        f'Unsafe navigation URL for {uid}')
        evidence[uid] = item
    for uid, unit in units.items():
        for e in unit.get('evidence_refs', []):
            expect(e in evidence, f'Unknown evidence ref {e} from {uid}')
    layouts = {}
    for ld in layout_defs:
        expect(ld.get('format') == LAYOUT_FORMAT, 'Unsupported layout format')
        lid = safe_id(ld.get('id'), 'layout.id')
        expect(lid not in layouts, f'Duplicate layout {lid}')
        expect(isinstance(ld.get('slots'), dict) and ld['slots'], f'No slots in {lid}')
        for slot, rule in ld['slots'].items():
            safe_id(slot, f'layout {lid} slot')
            expect(isinstance(rule.get('allowed_kinds'), list) and rule['allowed_kinds'], f'Missing allowed_kinds for {lid}.{slot}')
            expect(isinstance(rule.get('min'), int) and isinstance(rule.get('max'), int)
                   and 0 <= rule['min'] <= rule['max'], f'Invalid cardinality {lid}.{slot}')
        layouts[lid] = ld
    entries = realizations.get('entries')
    expect(isinstance(entries, dict), 'Missing realization entries')
    used_keys = {article[x] for x in ('title_key', 'subtitle_key', 'abstract_key')}
    seen_section_ids = set()
    for section in source['sections']:
        sid = safe_id(section.get('id'), 'section.id')
        expect(sid not in seen_section_ids, f'Duplicate section id {sid}')
        seen_section_ids.add(sid)
        lid = section.get('layout')
        expect(lid in layouts, f'Unknown layout {lid} in {sid}')
        safe_id(section.get('heading_key'), f'section {sid}.heading_key')
        used_keys.add(section['heading_key'])
        spec = layouts[lid]['slots']
        slots = section.get('slots', {})
        expect(isinstance(slots, dict), f'Invalid slots in {sid}')
        expect(not (set(slots) - set(spec)), f'Unknown slot in {sid}: {set(slots) - set(spec)}')
        for slotname, rule in spec.items():
            refs = slots.get(slotname, [])
            refs = [refs] if isinstance(refs, str) else refs
            expect(isinstance(refs, list) and all(isinstance(x, str) for x in refs), f'Invalid slot refs {sid}.{slotname}')
            expect(rule['min'] <= len(refs) <= rule['max'], f'Cardinality violation {sid}.{slotname}: expected {rule["min"]}..{rule["max"]}')
            expect(len(set(refs)) == len(refs), f'Duplicate refs in {sid}.{slotname}')
            for ref in refs:
                obj = units.get(ref) or evidence.get(ref)
                expect(obj is not None, f'Missing semantic ref {ref} for {sid}.{slotname}')
                kind = obj.get('kind', 'evidence')
                expect(kind in rule['allowed_kinds'], f'Wrong kind {kind} in {sid}.{slotname} ({ref})')
                used_keys.add(obj['realization_key'])
        # Result cards cannot present an unsubstantiated result with no claim→evidence relation.
        if lid == 'result-card':
            claim_id = slots['claim']
            claim = units[claim_id]
            expect(set(slots['evidence']) <= set(claim.get('evidence_refs', [])), f'Result {sid} evidence not linked to claim')
        if lid == 'argument-map':
            premises = slots['premises']
            expect(any(units[x].get('evidence_refs') for x in premises), f'Argument {sid} has no referenced evidence')
    # Strict language parity for ALL used phrases. No silent gaps or language fallback.
    for key in sorted(used_keys):
        expect(key in entries and isinstance(entries[key], dict), f'Missing realization key: {key}')
        for lang in languages:
            node = entries[key].get(lang)
            expect(isinstance(node, dict), f'Missing realization {key}/{lang}')
            txt = node.get('text')
            expect(isinstance(txt, str) and 0 < len(txt.strip()) <= 5000, f'Empty/oversized realization {key}/{lang}')
            expect(node.get('status') in {'fixture', 'reviewed', 'qualified'}, f'Invalid realization status {key}/{lang}')
            expect(isinstance(node.get('provider'), str) and bool(node['provider']), f'Missing provider {key}/{lang}')
            channel = node.get('channel', 'legacy')
            expect(channel in {'legacy', 'semantik_architect', 'ai_preconstructed'},
                   f'Unknown language channel {key}/{lang}')
            if channel == 'ai_preconstructed':
                expect(node['provider'] == 'ai_preconstructed', f'AI provider mismatch {key}/{lang}')
                expect(node['status'] != 'qualified', f'AI sentences cannot claim GF qualification {key}/{lang}')
                expect(not any(node.get(x) for x in ('runtime_set_id','request_id','gf_function')),
                       f'AI sentence must not claim SemantiK runtime {key}/{lang}')
                expect(all(isinstance(node.get(x),str) and bool(node[x]) for x in ('model_id','generation_ref'))
                       and SHA256.fullmatch(str(node.get('prompt_sha256',''))) is not None,
                       f'AI generation provenance required {key}/{lang}')
                expect(all(not tok.get('gf_function') and tok.get('annotation_status') != 'qualified'
                           for tok in node.get('tokens',[])),
                       f'AI phrase cannot claim GF lexical functions {key}/{lang}')
                review = node.get('human_review')
                expect(isinstance(review,dict) and review.get('status') in {'pending','approved'},
                       f'Human review required {key}/{lang}')
                if node['status'] == 'reviewed':
                    expect(review['status'] == 'approved' and isinstance(review.get('review_ref'),str)
                           and bool(review['review_ref'].strip()), f'Unreviewed AI sentence {key}/{lang}')
            elif channel == 'semantik_architect':
                expect(node['status'] != 'reviewed' or bool(node.get('request_id')),
                       f'SemantiK request identity required {key}/{lang}')
                expect(not any(node.get(x) for x in ('model_id','generation_ref','prompt_sha256','human_review')),
                       f'Mixed SemantiK/AI provenance {key}/{lang}')
            if node['status'] == 'qualified':
                expect(channel != 'ai_preconstructed' and isinstance(node.get('runtime_set_id'),str)
                       and bool(node['runtime_set_id']), f'Missing qualified runtime set {key}/{lang}')
            tokens = node.get('tokens', [])
            expect(isinstance(tokens, list) and len(tokens) <= 1000, f'Invalid token annotations {key}/{lang}')
            # Only exact surface-token spans are accepted. Unknown linguistic properties
            # are left absent rather than inferred from spelling.
            surface_spans = {(hit.start(), hit.end()): hit.group()
                for hit in re.finditer(r"\w+(?:[’'-]\w+)*|[^\w\s]", txt, re.UNICODE)}
            seen_spans = set()
            for tok in tokens:
                expect(isinstance(tok, dict), f'Invalid token {key}/{lang}')
                no_extra_keys(tok, {'start','end','surface','lemma','pos','features',
                                   'lexeme_ref','semantic_ref','gf_function','annotation_status'}, 'token')
                a,b = tok.get('start'),tok.get('end')
                expect(type(a) is int and type(b) is int and (a,b) in surface_spans
                       and (a,b) not in seen_spans and tok.get('surface') == surface_spans[(a,b)],
                       f'Token span mismatch or duplicate {key}/{lang}')
                seen_spans.add((a,b))
                expect(tok.get('annotation_status') in {'manual_fixture','reviewed','qualified'},
                       f'Token annotation status missing {key}/{lang}')
                for k in ('lemma','pos','lexeme_ref','semantic_ref','gf_function'):
                    expect(k not in tok or (isinstance(tok[k],str) and len(tok[k]) <= 256),
                           f'Invalid token attribute {k} in {key}/{lang}')
                features = tok.get('features',{})
                expect(isinstance(features,dict) and len(features)<=20
                       and all(isinstance(k,str) and isinstance(v,str)
                               and len(k)<=80 and len(v)<=160 for k,v in features.items()),
                       f'Invalid token morphology {key}/{lang}')
                if tok['annotation_status'] == 'qualified':
                    expect(node['status'] == 'qualified',
                           f'Qualified lexical annotation requires qualified realization {key}/{lang}')
    src = source['source']
    origin = src.get('origin')
    expect(origin in {'illustrative_fixture', 'kristal_v9', 'external_projection'}, 'Invalid source origin')
    source_verified = False
    if origin == 'kristal_v9':
        expect(state_snapshot is not None, 'A v9 state snapshot is required to check referenced state identity')
        expect(state_snapshot.get('artifact_type') == 'kristal_state_snapshot'
               and state_snapshot.get('schema_version') == '9.0', 'Not a v9 snapshot')
        commit = state_snapshot.get('logical_commitment', {})
        expect(state_snapshot.get('state_ref') == src.get('state_ref')
               and commit.get('digest') == src.get('state_commitment'), 'State snapshot reference/digest mismatch')
        expect(SHA256.fullmatch(str(src.get('state_commitment', ''))) is not None, 'Invalid state commitment digest')
        ids = src.get('artifact_refs', [])
        expect(bool(ids) and set(ids) <= {m.get('artifact_id') for m in state_snapshot.get('members', [])}, 'Artifact refs are not in pinned snapshot')
        # Even this is not cryptographic JCS verification. The state snapshot is treated as supplied metadata.
        source_verified = True
    demo = origin != 'kristal_v9' or any(
        entries[k][l]['status'] != 'qualified' and not (
            entries[k][l].get('channel') == 'ai_preconstructed' and
            entries[k][l]['status'] == 'reviewed' and
            entries[k][l].get('human_review', {}).get('status') == 'approved')
        for k in used_keys for l in languages)
    if production:
        expect(origin == 'kristal_v9' and source_verified, 'Publishing requires a pinned v9 source')
        expect(not demo, 'Publishing refuses illustrative or unreviewed realizations')
        expect(src.get('scientific_review') == 'approved', 'Scientific review approval required')
        expect(src.get('disclosure') == 'approved', 'Disclosure approval required')
        expect(src.get('language_review') == {l: 'approved' for l in languages}, 'Independent language review required for every language')
        # This compiler does NOT certify C1/C2/C3/C4 or grant the right to publish.
    return Compiled(source, realizations, layouts, units, evidence,
                    source['sections'], languages, digest(source), digest(realizations),
                    digest(sorted(layout_defs, key=lambda x: x['id'])), source_verified, demo)


def escape_tex(text: str) -> str:
    transform = {'\\': r'\textbackslash{}', '{': r'\{', '}': r'\}', '$': r'\$', '&': r'\&',
                 '%': r'\%', '#': r'\#', '_': r'\_', '~': r'\textasciitilde{}',
                 '^': r'\textasciicircum{}'}
    return ''.join(transform.get(x, x) for x in text)
