# Agent and contributor instructions — Kristal Local Kit

This repository is the **local authoring and semantic-build owner**, not the hosted publication authority. Follow the pinned Kristal Framework contracts; do not redefine Logical/State Commitments or reclassify derived AI/hosting files as canon.

1. Preserve every v9 semantic identity and commitment unless an authorized domain change explicitly requires otherwise.
2. Keep Local Kit `check`/`build-v9`/`build-ai`/`read-surface` separate from independent qualification, public GitHub synchronization, immutable publication and activation.
3. `read-surface` is a verified **derived** file inventory for consumers such as Manager; it does not grant permission to upload any bytes.
4. Materialization manifests must remain bound to their exact source Logical Commitments. Remote and missing blobs must never be fetched or asserted available implicitly.
5. Never migrate the user's production workspace to test compatibility: compare independent copies using `scripts/audit_workspace_migration.py` and explicitly distinguish unknown evidence from passed checks.
6. Manager owns the operator registry and authorized synchronization; Bootstrap/C1/C2/C3 own trust and release gates; Arketype owns noncanonical archetype design metadata; Kompiler/Konstellation consume read-only projections.
7. Work in English for new code, docs, tests and reports. Preserve stable serialized identifiers and the old examples' historical metadata.

**Local validation:** `python scripts/check_repo.py`. The status of a passing local test is not evidence of remote GitHub qualification or factual truth.

8. For opted-in Framework v11 authoring, use namespace-qualified KQ/KP identities in semantic graphs, never labels as identity keys. The crosswalk to Wikidata is external, reviewed and independent of lexical labels.
9. Do not apply a diK migration plan until all decisions and reviewed identity-role paths are proved against the exact source digest. An approved plan is not an authorization to overwrite history.
10. This v4 draft adapter was previously checked against pinned Framework v11 draft.3 reference tools on the shipped example. **That is not full TCK or production certification.** A new Framework source must be independently requalified; never infer success from a pin file alone.
11. Authoring Kit is the **only producer/registrar of canonical graphs**; diK produces versioned lexical dictionary inputs, alignment proposals and conversion plans, not an authoritative graph or registry.
12. `import-dik-catalog` validates a source catalog and creates a new isolated candidate. `--register` only registers a new catalog; `select-v11-catalog` is separate, and neither command builds/activates a release automatically. Preserve curated layers and avoid changing previous catalog bytes.
13. All new v11 canonical JSON registrations must use recoverable transaction journaling in `kristal_v11_core`; on a pending journal **stop writes** and use explicit `recover-v11`. Never simply delete an unknown journal, manually rewrite the state index, or remove a committed registered artifact.
14. Migration remains restricted to v11-shaped sources with typed identity slots and approved roles. It cannot convert arbitrary legacy documents, and a reviewer's declared name is not strong authentication.
15. See `docs/29_DIK_CATALOG_PROMOTION.md` and `docs/30_V11_TRANSACTION_RECOVERY.md` before changing these workflows.

**Draft.3 validation status:** see `VALIDATION_V11_DRAFT3.md`. Focused tests do not certify a complete diK alpha.7 or Framework/Integration-Pack TCK run.
