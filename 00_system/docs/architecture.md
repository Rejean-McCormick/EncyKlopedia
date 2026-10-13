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

## Skope intégré (0.13.0)

Skope est un outil de l’étape `scope` et non un moteur d’ingestion autonome. Il consulte l’index global EncyK en lecture seule et prépare des propositions de scopes `encyklopedia-scope/v3` à examiner. Les arêtes de l’index compact sont agrégées et ne constituent pas des preuves statement-par-statement. Arketype v1.4 peut fournir `arketype.scope-guidance/1.0` en lecture documentaire uniquement. Le gel, l’extraction Wikidata sans perte et le handoff Médiathèque restent les étapes existantes.
