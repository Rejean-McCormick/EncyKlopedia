#!/usr/bin/env python3
"""Read-only semantic preservation audit between original and migrated workspace.

Use two *separate* copies. This never invokes migrate-v10 or build-v9 and
never writes to either workspace. An absent built state is an unknown, not PASS.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b''):
            h.update(chunk)
    return 'sha256:' + h.hexdigest()


def _canonical(root: Path) -> dict[str, str]:
    base = root / 'canon'
    if not base.is_dir():
        raise ValueError(f'Missing canonical directory: {base}')
    result = {}
    for path in sorted(base.rglob('*')):
        if path.is_symlink():
            raise ValueError(f'Canonical symlink not eligible for this audit: {path}')
        if path.is_file():
            result[path.relative_to(root).as_posix()] = _sha(path)
    return result


def _state(root: Path) -> dict | None:
    # A generated build and its source are different artifacts. Their exact
    # commitment is compared only when both sides have a corresponding state.
    candidates = ('build/v9/state-snapshot.json', 'state/state-snapshot.json')
    for rel in candidates:
        p = root / rel
        if p.is_file():
            state = json.loads(p.read_text(encoding='utf-8'))
            return {'path': rel, 'state_ref': state.get('state_ref'),
                    'logical_commitment': state.get('logical_commitment')}
    return None


def audit(before: Path, after: Path) -> dict:
    before, after = before.resolve(), after.resolve()
    if before == after:
        raise ValueError('Before and after must be separate directories.')
    old_ws = json.loads((before / 'kristal.workspace.json').read_text(encoding='utf-8'))
    new_ws = json.loads((after / 'kristal.workspace.json').read_text(encoding='utf-8'))
    old_can, new_can = _canonical(before), _canonical(after)
    differences = []
    if old_ws.get('state_ref') != new_ws.get('state_ref'):
        differences.append('state_ref changed')
    if old_can != new_can:
        differences.append('canonical bytes or path membership changed')
    old_state, new_state = _state(before), _state(after)
    if old_state and new_state:
        if old_state['state_ref'] != new_state['state_ref']:
            differences.append('built state_ref changed')
        if old_state['logical_commitment'] != new_state['logical_commitment']:
            differences.append('v9 state logical commitment changed')
        commitment_check = 'MATCH' if not any('built state_ref' in x or 'commitment' in x for x in differences) else 'DIFFERENT'
    else:
        commitment_check = 'NOT_EVALUATED: built state missing on one or both sides'
    return {
        'format': 'kristal.kit-migration-audit/1.0-nonnormative',
        'source': 'separate offline workspace directories',
        'read_only': True,
        'before': str(before), 'after': str(after),
        'canonical_file_count_before': len(old_can),
        'canonical_file_count_after': len(new_can),
        'state_ref_unchanged': old_ws.get('state_ref') == new_ws.get('state_ref'),
        'canonical_bytes_unchanged': old_can == new_can,
        'v9_commitment_comparison': commitment_check,
        'differences': differences,
        'result': ('BLOCKED' if differences else 'NOT_FULLY_QUALIFIED' if not old_state or not new_state else 'PRESERVED'),
        'note': 'Byte and declared-commitment comparison, not independent factual qualification or domain validation.',
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before', type=Path, required=True)
    ap.add_argument('--after', type=Path, required=True)
    args = ap.parse_args()
    try:
        result = audit(args.before, args.after)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({'result': 'BLOCKED', 'error': str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2))
    return 1 if result['result'] == 'BLOCKED' else 3 if result['result'] == 'NOT_FULLY_QUALIFIED' else 0


if __name__ == '__main__':
    raise SystemExit(main())
