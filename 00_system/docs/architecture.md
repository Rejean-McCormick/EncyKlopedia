# EncyK architecture — 0.12

EncyK has one job:

> **discover → acquire → extract → handoff**

It is an intake pipeline, not a source repository, semantic compiler, or knowledge authority.

```text
external sources
      │
      ▼
    EncyK
 discover / acquire / scope / lossless extract
      │
      │ encyk.source-evidence-handoff/2.0.0
      ▼
Médiathèque kOA
 persistent Source → Snapshot → Representation authority
      │
      │ owner-preserving references / ArtifactRefs
      ▼
Interaction Kernel (optional)
      │
      ▼
DaaT (`daat`)
 explicit admission + contract mapping
      │
      ▼
Kristal portable (`kristal_state/6.0`)
      │
      ▼
Kristall v7
 semantic identity / Mesh / axes / registries / crystallization
      │
      ▼
Kompiler
 read-only context compilation
```

## What EncyK owns

- discovery rules and project scopes;
- acquisition logic and transient acquisition caches;
- frozen selection intent;
- lossless extraction of admitted source records;
- source-qualified external identity candidates;
- a content-addressed handoff bundle to Médiathèque.

## What EncyK does not own

- persistent canonical source bytes or source locators — **Médiathèque**;
- corpus-wide semantic normalization or context compilation — **not EncyK**; Kompiler is read-only context compilation downstream;
- IK admission and Kristal mapping — **DaaT** when that integration path is used;
- KQ/KP/KA/KS identity, Mesh, axes, registries or crystallization — **Kristal/Kristall**;
- final epistemic assertions — **Kristal/Kristall**.

## Evidence retention

`20_evidence/` is an outgoing evidence/handoff workspace, not a permanent source library. An operator may retain bundles for audit/retry, but accepted durable source storage belongs in Médiathèque. Derived caches/indexes belong in `30_working/` or `90_runtime/` and are rebuildable.
