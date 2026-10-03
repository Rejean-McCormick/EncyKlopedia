from __future__ import annotations

import argparse
import json

from scope_common import *


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='')
    a = ap.parse_args()
    root = find_root(a.root or None)
    db = default_global_db(root)
    ok, idx = global_index_status(root, db)
    try:
        dump = dump_descriptor(root, find_dump(root))
    except Exception as exc:
        dump = {'error': str(exc)}
    try:
        dp = find_dump(root)
        fok, fidx = fast_access_status(root, dp)
    except Exception as exc:
        fok = False
        fidx = {'complete': False, 'error': str(exc)}
    default_backend = 'index' if ok else ('fast' if fok and fidx.get('random_access_ready') else 'raw')
    baseline = load_json(root / '00_system/contracts/knowledge-baseline.json', {}) or {}
    rep = {
        'schema_version': 'encyk-status/v5',
        'release': baseline.get('encyk_release'),
        'root': str(root),
        'disk_free_gib': round(free_gib(root), 2),
        'raw_dump': dump,
        'performance': performance_status(root),
        'global_index': idx,
        'global_index_role': 'optional discovery accelerator',
        'fast_access': fidx,
        'fast_access_role': 'optional QID random-access accelerator',
        'default_discovery_backend': default_backend,
        'source_authority': 'koa-mediatheque',
        'handoff_contract': baseline.get('source_handoff'),
        'project_index_required': False,
        'scopes': [],
        'generated_at': utc_now(),
    }
    cfgdir = root / '00_system/tools/scope-builder/config/scopes'
    for path in sorted(cfgdir.glob('*.scope.json')):
        cfg = load_json(path, {})
        key = cfg.get('scope_key')
        wd = scope_workdir(root, key)
        row = {
            'scope_key': key,
            'title': cfg.get('title'),
            'config': str(path.relative_to(root)).replace('\\', '/'),
            'root_semantics': scope_root_semantics(cfg),
            'roots_resolved': (wd / 'roots.resolved.json').exists(),
            'discovered': (wd / 'discovery/entities.jsonl').exists(),
            'discovery_stats': load_json(wd / 'discovery/stats.json', None),
            'frozen': (wd / 'scope.freeze.json').exists(),
            'evidence': load_json(wd / 'evidence.latest.json', None),
            'optional_project_index': (wd / 'index' / f'{key}.sqlite').exists(),
            'identity_candidates': load_json(root / '20_evidence/identity-candidates' / key / 'latest.json', None),
            'mediatheque_handoff': load_json(root / '20_evidence/handoffs/mediatheque' / key / 'latest.json', None),
        }
        rep['scopes'].append(row)
    print(json.dumps(rep, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
