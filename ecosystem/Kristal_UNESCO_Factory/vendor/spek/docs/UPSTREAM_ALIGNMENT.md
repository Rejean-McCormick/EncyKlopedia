# Alignment with the supplied October 2026 snapshots

This prototype was designed by inspecting the user's snapshots of **Kristal Authoring Kit**, **Kristal Framework**, **Konstellation/Arketype**, and the **SemantiK phrase prototype**. No upstream source code is included here; the layout compiler is a self-contained derived experiment.

| Upstream reference in supplied archive | Requirement adopted | Current implementation |
| --- | --- | --- |
| Authoring Kit `docs/04_EPISTEMIC_AND_AUTHORITY.md` | Source testimony != proof; hypotheses must not be promoted automatically | Explicit epistemic statuses, required qualifiers and evidence refs; no promotion operation |
| Authoring Kit `docs/05_ORIENTATIONS_AND_PROJECTIONS.md` | Reader surfaces are derived and not canon | Article source is a separate derived editorial view |
| Authoring Kit `docs/19_TOOLCHAIN_ROLES.md` | Distinct Framework / C1 / C2 / Manager / C3 ownership | This prototype claims none of these authorities |
| Authoring Kit `docs/20_TOOLCHAIN_INTEROP.md` | Exact read-surface lists; no indiscriminate mirroring | Generated site contains only declared derivative files, hash-inventoried |
| Authoring Kit `docs/16_PUBLICATION_AND_ACTIVATION_V10.md` | BUILD != PUBLISH != ACTIVATE and public sync is disclosure | Offline compilation only; manual protected GitHub Pages deployment, no network release/activation |
| Framework `docs/12_BUILD_PUBLISH_ACTIVATE.md` | Separate candidate, release and active state | Output manifest status `built_not_published_not_activated` |
| SemantiK-only prototype `output/results.json` | Case/request provenance + `plain_text` one-phrase realization | Case mapping importer preserving request id and runtime id; always marks the historical fixture unqualified |
| SemantiK-only prototype `PROTOTYPE_REPORT.md` | PGF output was fixture, not an independently compiled and qualified GF runtime | No production claim; imported outputs remain fixtures until real upstream qualification |

## What this is NOT

- Not an implementation of the Framework's state commitment algorithm or official `kristal.github-read-surface/1.0`.
- Not a replacement for C1/C2 qualification, GitHub Bootstrap, Kristal Manager or C3 collection controller.
- Not a Konstellation-Light C4 public reader.
- Not a proof that a semantic mapping, source material or translated sentence is scientifically correct.
- Not a scientific manuscript submission system with complete citations/DOI/JATS metadata.

## Suggested upstream integration contract

The Authoring Kit/Framework owner can export a locally checked **semantic editorial projection** with `state_ref`, pinned source artifact IDs, a separately verified canonical commitment and disclosed permitted statements. The SemantiK owner can supply a qualified set of per-unit per-language realizations, with conformance evidence and exact request/RuntimeSet identifiers. The layout compiler can then consume only those vetted inputs and emit derived web/document artifacts.

This bridge must be designed and certified jointly with the upstream contract owners; the prototype does not silently infer semantic content from arbitrary workspace JSON.

## Spek v0.5 educational extension

Spek now also supports curated, read-only Ekole/Kompose **public/demo excerpts** using `spek.educational-projection/1`. Five versioned educational layout contracts are independent of the source adapter. See [Educational Layouts](EDUCATIONAL_LAYOUTS.md), [Educational Connectors](EDUCATIONAL_CONNECTORS.md), and [Educational Privacy](EDUCATIONAL_PRIVACY.md). Spek neither orchestrates missions nor certifies curricula nor authorizes restricted static publication.
