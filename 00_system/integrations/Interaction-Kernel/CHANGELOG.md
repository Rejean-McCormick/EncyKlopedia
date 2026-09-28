# Changelog

## Unreleased — 2026-09-16

- Clarified that IK is not an operational database, artifact store or distributed transaction coordinator.
- Added ADR-IK-05 for the operational-state / knowledge-artifact ownership boundary.
- Made local-commit-before-Event and durable cross-owner reconciliation explicit.
- Clarified ExportManifest/ArtifactRef source ownership and non-transfer of authority.
- Clarified Da’at as the mapping/anti-corruption boundary from source-owned snapshots to Kristal-native artifacts.
- Clarified that Runtime Packs and database-like query materializations do not become authoritative operational state by virtue of local storage or activation.
- No JSON Schema or Profile wire-contract changes.

## 1.1.0-dev.2 — 2026-09-14

- Initial executable Interaction Kernel reference implementation.
- Core Envelope, Receipt, QueryResult, ArtifactRef and ExportManifest schemas.
- Seven initial Profiles for Konnaxion/Orgo/Da’at/Kristal integration.
- Python and TypeScript RFC 8785 JCS + SHA-256 request fingerprint runtimes.
- Shared TCK using the nine pinned Kristal v5.0.0-rc.1 JCS vectors.
- Admission/idempotency replay-conflict reference pipelines.
- Konnaxion legacy bridge compatibility adapter and test.
- Orgo IntegrationOperation/Signal mapping reference adapter.
- Da’at pinned Kristal consumer lock and verification.
- kOA-Linux RuntimePackActivationPort reference boundary.
