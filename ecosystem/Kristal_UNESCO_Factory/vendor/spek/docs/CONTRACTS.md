# Contracts: illustrative examples (not upstream Framework schemas)

The `kristal.layout-*` namespaces below are **local experimental editorial contracts**, not released Framework or SemantiK specifications.

## Source (`kristal.layout-article-source/0.1`)

```json
{
  "format":"kristal.layout-article-source/0.1",
  "article":{"id":"article-id","title_key":"title","subtitle_key":"subtitle","abstract_key":"abstract"},
  "source":{"origin":"illustrative_fixture","state_ref":null,"state_commitment":null,"artifact_refs":[]},
  "units":[{"id":"claim.id","kind":"claim","realization_key":"claim.id","epistemic_status":"design_proposal","evidence_refs":["e.1"]}],
  "evidence":[{"id":"e.1","realization_key":"e.1","status":"local_artifact","locator":"path/to/reference"}],
  "sections":[{"id":"result","layout":"result-card","heading_key":"section-heading","slots":{"claim":"claim.id","conditions":"scope.id","evidence":["e.1"],"uncertainty":"qualifier.id"}}]
}
```

Missing slot IDs in the sketch must be defined under `units[]` in an actual valid source.

For `origin:kristal_v9`, `source.state_ref` and `source.state_commitment` must equal those in a separately supplied `kristal_state_snapshot`; each `artifact_refs[]` must be in its members. These are **reference-level checks only**. `scientific_review:approved`, `disclosure:approved`, and `language_review: {"fr":"approved","en":"approved","it":"approved"}` are additionally required for a production candidate. They are self-asserted claims until checked by outside authority.

## Realizations (`kristal.layout-realizations/0.1`)

```json
{
  "format":"kristal.layout-realizations/0.1",
  "entries": {
    "claim.id": {
      "fr": {"text":"Énoncé court.", "status":"fixture", "provider":"manual_demo_fixture"},
      "en": {"text":"Short sentence.", "status":"fixture", "provider":"manual_demo_fixture"},
      "it": {"text":"Frase breve.", "status":"fixture", "provider":"manual_demo_fixture"}
    }
  }
}
```

`status` values: `fixture`, `reviewed`, `qualified`. Qualified entries require `runtime_set_id`; no actual RuntimeSet signature, coverage certificate, or grammar verification is currently implemented. All used keys require all selected languages. Reviewer marks are not a proof of equivalence.

## Layout contracts (`kristal.editorial-layout/0.1`)

Each `slots` entry has `allowed_kinds[]`, `min`, and `max`. A missing required slot blocks compilation. Changing an existing layout's slot semantics requires a new layout version. A registry/version discipline is recommended for growth beyond this prototype.

| Layout | Required slots | Optional |
| --- | --- | --- |
| `result-card` | claim, conditions, evidence (1–4), uncertainty | implications (0–2) |
| `argument-map` | thesis, premises (1–4), inference, objection, conclusion | none |
| `comparison` | topic, criterion (1–2), approach_a, approach_b, synthesis, limitations | none |

## Build (`kristal.layout-build-manifest/0.1`)

`manifest.json` inventories every output relative path and byte digest. It includes the source/realization/layout fingerprints, generated languages, versions, and explicit `built_not_published_not_activated` lifecycle status. `mode: production_candidate` does not imply publication authorization. Run `verify-site` before transport and after checkout to detect unauthorized alterations.

## Spek v0.5 educational extension

Spek now also supports curated, read-only Ekole/Kompose **public/demo excerpts** using `spek.educational-projection/1`. Five versioned educational layout contracts are independent of the source adapter. See [Educational Layouts](EDUCATIONAL_LAYOUTS.md), [Educational Connectors](EDUCATIONAL_CONNECTORS.md), and [Educational Privacy](EDUCATIONAL_PRIVACY.md). Spek neither orchestrates missions nor certifies curricula nor authorizes restricted static publication.
