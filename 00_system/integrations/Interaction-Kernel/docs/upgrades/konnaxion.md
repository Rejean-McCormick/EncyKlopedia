# Konnaxion upgrade

Preserve the existing `orgo_bridge_*` J30 implementation and `OrgoImpactPublication`. Wrap it with the IK Profile `accountability.impact.publish` first.

Add:

- IK inbound/outbound adapter boundary;
- immutable `DecisionRecord` contract/read-model;
- durable emission port tied to DecisionRecord finalization;
- `KonnaxionExport v1` as a source-owned snapshot/export boundary;
- ArtifactRef support;
- RuntimePackActivationPort delegation (kOA-Linux owns host activation when present).

Konnaxion remains authoritative for its mutable governance/civic operational state. IK and Kristal artifacts may project or reference that state, but do not replace the Konnaxion system of record. Konnaxion↔Orgo remains direct unless a Profile explicitly requires a Kristal artifact.

The reference compatibility adapter is in [`adapters/konnaxion-python/`](../../adapters/konnaxion-python/).

See [ADR-IK-05](../adrs/ADR-IK-05-operational-state-artifact-boundary.md).
