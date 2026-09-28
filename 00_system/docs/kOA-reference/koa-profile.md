# kOA profile for Kristal v5

This document defines kOA-specific integration constraints without changing Kristal semantics.

## Compilation and epistemic state

Keep compilation, validation, recognition, publication and activation separate. A Working Exchange may exist before final validation/recognition where policy permits.

## Operational ownership and ingestion

Under the kOA profile, Orgo/Konnaxion/other owner databases remain authoritative for mutable product state. Kristal ingestion uses immutable source-owned exports/snapshots or explicitly referenced source artifacts with revision/digest and provenance. Da’at performs the mapping into Kristal-native semantics.

The profile does not define operational-DB↔Kristal bidirectional synchronization and does not require a distributed transaction across those owners. Products consume returned ArtifactRefs, events and derived projections without transferring ownership of their live domain records.

## Derived query/runtime materializations

A Runtime Pack may include query-optimized physical structures under the pinned Kristal contract and adopted kOA profile. Any tables, indexes, columnar files or read-only database representation are materializations, not authoritative knowledge or operational state. They must:

- reference the source Kristal artifact/content identity;
- preserve source artifact status and Reader Policy semantics;
- be immutable for a given build identity;
- be deterministically rebuildable from declared inputs;
- never accept operational writes that would create an independent source of truth.

## Runtime Pack on kOA-Linux

When a Kristal Runtime Pack is adopted by kOA-Linux:

- the platform artifact uses the `knowledge` release channel;
- Release Set compatibility can be required by the platform profile;
- `kristal_runtime` owns local Runtime Pack verification/compatibility and active-state records;
- `kristal_runtime` emits activation/rollback receipts and owns runtime health;
- kOA Node Agent executes the narrow privileged host transition when required;
- Koali Space activation remains unrelated presentation state.

## Reader Policy

Reader Policy is part of the consumption contract. Consumers preserve labels needed to distinguish source status, certainty, validation, recognition and dispute/rejection state.

## Da’at

Ecosystem/IK-facing Kristal requests route through Da’at or another explicitly adopted anti-corruption/mapping boundary. Da’at verifies the pinned dependency, applies versioned mappings and preserves Kristal-owned semantics.
