# Interaction Kernel adoption status

Interaction Kernel is the **selected cross-system interoperability protocol/Profile layer** for boundaries that explicitly adopt and qualify it. It is not a blanket replacement for existing platform/product contracts.

## Current interpretation

- Konnaxion↔Orgo has now qualified two explicit Profile/version pairs in an integrated local runtime:
  - `governance.decision.execute/1.0.0`;
  - `accountability.impact.publish/1.0.0`.
- The 2026-09-21 qualification demonstrated DecisionRecord publication, durable delivery, Orgo Signal/Workflow/Case/Task execution, durable impact publication back to Konnaxion, idempotent replay, and divergent replay conflict handling.
- Da’at remains the target anti-corruption/mapping boundary for IK-facing Kristal work; that mapping is not qualified by the Konnaxion↔Orgo result.
- kOA-Linux already defines canonical internal/component interaction types and contracts; no universal replacement by IK is claimed.
- generic product build/runtime/security qualification does not prove IK conformance for an undeclared Profile.

## Qualified evidence

Canonical cross-product evidence:

- `../../../status/2026-09-21-konnaxion-orgo-ik-e2e-qualification.md`

The demonstrated path is:

```text
Konnaxion DecisionRecord
→ governance.decision.execute/1.0.0
→ Orgo Signal / Workflow / Case / Task
→ IntegrationOperation
→ accountability.impact.publish/1.0.0
→ Konnaxion OrgoImpactPublication
```

Replay behavior is part of the qualification: semantically identical replay is idempotent, while divergent reuse of the same idempotency identity is rejected with `IK_IDEMPOTENCY_CONFLICT` / HTTP 409.

## Remaining closure

For any additional product/platform boundary that wants to claim IK conformance:

1. publish the Profile ID and version in the owning contracts;
2. map payload, authority, idempotency, authentication and receipt behavior to the owning runtime;
3. provide boundary-specific conformance evidence;
4. preserve compatibility bridges only as long as required by explicit migration policy;
5. do not infer ecosystem-wide IK adoption from the Konnaxion↔Orgo qualification.
