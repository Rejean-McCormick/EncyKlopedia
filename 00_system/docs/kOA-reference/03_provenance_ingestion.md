# Layer 03 — Provenance / Ingestion

## 1. Function

The Provenance / Ingestion layer captures external material before it becomes knowledge.

Its function is to bring raw inputs into kOA in a way that is:

- traceable;
- reproducible;
- auditable;
- content-addressed where possible;
- policy-aware;
- safe for downstream processing.

This layer does not decide what is true. It preserves what entered the system, where it came from, under what context, and how it was captured.

In the kOA Digital Ecosystem, the main technical node corresponding to this layer is **Chokmah — Inputs**, the ingest and provenance boundary.

## 2. Core question

> What did the system receive, from where, under what conditions, and can that exact input be referenced again?

This layer answers the pre-knowledge question:

> Before we interpret, validate, deliberate, decide, or act — what exactly did we see?

## 3. Internal kOA components

Primary internal components:

- **Chokmah** — ingest and provenance boundary;
- **Input Snapshot** — immutable captured input;
- **Input Snapshot Set** — stable set of snapshot references;
- **Snapshot Manifest** — provenance and acquisition metadata;
- **Ingest Receipt** — result of an ingestion attempt;
- **Quarantine Report** — optional report when material is blocked, restricted, unsafe, or requires special handling;
- **Orgo Build Record** — downstream operational record binding builds to stable input references;
- **Mandate / policy tags** — constraints inherited from the mandate and blueprint context.

Related technical references:

- `docs/2-Technical-Reference/20-nodes/chokmah-inputs.md`
- `docs/2-Technical-Reference/10-system/architecture.md`
- `docs/2-Technical-Reference/10-system/lifecycle.md`
- `docs/2-Technical-Reference/30-artifacts/build-record.md`
- `docs/2-Technical-Reference/30-artifacts/mandate-bundle.md`
- `docs/2-Technical-Reference/60-guides/integrators.md`


## 4. Inputs

This layer receives raw material from configured sources.

Typical inputs include:

- files;
- feeds;
- APIs;
- user submissions;
- curated evidence bundles;
- source documents;
- uploads;
- connectors;
- external datasets;
- prior artifact references;
- contextual metadata;
- mandate and policy tags;
- confidentiality classifications;
- retention or quarantine directives.

The input is not yet trusted knowledge. It is material to be captured.

## 5. Outputs

This layer produces stable references and ingestion evidence.

Primary outputs:

- **Input Snapshot Set**
  - one or more content-addressed snapshot references;

- **Snapshot Manifest**
  - mapping from snapshot reference to provenance and acquisition metadata;
  - source identity;
  - retrieval time;
  - authority or authentication context;
  - routing tags;
  - policy tags;
  - deterministic transformation steps, if any;
  - integrity metadata such as hashes or checksums;

- **Ingest Receipt**
  - snapshot references created or confirmed;
  - warnings;
  - errors;
  - partial result indicators;
  - diagnostics references;

- **Quarantine Report**, when applicable
  - blocked content;
  - unsafe content;
  - restricted content;
  - policy violation;
  - classification mismatch;
  - malware or sensitive data handling.

The downstream system should depend on recorded snapshot references, not live sources.

## 6. External vocabulary

Comparable external terms:

- provenance;
- data lineage;
- source traceability;
- evidence chain;
- chain of custody;
- immutable snapshot;
- content-addressed input;
- audit trail;
- reproducible input reference;
- ingestion boundary;
- source metadata;
- input manifest;
- evidence intake;
- acquisition metadata.

Useful external framing:

> Provenance / Ingestion is kOA’s source traceability layer.

Or:

> It is the layer that preserves evidence before interpretation.

## 7. Boundary rules

This layer may capture, package, and reference inputs.

It must not silently interpret them.

### This layer may

- ingest raw material;
- store immutable snapshots;
- record provenance;
- normalize transport or container formats if deterministic and explicitly recorded;
- classify confidentiality and handling requirements;
- produce deterministic ingest results;
- quarantine material under policy;
- emit stable references for downstream processing.

### This layer must not

- decide truth;
- create canonical knowledge;
- alter meaning silently;
- “fix” content without recording the transformation;
- enrich content as if the enrichment were part of the original source;
- allow downstream stages to depend on mutable live sources;
- erase provenance;
- hide transformation steps;
- leak restricted or confidential material downstream.

## 8. Invariants

### 8.1 Immutability

Once a snapshot reference is issued, the referenced bytes must not change.

If the source changes, a new snapshot is created.

### 8.2 Content addressing

Same payload bytes should resolve to the same snapshot reference, subject to the defined packaging rules.

Metadata changes belong in the manifest, not in the payload identity.

### 8.3 Complete provenance

Every snapshot must have enough provenance for audit and reproduction:

- where it came from;
- when it was retrieved;
- under which policy or authority context;
- what access constraints applied;
- what transformations were applied;
- which tools or adapters were involved.

### 8.4 Idempotent ingestion

Re-ingesting the same payload should return the same reference.

Retries must not create duplicate distinct snapshots for identical bytes.

### 8.5 Confidentiality enforcement

Restricted material must remain access-controlled.

Downstream stages should receive references unless explicitly authorized to fetch bytes.

### 8.6 No hidden enrichment

The ingestion layer captures material. It does not introduce new facts.

Any derived interpretation belongs to a later layer.

### 8.7 Build reproducibility

Orgo must be able to bind a build to a stable input set.

Downstream compilation must depend on recorded snapshot references, not mutable external sources.

## 9. Relation to other layers

### Previous layer

Layer 02 — **Semantics / Meaning**

The semantic layer defines the concepts, categories, and meaning structures that help describe inputs and route them properly.

### This layer

Layer 03 — **Provenance / Ingestion**

Captures raw material with traceability before interpretation.

### Next layer

Layer 04 — **Structured Knowledge**

Transforms provenance-preserved inputs into structured claims, evidence objects, Kristal-adjacent artifacts, and eventually validated knowledge.

The transition is:

```text
Raw external material
→ provenance-preserved snapshots
→ structured proposals / claims
→ validation
→ canonical knowledge
```
## 10. Failure mode if absent

Without this layer, the system cannot reliably know what its knowledge is based on.

Typical failures:

* sources are cited but cannot be reproduced;
* live external data changes without record;
* claims lose their evidence chain;
* downstream outputs cannot be audited;
* participants dispute what was originally submitted;
* restricted material leaks;
* transformations alter meaning silently;
* builds cannot be reproduced;
* validation becomes unverifiable;
* memory becomes anecdotal rather than evidential.

The result is epistemic drift:

> The system may appear to know, but it can no longer prove what it saw.

## 11. Failure handling

This layer should fail closed when it cannot guarantee correct capture or provenance.

Common failure cases:

* source unreachable;
* authentication failure;
* partial download;
* truncated payload;
* hash mismatch;
* unsupported format;
* unsafe content;
* policy violation;
* classification mismatch;
* storage failure;
* inability to commit immutable snapshot;
* malformed content that violates declared constraints.

Expected behavior:

* stop ingestion where required;
* return stable error codes;
* preserve diagnostic references;
* quarantine when required;
* avoid coercing malformed content into a false-valid state;
* avoid downstream continuation without sufficient provenance.

## 12. Observability

This layer should emit enough observability to support debugging, auditing, and rebuilds.

Useful signals:

* ingest adapter identity;
* ingest adapter version;
* configuration reference;
* source descriptor reference;
* snapshot ID;
* snapshot set reference;
* manifest reference;
* retrieval timestamp;
* policy tag reference;
* classification applied;
* transformation steps;
* warnings;
* stable error codes;
* diagnostics references;
* correlation ID;
* build ID or request ID when available.

## 13. Example flow

```text
1. Orgo receives or schedules an ingest request.
2. Chokmah reads the source descriptor.
3. Chokmah fetches the source material.
4. Chokmah stores the exact retrieved bytes as an immutable snapshot.
5. Chokmah records provenance and acquisition metadata in a snapshot manifest.
6. Chokmah emits an ingest receipt.
7. Orgo binds the input snapshot set to a build context.
8. Downstream extractors use snapshot references, not live sources.
```

## 14. Layer definition

**Provenance / Ingestion** is the layer where external material enters kOA as traceable, immutable, policy-aware input references before it can become structured knowledge.

## 15. One-sentence definition

Provenance / Ingestion preserves exactly what kOA received, where it came from, and under what conditions, so downstream knowledge, decisions, actions, and memory remain auditable and reproducible.

