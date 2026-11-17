# Native knowledge model — design candidate

A vocabulary list is necessary but insufficient. Use distinct objects for:

| Object | Required distinctions |
| --- | --- |
| `Concept` | stable UNESCO ID, labels, source URI, branch membership; vocabulary only |
| `DefinitionCandidate` | wording, source, locator, intended sense, review state |
| `PolicyInstrument` | authority, intended population, scope, effective dates, implementation status |
| `Institution` | role, jurisdiction, validity period, source |
| `Population` | eligibility/measurement boundaries and sensitive classifications as sourced |
| `Indicator` | definition, producer, denominator, year, territory, uncertainty |
| `Claim` | typed relation or statement, time/place applicability, evidence, counterevidence, review |
| `Evidence` | source identity, locator, author, publication/version date, licensing, appraisal |
| `PolicyEvent` | proposal/adoption/implementation/repeal/evaluation must not collapse into one fact |

Relationships include UNESCO SKOS links, `implements`, `governed_by`, `targets`, `financed_by`, `measured_by`, `supported_by`, `contested_by` and external `cross_branch_reference` edges. Proposed edge names are **editorial modelling suggestions**, not unilaterally introduced Framework contract identifiers.

Canonical enrichment requires separately reviewed KQ/KP/KA/KS and the authoritative external Authoring Kit. Until then, store any proposed facts under `derived/` with `not_canon = true`.
