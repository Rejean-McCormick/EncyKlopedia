# 21 — V9 materialization authoring and partial availability

Logical Artifacts and their Logical Commitments are independent of physical representation. The Authoring Kit preserves existing v9 Materialization Manifests instead of reducing them to the `inline-json/1` profile. Custom compressed, factored, segmented and dictionary-based profiles remain valid.

## Discovery and registration

Manifests are discovered under `materializations/v9/manifests/**/*.json` and the supported legacy `.kristal/v9/materializations/**/*.json`. Only `artifact_type=kristal_materialization_manifest` is treated as an authoring manifest.

```bash
python tools/kristal.py register-materialization . --manifest path/to/materialization.json
python tools/kristal.py check .
python tools/kristal.py build-v9 .
```

A registered manifest must bind to the **current** source `artifact_id`, Logical Contract and Logical Commitment. Checks enforce manifest envelope, segment keys and uniqueness, `reconstructability.lossless=true`, valid byte digests, and size/SHA-256 for any currently available safe workspace-local blob.

## Remote / missing blobs

`https://`, object-store and other non-workspace locators are **descriptors only**: the Kit does not fetch bytes or claim them available. A safe relative locator whose blob is missing is reported separately. Coverage and transport inventory distinguish `workspace_local`, `workspace_missing`, `external` and `unlocated`; a partial physical representation does not imply semantic absence.

`build-v9` aggregates materialization capability profiles and preserves descriptor manifests in `build/v9/materializations/`; local blobs are not duplicated. AI `ai/INDEX.json` carries materialization **manifests** as reader files but lists blobs in separate `materialization_blobs` with size, digest, availability, transport class and locator. Managers/hosts decide transport explicitly and must not bulk-push large data into a Git tree.

```text
MANIFEST PRESERVATION != BLOB DUPLICATION
BLOB DIGEST != LOGICAL COMMITMENT
PARTIAL AVAILABILITY != NEGATION
```

A rebuild or change of host location may alter physical bytes/availability without altering v9 logical identity. Materialization schema files remain Framework-defined; no new logical contract was introduced in this candidate.
