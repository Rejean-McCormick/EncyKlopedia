# Integration — Interaction Kernel

Interaction Kernel (IK) is the **selectively adopted system-of-systems interoperability protocol/Profile layer** for explicit cross-product boundaries such as Konnaxion↔Orgo and mapped ecosystem↔Da’at work. IK is transport/protocol semantics, not a participant database or Kristal artifact store.

## Status boundary

Digital Ecosystem must distinguish:

```text
IK target cross-system architecture
≠
kOA-Linux canonical internal/component communication contracts
```

The current kOA-Linux snapshot already defines its own registered command/query/event/job/artifact/receipt/gateway patterns. IK must not be described as having replaced those contracts until kOA-Linux and the product owners explicitly publish adoption/mapping.

## Adoption status

Qualified on 2026-09-21 for the Konnaxion↔Orgo boundary:

- `governance.decision.execute/1.0.0`;
- `accountability.impact.publish/1.0.0`.

The integrated qualification exercised durable delivery, Signal→Workflow→Case→Task execution, durable impact return, idempotent replay, and divergent replay rejection. See `../status/2026-09-21-konnaxion-orgo-ik-e2e-qualification.md`.

Still planned/mapped rather than qualified by this evidence:

- Kristal build/artifact/revision/distribution Profiles through Da’at;
- any kOA-Linux internal/component mapping not explicitly adopted by its owning contracts.

## Rules

- Konnaxion↔Orgo is direct by default; no forced Kristal hop.
- Da’at remains the anti-corruption/mapping boundary for IK-facing Kristal work.
- Profile admission does not imply Kristal validation/recognition.
- Source-owned artifacts remain source-owned; ArtifactRef/ExportManifest identify immutable boundary artifacts without moving the live database record.
- IK must not create a distributed transaction spanning product databases and Kristal; owners commit locally and reconcile durable cross-system effects asynchronously.
- Durable interactions preserve idempotency identity and reconciliation.

## Adoption claim

A product/platform may claim IK conformance only when its owning contracts and evidence identify the Profile/version and required behavior. The 2026-09-21 Konnaxion↔Orgo result satisfies that requirement for the two Profile/version pairs listed above only. General build/runtime qualification is not IK conformance evidence.
