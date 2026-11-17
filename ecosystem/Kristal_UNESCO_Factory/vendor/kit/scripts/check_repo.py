#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/'tools/kristal.py'


def run(*args,cwd=None):
    p=subprocess.run(list(args),cwd=cwd or ROOT,text=True,capture_output=True)
    if p.returncode:
        print(p.stdout);print(p.stderr,file=sys.stderr);raise SystemExit(p.returncode)
    return p

# JSON parseability.
for p in sorted(ROOT.rglob('*.json')):
    if any(part in {'.git','__pycache__'} for part in p.parts):continue
    try:json.loads(p.read_text(encoding='utf-8'))
    except Exception as exc:raise SystemExit(f'Invalid JSON {p.relative_to(ROOT)}: {exc}')

# Local Markdown links.
link_re=re.compile(r'\[[^\]]+\]\(([^)]+)\)')
missing=[]
for p in sorted(ROOT.rglob('*.md')):
    if any(part=='.git' for part in p.parts):continue
    text=p.read_text(encoding='utf-8')
    for link in link_re.findall(text):
        if '://' in link or link.startswith('#') or link.startswith('mailto:'):continue
        target=link.split('#',1)[0]
        if target and not (p.parent/target).resolve().exists():missing.append((p.relative_to(ROOT).as_posix(),link))
if missing:raise SystemExit(f'Broken local Markdown links: {missing}')

# Unit tests. Run in small isolated batches; this catches hidden process/global-state
# coupling and avoids long-lived subprocess accumulation on constrained runners.
TEST_BATCHES = [
    [
        'tests.test_tools.ToolTests.test_build_v9_does_not_generate_ai_by_default',
        'tests.test_tools.ToolTests.test_build_v9_logical_and_state_commitments',
        'tests.test_tools.ToolTests.test_build_v9_with_ai_generates_optional_read_layer',
        'tests.test_tools.ToolTests.test_commitment_invariance_identity_vs_payload',
        'tests.test_tools.ToolTests.test_custom_materialization_is_preserved_and_advertised',
        'tests.test_tools.ToolTests.test_materialization_binding_mismatch_fails_check',
        'tests.test_tools.ToolTests.test_materialization_local_blob_digest_mismatch_fails_check',
    ],
    [
        'tests.test_tools.ToolTests.test_configure_from_bootstrap_network',
        'tests.test_tools.ToolTests.test_configure_github_and_export_hosted',
        'tests.test_tools.ToolTests.test_external_references_are_explicit_not_silently_fetched',
        'tests.test_tools.ToolTests.test_hash_manifest_and_pack_are_reproducible',
        'tests.test_tools.ToolTests.test_hosting_metadata_does_not_change_state_commitment',
        'tests.test_tools.ToolTests.test_legacy_materialization_capability_hint_is_preserved',
    ],
    [
        'tests.test_tools.ToolTests.test_init_and_check_local_v32',
        'tests.test_tools.ToolTests.test_init_with_ai_seeds_optional_ai_entrypoint',
        'tests.test_tools.ToolTests.test_inspect_is_read_only_and_machine_readable',
        'tests.test_tools.ToolTests.test_inspect_prefers_explicit_state_export',
        'tests.test_tools.ToolTests.test_read_surface_is_exact_machine_projection_and_detects_staleness',
        'tests.test_tools.ToolTests.test_check_does_not_warn_about_ai_when_disabled',
        'tests.test_tools.ToolTests.test_jcs_basics',
        'tests.test_tools.ToolTests.test_jcs_rfc8785_sample',
    ],
    [
        'tests.test_tools.ToolTests.test_local_tool_is_self_contained',
        'tests.test_tools.ToolTests.test_migrate_v1_envelope',
        'tests.test_tools.ToolTests.test_migrate_v2_to_v3_preserves_state_index',
        'tests.test_tools.ToolTests.test_migrate_v31_preserves_existing_optional_ai_layer',
        'tests.test_tools.ToolTests.test_migrate_v3_to_v32_preserves_state_index',
        'tests.test_tools.ToolTests.test_pinned_reference_is_in_state_commitment',
        'tests.test_tools.ToolTests.test_precomputed_non_json_artifact_preserves_polymorphism',
    ],
    [
        'tests.test_tools.ToolTests.test_pack_ai_is_deterministic_and_excludes_github_tooling',
        'tests.test_tools.ToolTests.test_portable_ai_indexes_materialization_manifest_and_local_blobs',
        'tests.test_tools.ToolTests.test_portable_ai_layer_is_deterministic',
        'tests.test_tools.ToolTests.test_projection_v3_workspace_preserves_projection_v2',
        'tests.test_tools.ToolTests.test_publish_and_activate_are_separate',
        'tests.test_tools.ToolTests.test_source_uniqueness',
        'tests.test_tools.ToolTests.test_utf8_reference_order_is_deterministic',
    ],
]
for batch in TEST_BATCHES:
    run(sys.executable,'-m','unittest','-v',*batch)

run(sys.executable, '-m', 'unittest', '-v', 'tests.test_discovery', 'tests.test_discovery_interop', 'tests.test_cleanup_gui')

# Validate harmonization regressions without changing shipped workspaces.
run(sys.executable, '-m', 'unittest', '-v', 'tests.test_v10_alignment')

# Opt-in Framework v11 regression suite (legacy suites remain unchanged).
run(sys.executable, '-m', 'unittest', '-v', 'tests.test_v11_authoring')
run(sys.executable, '-m', 'unittest', '-v', 'tests.test_v11_qualification')

# Check shipped examples and rebuild the v9 example in a temp copy.
run(sys.executable,str(CLI),'check',str(ROOT/'examples/demo-open'))
run(sys.executable,str(CLI),'check',str(ROOT/'examples/demo-v9-small'))
run(sys.executable,str(CLI),'check',str(ROOT/'examples/demo-hosted-v10'))
with tempfile.TemporaryDirectory(prefix='kristal-authoring-ci-') as td:
    tmp=Path(td)/'demo';shutil.copytree(ROOT/'examples/demo-v9-small',tmp)
    shutil.rmtree(tmp/'build',ignore_errors=True);shutil.rmtree(tmp/'release',ignore_errors=True)
    run(sys.executable,str(CLI),'build-v9',str(tmp))
    run(sys.executable,str(CLI),'build-ai',str(tmp))
    run(sys.executable,str(CLI),'check-ai',str(tmp))
    first=(tmp/'build/v9/state-snapshot.json').read_bytes()
    first_ai=(tmp/'AI_MANIFEST.json').read_bytes()
    run(sys.executable,str(CLI),'build-v9',str(tmp))
    run(sys.executable,str(CLI),'build-ai',str(tmp))
    if first!=(tmp/'build/v9/state-snapshot.json').read_bytes():raise SystemExit('build-v9 is not byte-reproducible for demo-v9-small')
    if first_ai!=(tmp/'AI_MANIFEST.json').read_bytes():raise SystemExit('portable AI manifest is not reproducible')
    a=Path(td)/'portable-a.zip';b=Path(td)/'portable-b.zip'
    run(sys.executable,str(CLI),'pack-ai',str(tmp),'--output',str(a));run(sys.executable,str(CLI),'pack-ai',str(tmp),'--output',str(b))
    if a.read_bytes()!=b.read_bytes():raise SystemExit('pack-ai is not byte-reproducible')
    run(sys.executable,str(CLI),'publish-v9',str(tmp))
# Hosted example must build without contacting GitHub.
with tempfile.TemporaryDirectory(prefix='kristal-authoring-hosted-ci-') as td:
    tmp=Path(td)/'hosted';shutil.copytree(ROOT/'examples/demo-hosted-v10',tmp)
    shutil.rmtree(tmp/'build',ignore_errors=True);shutil.rmtree(tmp/'release',ignore_errors=True)
    run(sys.executable,str(CLI),'build-v9',str(tmp))
    run(sys.executable,str(CLI),'build-ai',str(tmp))
    if not (tmp/'build/v9/state-snapshot.json').is_file():raise SystemExit('hosted demo did not produce v9 state')
    run(sys.executable,str(CLI),'check-ai',str(tmp))
print(f'Kristal Local Kit {(ROOT / "VERSION").read_text().strip()} repository check: PASS')
