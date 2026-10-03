from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from scope_common import *

STAGES = ['resolve', 'discover', 'freeze', 'evidence', 'index', 'identities', 'handoff']


def call(cmd: list[str]) -> None:
    print('\n$ ' + ' '.join(map(str, cmd)), flush=True)
    rc = subprocess.call([str(x) for x in cmd])
    if rc:
        raise SystemExit(rc)


def wait_index(root: Path, poll: int) -> None:
    while True:
        ok, meta = global_index_status(root)
        if ok:
            print('[auto] global discovery index complete.', flush=True)
            return
        print(
            f"[auto] waiting for optional global index | processed={meta.get('processed_entities','?')} | complete={meta.get('complete',False)}",
            flush=True,
        )
        time.sleep(poll)


def main() -> None:
    ap = argparse.ArgumentParser(
        description='Orchestrate EncyK discover → acquire/extract → external identity candidates → Mediatheque handoff.'
    )
    ap.add_argument('--root', default='')
    ap.add_argument('--scope', action='append', required=True, help='Repeat to union scopes in one evidence dump scan.')
    ap.add_argument('--through', choices=STAGES, default='handoff')
    ap.add_argument('--from-stage', choices=STAGES, default='resolve')
    ap.add_argument('--discovery-backend', choices=['auto', 'index', 'fast', 'raw'], default='auto')
    ap.add_argument('--wait-for-index', action='store_true')
    ap.add_argument('--poll-seconds', type=int, default=60)
    ap.add_argument('--build-query-index', action='store_true', help='Optional rebuildable per-project SQLite.')
    ap.add_argument('--cache-vault', action='store_true', help='Optional selected-record cache under 30_working/entity-vaults.')
    ap.add_argument('--min-free-gib', type=float, default=20.0)
    ap.add_argument('--threads', type=int, default=0)
    ap.add_argument('--prepare-fast-access', action='store_true')
    ap.add_argument('--allow-full-scan', action='store_true')
    a = ap.parse_args()

    root = find_root(a.root or None)
    scripts = Path(__file__).resolve().parent
    if a.prepare_fast_access:
        perf = root / '00_system/tools/performance/scripts/build_fast_access.py'
        call([sys.executable, perf, '--root', root, *(['--threads', str(a.threads)] if a.threads else [])])
    if a.wait_for_index:
        wait_index(root, a.poll_seconds)
        a.discovery_backend = 'index'

    scope_cfgs: list[tuple[str, str]] = []
    for scope in a.scope:
        _, cfg = load_scope_config(root, scope)
        scope_cfgs.append((scope, cfg['scope_key']))

    start = STAGES.index(a.from_stage)
    end = STAGES.index(a.through)
    if start > end:
        raise SystemExit('--from-stage doit précéder --through')

    def active(stage: str) -> bool:
        return start <= STAGES.index(stage) <= end

    for scope, _ in scope_cfgs:
        if active('resolve'):
            call([sys.executable, scripts / '01_resolve_roots.py', '--root', root, '--scope', scope, '--backend', a.discovery_backend])
        if active('discover'):
            call([sys.executable, scripts / '02_discover_scope.py', '--root', root, '--scope', scope, '--backend', a.discovery_backend])
        if active('freeze'):
            call([sys.executable, scripts / '03_freeze_scope.py', '--root', root, '--scope', scope])

    if active('evidence'):
        if free_gib(root) < a.min_free_gib:
            raise SystemExit(f'Espace libre sous le seuil {a.min_free_gib:.1f} GiB; arrêt avant extraction evidence.')
        cmd = [sys.executable, scripts / '04_extract_evidence.py', '--root', root]
        for scope, _ in scope_cfgs:
            cmd += ['--scope', scope]
        if a.cache_vault:
            cmd.append('--cache-vault')
        if a.allow_full_scan:
            cmd.append('--allow-full-scan')
        if a.threads:
            cmd += ['--threads', str(a.threads)]
        call(cmd)

    for scope, _ in scope_cfgs:
        if active('index') and a.build_query_index:
            call([sys.executable, scripts / '05_build_scope_index.py', '--root', root, '--scope', scope])
        if active('identities'):
            call([sys.executable, scripts / '06_prepare_identity_candidates.py', '--root', root, '--scope', scope])
        if active('handoff'):
            # Identity candidates are part of the canonical handoff when the pipeline reaches handoff directly.
            latest = load_json(scope_workdir(root, load_scope_config(root, scope)[1]['scope_key']) / 'evidence.latest.json', {}) or {}
            key = load_scope_config(root, scope)[1]['scope_key']
            id_latest = load_json(root / '20_evidence/identity-candidates' / key / 'latest.json', {}) or {}
            if id_latest.get('snapshot_id') != latest.get('snapshot_id'):
                call([sys.executable, scripts / '06_prepare_identity_candidates.py', '--root', root, '--scope', scope])
            call([sys.executable, scripts / '07_prepare_source_handoff.py', '--root', root, '--scope', scope])

    report = {
        'complete': True,
        'scopes': [key for _, key in scope_cfgs],
        'from_stage': a.from_stage,
        'through': a.through,
        'discovery_backend_requested': a.discovery_backend,
        'direct_lossless_evidence': True,
        'handoff_target': 'koa-mediatheque',
        'project_query_index_built': bool(a.build_query_index and active('index')),
        'vault_cache_enabled': a.cache_vault,
        'threads': a.threads or performance_status(root).get('recommended_threads'),
        'fast_access_prepared': a.prepare_fast_access,
        'allow_full_scan': a.allow_full_scan,
        'finished_at': utc_now(),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
