# Interaction Kernel integration

**Normative for kOA ecosystem mapping:** YES
**Protocol authority:** Interaction Kernel supplied documentation/contracts

Interaction Kernel (IK) is the distributed cross-system protocol used by the target ecosystem architecture. It is not a central server and does not replace participant-owned domain APIs or stores. It is not an operational database and it is not the storage location for Kristal artifacts.

## Core protocol

Business classes:

- `command`
- `query`
- `event`

Protocol records:

- Receipt
- QueryResult

Boundary objects:

- ArtifactRef
- ExportManifest

An ArtifactRef never transfers ownership, authority or validation status. An ExportManifest identifies source-owned immutable boundary material; it is not permission to mutate the source database.

## Reliability

Reference delivery semantics are **at-least-once + idempotent processing + reconciliation**.

The logical effect is identified by `idempotency_key`. Semantic replay is protected by a deterministic request fingerprint using `ik.request-fingerprint/jcs-rfc8785+sha256/v1`.

```text
same key + same fingerprint       => replay / no new effect
same key + different fingerprint  => IK_IDEMPOTENCY_CONFLICT
```

## Required architecture rules

- Konnaxion↔Orgo is direct by default.
- A Profile may explicitly require Kristal, but Kristal is not an automatic hop.
- Da’at is the baseline IK↔Kristal ACL/mapping boundary.
- Durable commands/queries resolve to a concrete receiver.
- Published Profile/schema versions are immutable.
- Known incompatibility is rejected explicitly.
- Product owners commit mutable state locally; IK does not require a distributed transaction spanning Orgo/Konnaxion/Kristal.
- Kristal build/revision flows carry source exports/references to Da’at and return Kristal ArtifactRefs/events; they do not dual-write the same domain record into Kristal.

## Current Profiles

- `governance.decision.execute/1.0.0`
- `accountability.impact.publish/1.0.0`
- `operational.reconsideration.recommended/1.0.0`
- `kristal.build.request/1.0.0`
- `kristal.artifact.ready/1.0.0`
- `kristal.revision.request/1.0.0`
- `knowledge.distribution.request/1.0.0`

## Migration status

The migration plan defines these steps:

1. lock Core/Profile contracts and TCK;
2. wrap the existing historical Orgo→Konnaxion bridge under `accountability.impact.publish`;
3. implement immutable Konnaxion DecisionRecord→Orgo Signal/workflow;
4. add ArtifactRef/ExportManifest and source-owned exports;
5. migrate Da’at to the pinned Kristal v5 RC;
6. upgrade/reuse BuildRecord/ReleaseRecord semantics;
7. route Runtime Pack activation through the single deployment activation owner;
8. deprecate bespoke paths only after conformance and redrive validation.
