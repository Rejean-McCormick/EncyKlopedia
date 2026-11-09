#!/usr/bin/env python3
"""Verify v19 overlay using a locally installed or legacy manifest.

The original overlay distributed its manifest only at the archive root.
Windows ZIP extractors may install the repository subdirectories without it.
The canonical manifest is now installed beside this verifier as well.
No verification bypass: each expected file's size and SHA-256 are checked.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

MANIFEST = 'MANIFEST_OVERLAY_UNESCO_ATLAS_V19_20261109.json'


def main(argv=None):
    argv = argv or []
    root = Path(argv[0]).resolve() if argv else Path(__file__).resolve().parents[4]
    local_manifest = Path(__file__).resolve().parent / MANIFEST
    legacy_manifest = root / MANIFEST
    manifest = local_manifest if local_manifest.is_file() else legacy_manifest
    try:
        if not manifest.is_file():
            raise FileNotFoundError(
                'Manifeste v19 absent : installer le correctif dans C:/mycode. '
                f'Emplacements examines : {local_manifest} ; {legacy_manifest}'
            )
        document = json.loads(manifest.read_text(encoding='utf-8-sig'))
        entries = document['files']
        if not isinstance(entries, dict) or not entries:
            raise ValueError('Manifeste v19 vide ou invalide')
        failures = []
        for relative, expected in sorted(entries.items()):
            candidate = (root / relative).resolve()
            # A corrupt manifest cannot make the verifier read outside the install root.
            if not candidate.is_relative_to(root) or not candidate.is_file():
                failures.append(relative)
                continue
            data = candidate.read_bytes()
            if len(data) != expected['bytes'] or hashlib.sha256(data).hexdigest() != expected['sha256']:
                failures.append(relative)
        result = {
            'status': 'OVERLAY_UNESCO_ATLAS_V19_VALID' if not failures else 'OVERLAY_INTEGRITY_FAILED',
            'files_checked': len(entries),
            'problems': failures,
            'manifest_location': str(manifest),
            'root': str(root),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if not failures else 2
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'OVERLAY_INTEGRITY_FAILED', 'error': str(exc)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
