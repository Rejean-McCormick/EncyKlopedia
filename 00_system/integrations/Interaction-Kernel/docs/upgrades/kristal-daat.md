# Kristal / Da’at upgrade

Do not add IK fields to Kristal core schemas.

Upgrade Da’at/kOA integration from v4-centric assumptions to the pinned v5 release candidate. Replace global `no compile on fail` with stage-specific gates: Working Exchange compilation may precede final validation/recognition when the Profile permits; Reference/release/distribution remain fail-closed according to policy.

Da’at is responsible for pin verification, versioned mapping profiles, native Kristal invocation, output validation and IK artifact handoff.

Preserve the operational-state boundary during migration:

- source applications keep mutable operational records in their own databases;
- Da’at consumes source-owned snapshots/ExportManifests rather than writing source databases;
- Kristal owns the resulting Kristal-native artifacts;
- Runtime Packs or database-like query materializations are derived artifacts, not replacement operational systems of record;
- completion crosses the boundary through Receipts, Events and ArtifactRefs rather than a distributed database transaction.

See [ADR-IK-05](../adrs/ADR-IK-05-operational-state-artifact-boundary.md).
