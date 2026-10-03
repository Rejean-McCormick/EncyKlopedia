from __future__ import annotations

import argparse
import json
from pathlib import Path

from scope_common import *

CONTRACT = 'encyk.source-evidence-handoff/2.0.0'


def file_entry(root: Path, path: Path, role: str) -> dict[str, Any]:
    return {
        'role': role,
        'path': str(path.relative_to(root)).replace('\\', '/'),
        'bytes': path.stat().st_size,
        'sha256': 'sha256:' + sha256_file(path),
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description='Prepare a content-addressed EncyK source-evidence handoff for Mediatheque kOA.'
    )
    ap.add_argument('--root', default='')
    ap.add_argument('--scope', required=True)
    a = ap.parse_args()

    root = find_root(a.root or None)
    cfgp, cfg = load_scope_config(root, a.scope)
    key = cfg['scope_key']
    wd = scope_workdir(root, key)

    baseline = load_json(root / '00_system/contracts/knowledge-baseline.json', {}) or {}
    if baseline.get('source_handoff') != CONTRACT:
        raise SystemExit('Ecosystem baseline absent or incompatible.')

    latest = load_json(wd / 'evidence.latest.json', {}) or {}
    sid = latest.get('snapshot_id')
    if not sid:
        raise SystemExit('Evidence snapshot absent.')

    snap = scope_snapshot_dir(root, key, sid)
    freeze = wd / 'scope.freeze.json'
    evidence_manifest = snap / 'snapshot-manifest.json'
    evidence = snap / 'entities.wikidata.jsonl.gz'
    entity_manifest = snap / 'entities.manifest.jsonl'
    for path in (freeze, evidence_manifest, evidence, entity_manifest):
        if not path.exists():
            raise FileNotFoundError(path)

    identity_latest = load_json(root / '20_evidence/identity-candidates' / key / 'latest.json', {}) or {}
    identity_path: Path | None = None
    if identity_latest.get('snapshot_id') == sid and identity_latest.get('file'):
        candidate = root / str(identity_latest['file'])
        if candidate.exists():
            identity_path = candidate

    files = [
        file_entry(root, freeze, 'frozen_scope'),
        file_entry(root, evidence_manifest, 'evidence_manifest'),
        file_entry(root, evidence, 'lossless_source_evidence'),
        file_entry(root, entity_manifest, 'entity_content_manifest'),
    ]
    if identity_path is not None:
        files.append(file_entry(root, identity_path, 'external_identity_candidates'))

    evman = load_json(evidence_manifest, {}) or {}
    created_at = str(evman.get('created_at') or utc_now())
    dump_meta = evman.get('dump') or {}
    source_snapshot = {k: dump_meta.get(k) for k in ('dump_id', 'filename', 'bytes', 'sha1', 'identity_strength') if dump_meta.get(k) is not None}
    if not source_snapshot and evman.get('dump_id'):
        source_snapshot = {'dump_id': evman.get('dump_id')}
    med = baseline['mediatheque']

    payload: dict[str, Any] = {
        'schema_version': 'encyk-source-evidence-handoff/v2',
        'contract': CONTRACT,
        'producer': {'system': 'encyk', 'version': baseline['encyk_release']},
        'consumer': {
            'system': 'koa-mediatheque',
            'minimum_version': med['minimum_release'],
            'source_catalog_profile': med['source_catalog_profile'],
        },
        'scope_key': key,
        'snapshot_id': sid,
        'source_system': 'wikidata',
        'source_descriptor': {
            'external_source_id': 'wikidata:entity-dump',
            'title': 'Wikidata entity dump',
            'publisher': 'Wikimedia Foundation',
            'source_kind': 'dataset',
            'source_family': 'wikidata',
            'canonical_url': 'https://dumps.wikimedia.org/wikidatawiki/entities/',
        },
        'created_at': created_at,
        'source_snapshot': source_snapshot,
        'scope_config': file_entry(root, cfgp, 'scope_config'),
        'files': files,
        'invariants': [
            'Selection may be selective; admitted source records remain lossless.',
            'External identifiers are source identity candidates, not canonical Mediatheque source/snapshot/version identity.',
            'Mediatheque becomes the persistent source/snapshot/representation authority after acceptance.',
            'EncyK does not maintain a second canonical source catalog after handoff.',
            'The handoff contains source evidence and source identity hints only; it contains no downstream semantic artifact.',
            'Derived SQLite indexes and caches are rebuildable accelerators and are not source evidence.',
        ],
    }

    identity_payload = dict(payload)
    identity_payload.pop('created_at', None)
    handoff_hash = sha256_bytes(
        json.dumps(identity_payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    )
    hid = 'handoff-' + handoff_hash[:20]
    payload['handoff_id'] = hid

    outdir = root / '20_evidence/handoffs/mediatheque' / key
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f'{hid}.json'
    save_json(out, payload)
    save_json(
        outdir / 'latest.json',
        {
            'handoff_id': hid,
            'path': str(out.relative_to(root)).replace('\\', '/'),
            'snapshot_id': sid,
            'contract': CONTRACT,
            'consumer': 'koa-mediatheque',
            'updated_at': utc_now(),
        },
    )
    print(
        json.dumps(
            {
                'handoff_id': hid,
                'contract': CONTRACT,
                'scope_key': key,
                'snapshot_id': sid,
                'path': str(out),
                'consumer': 'koa-mediatheque',
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == '__main__':
    main()
