# Kristal Authoring Kit — v4.0.0-draft.1 validation

**2026-10-16 — candidate release, not Framework certification.**

## Scope

- Started from user-supplied `znapshot_Kristal-Authoring-Kit_10161100.zip` (reported version 3.3.1).
- Added optional `kristal.semantic-identity/11.0` gate for KQ/KP/KA/KS graphs, registry, Wikidata Q/P crosswalk and multilingual lexical catalog.
- Reused historical workspace format `kristal.local-workspace/3.2.0`, v9 state builds and v10 hosting contracts.
- Added diK-compatible per-language KQ/KP coverage, reviewed migration-plan and identity-role validation, **new-file-only** migration for v11-shaped graph sources, and explicit selection of another validated graph.
- No external tool or new web connection. `kristal_v11_core.py` uses only Python standard library.

## Evidence of tests run

| Scope | Result |
|---|---|
| New tests for rejected textual predicates, unverified crosswalk, edited dictionary, missing KQ/KP, local tool, reviewed conversion and non-destructive source | Passed in separate targeted executions |
| New negative test: a reviewer-marked citation path must never be converted | Passed |
| New positive test: valid v11 opt-in, `check`, `build-v9` and direct/fallback KQ/KP coverage | Passed |
| Demo v11 workspace `check`, `coverage-v11`, `build-v9` | Passed |
| Representative historical v9 tests: local tool, init/check, Logical/State Commitment, materialization | Passed |
| JSON parseability and local Markdown links | Passed |
| Full historical `scripts/check_repo.py` plus entire continuous `tests.test_v11_authoring` suite | **Not completed** in this environment due time limits; full CI must rerun |
| Framework v11.0.0-draft.3 independent schema/TCK requalification | **Not yet performed**; exact generated Framework draft.3 ZIP was not present in the current container session |
| Crash-safe *multi-file* transaction proof for graph plus state index | **Not established**; best-effort on-exception rollback only |

## Required next qualification gates

1. Obtain the actual normative Framework v11 draft.3 ZIP and verify every output against its exact schemas and TCK fixtures; pin an immutable framework digest in CI.
2. Run `python scripts/check_repo.py` and the deterministic release-build comparator in an unconstrained CI executor.
3. Qualify schema-specific legacy adapters; no generic word-to-Q replacement is currently supported for arbitrary historical graph formats.
4. Test crash recovery across new graph file + state-index mutation before marking migration producer production-grade.
5. Revalidate dictionary-scale workloads with the production diK source catalogs and 300+ locales.

The fact that these local checks pass is not evidence of hosted GitHub publication qualification or objective semantic truth. No live GitHub repositories have been changed.
