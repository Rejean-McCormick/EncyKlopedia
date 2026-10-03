from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from scope_common import *


def fingerprint(root: Path, scope_arg: str) -> str:
    cfgp, cfg = load_scope_config(root, scope_arg)
    src = cfg.get('root_source') or {}
    reg = root / src.get('path', '')
    digest = hashlib.sha256()
    digest.update(cfgp.read_bytes())
    if reg.exists():
        digest.update(reg.read_bytes())
    try:
        dump = find_dump(root)
        desc = dump_descriptor(root, dump)
        digest.update(json.dumps({'dump_id': desc['dump_id'], 'bytes': desc['bytes']}, sort_keys=True).encode())
    except Exception:
        pass
    return digest.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description='Run EncyK only when acquisition/scope inputs changed.')
    ap.add_argument('--root', default='')
    ap.add_argument('--scope', action='append', required=True)
    ap.add_argument('--through', default='handoff')
    ap.add_argument('--discovery-backend', choices=['auto', 'index', 'fast', 'raw'], default='auto')
    ap.add_argument('--prefer-index', action='store_true')
    ap.add_argument('--poll-seconds', type=int, default=60)
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--build-query-index', action='store_true')
    ap.add_argument('--cache-vault', action='store_true')
    ap.add_argument('--allow-full-scan', action='store_true')
    ap.add_argument('--threads', type=int, default=0)
    a = ap.parse_args()

    root = find_root(a.root or None)
    script = Path(__file__).resolve().parent / 'run_scope_pipeline.py'
    state_dir = root / '90_runtime/automation'
    state_dir.mkdir(parents=True, exist_ok=True)
    fingerprints = {scope: fingerprint(root, scope) for scope in a.scope}

    if not a.force:
        current = True
        for scope in a.scope:
            _, cfg = load_scope_config(root, scope)
            key = cfg['scope_key']
            state = load_json(state_dir / f'{key}.json', {}) or {}
            handoff = load_json(root / '20_evidence/handoffs/mediatheque' / key / 'latest.json', {}) or {}
            if state.get('input_fingerprint') != fingerprints[scope] or not handoff.get('handoff_id'):
                current = False
                break
        if current:
            print('[auto] all selected scopes are current; nothing to do.')
            return

    cmd = [sys.executable, script, '--root', root, '--through', a.through, '--discovery-backend', ('index' if a.prefer_index else a.discovery_backend)]
    if a.prefer_index:
        cmd += ['--wait-for-index', '--poll-seconds', str(a.poll_seconds)]
    if a.build_query_index:
        cmd.append('--build-query-index')
    if a.cache_vault:
        cmd.append('--cache-vault')
    if a.allow_full_scan:
        cmd.append('--allow-full-scan')
    if a.threads:
        cmd += ['--threads', str(a.threads)]
    for scope in a.scope:
        cmd += ['--scope', scope]

    rc = subprocess.call([str(x) for x in cmd])
    if rc:
        raise SystemExit(rc)

    for scope in a.scope:
        _, cfg = load_scope_config(root, scope)
        key = cfg['scope_key']
        handoff = load_json(root / '20_evidence/handoffs/mediatheque' / key / 'latest.json', {}) or {}
        save_json(
            state_dir / f'{key}.json',
            {
                'scope_key': key,
                'input_fingerprint': fingerprints[scope],
                'handoff_id': handoff.get('handoff_id'),
                'updated_at': utc_now(),
            },
        )


if __name__ == '__main__':
    main()
