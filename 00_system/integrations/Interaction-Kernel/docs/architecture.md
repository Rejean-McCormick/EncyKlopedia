# Architecture

IK is a distributed protocol, not a central server, database, artifact store or distributed transaction coordinator.

```text
Konnaxion  <---------- IK ----------> Orgo
    \                                /
     +----------- IK ----------> Da'at
                                   |
                           Kristal-native contracts
                                   |
                                Kristal
```

## Ownership

| Plane | Owner | Examples |
|---|---|---|
| civic/governance | Konnaxion | deliberation, DecisionRecord, impact/accountability |
| operational/work | Orgo | Signal, Workflow, Case, Task, IntegrationOperation |
| knowledge/epistemic | Kristal | Structured Epistemic State, Exchange, ValidationReport, AuthorityRecognition, Runtime Pack |
| Kristal boundary | Da’at | IK admission, mapping profile, Kristal pin, handoff |
| host activation | kOA-Linux when present | verify/stage/activate/rollback Runtime Pack |

## State and artifact flow

The normal cross-boundary flow is one-way with respect to authoritative ownership:

```text
participant-owned operational state
              |
              | committed local state
              v
    source-owned snapshot/export
              |
              | ExportManifest / ArtifactRef
              v
             IK
              |
              v
            Da'at
              |
              | Kristal-native mapping
              v
      Kristal-owned artifact
              |
              | ArtifactRef / Event
              v
   participant-local projection
```

A local projection, cache, index or Runtime Pack activation does not acquire ownership of the source system's operational state.

## Transaction boundary

IK does not require or define a transaction spanning participant databases. A participant commits its own state locally, then uses durable emission, idempotent processing and reconciliation for cross-owner effects. An Event announces a fact already committed by its publisher.

Invariants: unique authoritative owner, no cross-system DB writes, no distributed cross-owner commit requirement, Konnaxion↔Orgo direct by default, Kristal optional by Profile, delivery lifecycle separate from domain lifecycle, artifact reference separate from artifact ownership.

See [ADR-IK-05](adrs/ADR-IK-05-operational-state-artifact-boundary.md).
