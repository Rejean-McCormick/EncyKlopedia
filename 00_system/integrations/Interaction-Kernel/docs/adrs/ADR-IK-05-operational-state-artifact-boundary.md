# ADR-IK-05 — Operational state and knowledge-artifact boundary

**Status:** Accepted

## Decision

Interaction Kernel is an interoperability protocol. It is not an operational database, an artifact store, or a distributed transaction coordinator.

Each participant remains the authoritative owner of its mutable operational state:

- Konnaxion owns governance/civic runtime state such as deliberation, decisions and local workflow state;
- Orgo owns operational/work state such as Signals, Workflows, Cases and Tasks;
- Kristal owns Kristal-native knowledge/epistemic artifacts;
- Da’at owns the IK↔Kristal boundary and versioned mapping process, not the source applications' operational state;
- the configured host activation owner owns local Runtime Pack activation state.

A participant MUST commit its own authoritative state before publishing an Event that claims the fact is committed. Cross-owner workflows use durable delivery, idempotency and reconciliation rather than a transaction spanning participant databases.

When operational state contributes to Kristal, the source publishes or exposes a source-owned immutable snapshot/export and references it through `ExportManifest` and/or `ArtifactRef`. Da’at maps that snapshot to Kristal-native inputs. Kristal outputs remain Kristal-owned artifacts and are returned by reference.

Runtime Packs and other query-oriented materializations may contain derived tables, indexes or database-like structures. Such materializations do not become authoritative operational state merely because they are locally queryable or activatable. Their authority is bounded by the owning artifact contract and deployment activation contract.

## Consequences

- no direct cross-system database writes;
- no requirement for a distributed commit across Konnaxion, Orgo, Da’at or Kristal;
- IK envelopes carry intent, facts and references, not shared mutable application state;
- `ArtifactRef` and `ExportManifest` do not transfer ownership;
- local projections/caches may be rebuilt or replaced without changing the authoritative owner;
- Konnaxion↔Orgo remains direct unless a Profile explicitly requires a Kristal artifact.
