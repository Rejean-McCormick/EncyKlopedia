# ADR-0011: Operational state, Kristal knowledge, and runtime materialization boundary

- **Status:** Accepted
- **Date:** 2026-09-16
- **Scope:** cross-system state ownership and Kristal ingestion/materialization; does not redefine Kristal schemas

## Context

The ecosystem needs a stable rule for deciding which data remains in normal product databases, which data becomes a Kristal artifact, and whether database-like structures may be packaged with Kristal Runtime Packs.

Without an explicit boundary, implementations could drift toward dual writes, bidirectional database synchronization or treating a Runtime Pack query store as a second authority.

## Decision

1. **Product operational state remains product-owned.** Orgo, Konnaxion and other systems keep mutable transactional/domain state in their own authoritative stores.
2. **No cross-system dual-write authority.** A product does not make the same live domain record authoritative in both its operational database and Kristal.
3. **Kristal ingestion is artifact-based.** Knowledge compilation consumes immutable source-owned exports/snapshots or explicitly referenced source artifacts with revision/digest and provenance.
4. **Da’at is the mapping boundary.** Da’at maps source artifacts into Kristal-native epistemic structures; Interaction Kernel may transport the request, references and resulting events/receipts but owns neither database nor Kristal storage.
5. **The resulting Kristal artifact is distinct from its source record.** It may assert knowledge derived from that record and preserve lineage to it, but does not transfer ownership of the live record.
6. **Runtime/query stores are derived materializations.** A Runtime Pack may contain deterministic tables, indexes, columnar data or a profile-defined read-only database representation for efficient consumption.
7. **A materialization is never authoritative.** For a given build identity it is immutable, tied to the source Kristal artifact, and deterministically rebuildable from declared inputs. Removing/rebuilding it must not change authoritative knowledge state.
8. **No bidirectional authority synchronization.** Operational database → source artifact → Kristal artifact → Runtime Pack is the authority direction. Products may consume ArtifactRefs/projections, but the three layers do not become peer writable sources of truth.
9. **No distributed transaction is required across owners.** Each owner commits locally and durable cross-system effects use the adopted asynchronous/idempotent/reconciliation contracts.

## Reference model

```text
Operational DB / product state
  mutable + transactional + product-owned
        │
        │ immutable export/snapshot + provenance
        ▼
Da’at mapping boundary
        ▼
Kristal Exchange / epistemic artifacts
  content-addressed + epistemic + Kristal-owned
        │
        │ deterministic derivation
        ▼
Runtime Pack / query materialization
  read-oriented + non-authoritative + rebuildable
```

## Consequences

- Orgo Cases/Tasks and Konnaxion consultations/votes/DecisionRecords remain in their product stores.
- Kristal carries assertions, provenance, certainty/status, validation/recognition, authority scope, Reader Policy and related epistemic state derived from source artifacts.
- ArtifactRef/ExportManifest can connect layers without copying ownership.
- SQLite or another database-like file may be supported only as an explicitly profiled **read-only derived Runtime Pack materialization**, not as the mutable product database or canonical Kristal state unless a future Kristal normative contract explicitly says otherwise.
- Schemas do not need to change merely to document this boundary; a concrete SQLite/profile contract would require its own later specification/adoption.
