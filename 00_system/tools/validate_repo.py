from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main() -> int:
    errors: list[str] = []
    manifest = load(ROOT / 'MANIFEST.json')
    baseline = load(ROOT / '00_system/contracts/knowledge-baseline.json')

    if manifest.get('package_version') != '0.12.0':
        errors.append('manifest package_version != 0.12.0')
    if (ROOT / 'VERSION').read_text().strip() != '0.12.0':
        errors.append('VERSION != 0.12.0')
    if manifest.get('zones') != ['00_system', '10_sources', '20_evidence', '30_working', '90_runtime']:
        errors.append('active zones mismatch')
    if baseline.get('source_handoff') != 'encyk.source-evidence-handoff/2.0.0':
        errors.append('source handoff baseline mismatch')
    if baseline.get('mediatheque', {}).get('source_catalog_profile') != 'koa.source-catalog/2.0.0':
        errors.append('Mediatheque source catalog baseline mismatch')
    if baseline.get('interaction_kernel', {}).get('baseline') != '2.0.0-dev.2':
        errors.append('IK baseline mismatch')
    if baseline.get('daat') != {
        'human_name': 'DaaT',
        'machine_id': 'daat',
        'role': 'optional IK-to-Kristal admission and explicit contract-mapping boundary',
    }:
        errors.append('DaaT baseline mismatch')
    if baseline.get('kristal', {}).get('portable_contract') != 'kristal_state/6.0':
        errors.append('Kristal portable contract mismatch')
    if baseline.get('kristal', {}).get('kristall_design_baseline') != '7.0.0-draft.3.2':
        errors.append('Kristall baseline mismatch')
    if baseline.get('kompiler', {}).get('baseline') != '0.5.0':
        errors.append('Kompiler baseline mismatch')

    forbidden_paths = [
        ROOT / '40_kristal',
        ROOT / '50_mediatheque',
        ROOT / '20_ingest',
        ROOT / '00_system/integrations/Interaction-Kernel',
        ROOT / '00_system/tools/legacy',
    ]
    for path in forbidden_paths:
        if path.exists():
            errors.append(f'forbidden active path exists: {path.relative_to(ROOT)}')

    required = [
        '00_system/tools/scope-builder/scripts/01_resolve_roots.py',
        '00_system/tools/scope-builder/scripts/02_discover_scope.py',
        '00_system/tools/scope-builder/scripts/03_freeze_scope.py',
        '00_system/tools/scope-builder/scripts/04_extract_evidence.py',
        '00_system/tools/scope-builder/scripts/05_build_scope_index.py',
        '00_system/tools/scope-builder/scripts/06_prepare_identity_candidates.py',
        '00_system/tools/scope-builder/scripts/07_prepare_source_handoff.py',
        '00_system/contracts/source-evidence-handoff/2.0.0/schema.json',
        'harvest.ps1',
        'harvest_raw.ps1',
    ]
    for rel in required:
        if not (ROOT / rel).is_file():
            errors.append(f'missing required file: {rel}')

    # Human-facing DaaT naming is normalized everywhere in active text.
    old_names = ('Da' + chr(39) + 'at', 'Da' + chr(0x2019) + 'at', 'Da' + '-at')
    active_roots = [ROOT / 'README.md', ROOT / 'CHANGELOG.md', ROOT / '00_system']
    for base in active_roots:
        files = [base] if base.is_file() else [p for p in base.rglob('*') if p.is_file()]
        for path in files:
            if 'history' in path.parts:
                continue
            try:
                text = path.read_text(encoding='utf-8')
            except (UnicodeDecodeError, OSError):
                continue
            for old in old_names:
                if old in text:
                    errors.append(f'legacy DaaT spelling in {path.relative_to(ROOT)}')

    # No active Kristal v5 pin or old handoff contract.
    forbidden_tokens = ('5.0.0' + '-rc', 'kristal.' + 'referent-registry/1.0.0', 'encyklopedia.' + 'corpus-harvest-handoff/1.0.0')
    for base in [ROOT / 'README.md', ROOT / '00_system']:
        files = [base] if base.is_file() else [p for p in base.rglob('*') if p.is_file()]
        for path in files:
            try:
                text = path.read_text(encoding='utf-8')
            except (UnicodeDecodeError, OSError):
                continue
            if any(token in text for token in forbidden_tokens):
                errors.append(f'stale legacy contract pin in {path.relative_to(ROOT)}')

    if errors:
        for error in errors:
            print('ERROR:', error)
        return 1
    print('EncyK repository validation: PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
