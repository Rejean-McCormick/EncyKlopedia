# Authoring Kit 4.0.0-draft.3 — diK/v11 validation

**Version candidate, 2026-10-17.** No production release, GitHub changes, or live network I/O have been performed.

## Executed tests

- New `tests.test_v11_dik_draft3` test suite: **8/8 PASS**. Exercises diK catalog staging, registration, explicit selection, preservation of curated label precedence, unapproved Q refusal, layer tamper refusal, unregistered candidate refusal and two distinct interrupted commit/recovery phases.
- Existing `tests.test_v11_authoring` and `tests.test_v11_qualification`: **11 tests executed, 9 successful and 2 skipped**, with local Framework/Integration source variables unset. Source pin and contract declarations remain unchanged.
- `python tools/kristal.py check-v11 examples/demo-semantic-v11`: PASS.
- `python tools/kristal.py coverage-v11 examples/demo-semantic-v11 --locales fr,fr-CA`: PASS (direct/fallback/missing distinguished).
- Actual new catalog candidate registration and subsequent activation on a copy of `demo-semantic-v11`: PASS, `check-v11` after selection: PASS.

## Scope of the evidence

Tests use the Authoring Kit's local Framework v11 draft.3-profile adapter and the example catalog shape shared by diK. They do **not** constitute a complete installed-diK alpha.7 cross-repository run: the matching diK source artifact was not provided in this turn. Nor do they prove full upstream Framework TCK or support for hundreds of real translated locales.

The Framework/Integration pin is retained byte-for-byte. `docs/28_V11_FRAMEWORK_QUALIFICATION.md` records prior draft.2 qualification of the previous snapshot against exact Framework reference tools; this draft.3 update still needs an independently rerun pin check with its exact source archive before being declared certified.

## Known limits

- Recoverable transaction is not a truly atomically visible multi-file commit; power-loss durability and concurrent preexisting v9 writers are not certified. Explicit recovery is required for pending journals.
- `apply-v11-plan` accepts approved, typed roles only in already-v11-shaped graphs. Arbitrary legacy graphs are intentionally outside its scope.
- Incoming diK catalog may contain imported Wikidata layers only. Reviewed curated or external sources are preserved from the old catalog; promotion of new curated edits uses a separate policy.
- No source-attribution signatures, no crosswalk reapproval automation, no original 300-language benchmark and no live Wikidata integration.

**Repository-wide validation:** `python scripts/check_repo.py` completed **PASS** on 2026-10-17, including its historical v9/v10 regressions and deterministic demo builds. The focused diK tests were separately executed (8/8 PASS), and the CI workflow invokes them explicitly.
