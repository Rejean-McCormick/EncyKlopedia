# Layout Catalog

The first Spek library contains three reusable editorial layouts. Their authoritative typed contracts live in `layouts/`.

## 1. Result card (`result-card`)

**Reader's question:** What was found, under what conditions, based on which evidence, and with what uncertainty?

**Mandatory:** `claim` (1), `conditions` (1), `evidence` (1–4), `uncertainty` (1–2). **Optional:** `implications` (0–2).

**Structure:** finding banner → conditions and evidence cards → limitation and implications. The claim's `evidence_refs` must explicitly include each evidence item in the card.

## 2. Argument map (`argument-map`)

**Reader's question:** What is asserted, why, and how does the reasoning progress?

**Mandatory:** `thesis` (1), `premises` (1–4), `inference` (1), `conclusion` (1), `objection` (1–2). At least one premise must have an evidence reference.

**Structure:** thesis → premises → explicit inference → conclusion, with objections visible rather than hidden.

## 3. Comparison (`comparison`)

**Reader's question:** How do two approaches differ against an explicit common criterion?

**Mandatory:** `topic` (1), `criterion` (1–2), `approach_a` (1), `approach_b` (1), `synthesis` (1), `limitations` (1–2).

**Structure:** topic and criterion → side-by-side approaches → synthesis and limitations. A comparison is not an endorsement unless the source actually makes that claim.

## Creating layouts

A JSON contract alone is not enough in 0.1. New IDs must be implemented in the audited HTML/TeX/PDF renderers and language label tables, and covered by tests. Read [[Layout Authoring]] for the workflow.

## v0.5 educational templates

Five additional layouts: concept card, learning path, evidence comparison, observation vs inference, and documented chronology. See [[Educational Layout Pack]].
