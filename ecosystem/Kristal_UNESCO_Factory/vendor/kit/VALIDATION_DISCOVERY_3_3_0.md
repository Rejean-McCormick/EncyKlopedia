# Local Kit 3.3.0 — discovery extension validation

## Scope

This package is based on the supplied Local Kit 3.2.5-rc.1 and introduces
**derived reader discovery only**, keeping `kristal.local-workspace/3.2.0`
and semantic state `kristal.state/9.0` unchanged.

- Root reader identity (`kristal.discovery/1.0`)
- Deterministic inventory of explicitly registered local physical files, declared segment descriptors, missing/external flags and size classes
- Optional Arketype v1.4 catalog resolution and noncanonical classification in the workspace
- Advisory reader profiles with format-/size-specific candidates (JSON, JSONL, other)
- Read-surface and inspect interop with no new publication permissions

## Validation procedure

1. `python scripts/check_repo.py`: repository integrity, historical tests, v10 alignment tests, new discovery tests, copied example builds, AI capsule and v9 repeatability.
2. `python -m unittest -v tests.test_discovery`: classification, stale detection, legacy compatibility, no canonical registration of hints, direct JSONL strategy, bit-for-bit repeatability.
3. Draft 2020-12 JSON Schema validation of workspace, discovery, inventory and profile for a generated example (`jsonschema` as test-time dependency only; CLI still standard library).
4. Manual exercise: `classify --arketype-dir <Arketype 1.4 folder> --usage PRF-15` resolves to ARK-08 and causal-graph-v1.
5. v9 logical invariant: rebuild before and after classification; state Logical Commitment remains identical.

## Qualifications / boundaries

- **Metadata is not semantic validation.** A PRF/ARK identity may be a declaration rather than a verified fact.
- Recorded total size is local *tracked byte size*; does not claim to measure a whole project, an external federation or a compressed payload's inflated size.
- None of these profiles cause a reader to open a file, elevate access or download blobs. The reader must verify file digest, MIME, record size, memory, decompression and access independently.
- `kristal.discovery.json` must not be registered as a domain Logical Artifact or included in the State Logical Commitment.
- `build-discovery` is safe for existing workspaces but does not migrate canon, rebuild the state or publish anything.
