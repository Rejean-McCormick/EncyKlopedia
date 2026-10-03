from __future__ import annotations

import argparse
import gzip
import json
import re
from pathlib import Path

from scope_common import *

ROLE_KIND_HINTS = {
    'person_root': 'person',
    'person': 'person',
    'work_root': 'work',
    'work': 'work',
    'place': 'place',
    'country': 'place',
    'institution': 'collective',
    'institution_or_group': 'collective',
    'field': 'concept',
    'occupation': 'concept',
    'worldview': 'concept',
    'movement': 'concept',
    'intellectual_context': 'concept',
    'work_context': 'other',
    'place_or_institution_context': 'other',
    'person_neighbor': 'other',
    'root_neighbor': 'other',
    'person_or_influence': 'other',
}

EXTERNAL_ID_SYSTEMS = {
    'P214': 'viaf',
    'P1938': 'project-gutenberg-author',
    'P648': 'openlibrary',
    'P268': 'bnf',
    'P950': 'bne',
    'P212': 'isbn13',
    'P957': 'isbn10',
    'P356': 'doi',
}


def labels(obj: dict[str, Any]) -> list[dict[str, str]]:
    out = []
    for lang, val in (obj.get('labels') or {}).items():
        if isinstance(val, dict) and val.get('value'):
            rec = {'text': str(val['value'])}
            if re.fullmatch(r'^[a-zA-Z]{2,3}(-[a-zA-Z0-9]{2,8})*$', str(lang)):
                rec['lang'] = str(lang)
            out.append(rec)
    return out or [{'text': str(obj.get('id') or 'unknown')}]


def description(obj: dict[str, Any]) -> str | None:
    desc = obj.get('descriptions') or {}
    for lang in ('fr', 'en', 'mul'):
        val = desc.get(lang)
        if isinstance(val, dict) and val.get('value'):
            return str(val['value'])
    for val in desc.values():
        if isinstance(val, dict) and val.get('value'):
            return str(val['value'])
    return None


def source_external_ids(obj: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    wid = obj.get('id')
    if wid:
        out.append({'system': 'wikidata', 'id': str(wid), 'url': f'https://www.wikidata.org/wiki/{wid}'})
    claims = obj.get('claims') or {}
    for pid, system in EXTERNAL_ID_SYSTEMS.items():
        for st in claims.get(pid, []) or []:
            sn = st.get('mainsnak') or {}
            dv = sn.get('datavalue') or {}
            if dv.get('type') == 'string' and isinstance(dv.get('value'), str):
                out.append({'system': system, 'id': dv['value']})
    seen: set[tuple[str, str]] = set()
    dedup: list[dict[str, str]] = []
    for item in out:
        key = (item['system'], item['id'])
        if key not in seen:
            seen.add(key)
            dedup.append(item)
    return dedup


def infer_kind_hint(cfg: dict[str, Any], roles: list[str]) -> str:
    sem = scope_root_semantics(cfg)
    if sem['role'] in roles:
        return sem['kind']
    # 0.12 name; retain the old config key only as a read-compatibility fallback.
    section = cfg.get('identity_candidates') or cfg.get('referents') or {}
    overrides = section.get('role_kind_overrides') or {}
    for role in roles:
        kind = overrides.get(role) or ROLE_KIND_HINTS.get(role)
        if kind in IDENTITY_KIND_HINTS:
            return str(kind)
    return 'other'


def main() -> None:
    ap = argparse.ArgumentParser(
        description='Prepare source-qualified external identity candidates from one frozen EncyK scope.'
    )
    ap.add_argument('--root', default='')
    ap.add_argument('--scope', required=True)
    a = ap.parse_args()

    root = find_root(a.root or None)
    _, cfg = load_scope_config(root, a.scope)
    key = cfg['scope_key']
    wd = scope_workdir(root, key)
    latest = load_json(wd / 'evidence.latest.json', {}) or {}
    sid = latest.get('snapshot_id')
    if not sid:
        raise SystemExit('Evidence snapshot absent.')

    freeze = load_json(wd / 'scope.freeze.json', {}) or {}
    roles = freeze.get('entity_roles') or {}
    snap = scope_snapshot_dir(root, key, sid)
    evidence = snap / 'entities.wikidata.jsonl.gz'
    manifest_rows = {row['wid']: row for row in read_jsonl(snap / 'entities.manifest.jsonl')}
    if not evidence.exists():
        raise FileNotFoundError(evidence)

    records: list[dict[str, Any]] = []
    with gzip.open(evidence, 'rt', encoding='utf-8') as handle:
        for line in handle:
            if not line.strip():
                continue
            obj = json_loads(line)
            wid = str(obj.get('id') or '')
            if not wid:
                continue
            rs = sorted(set((roles.get(wid) or {}).get('roles') or []))
            rec: dict[str, Any] = {
                'schema_version': 'encyk-external-identity-candidate/v1',
                'source_system': 'wikidata',
                'external_id': wid,
                'external_ref': f'wikidata:{wid}',
                'labels': labels(obj),
                'external_ids': source_external_ids(obj),
                'scope_roles': rs,
                'kind_hint': infer_kind_hint(cfg, rs),
                'source_scope': key,
                'source_snapshot': sid,
                'source_entity_sha256': (manifest_rows.get(wid) or {}).get('sha256'),
                'authority': 'source_identity_hint_only',
            }
            desc = description(obj)
            if desc:
                rec['description'] = desc
            records.append(rec)

    records.sort(key=lambda x: x['external_ref'])
    outdir = root / '20_evidence/identity-candidates' / key
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f'{sid}.external-identities.jsonl'
    write_jsonl(out, records)
    manifest = {
        'schema_version': 'encyk-external-identity-candidate-set/v1',
        'scope_key': key,
        'snapshot_id': sid,
        'candidate_count': len(records),
        'file': str(out.relative_to(root)).replace('\\', '/'),
        'sha256': 'sha256:' + sha256_file(out),
        'authority': 'candidate_only',
        'identity_invariant': 'external identifiers are mappings/candidates; they are not canonical Mediatheque source UUIDs or downstream semantic identities',
        'generated_at': utc_now(),
    }
    save_json(outdir / f'{sid}.manifest.json', manifest)
    save_json(outdir / 'latest.json', manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
