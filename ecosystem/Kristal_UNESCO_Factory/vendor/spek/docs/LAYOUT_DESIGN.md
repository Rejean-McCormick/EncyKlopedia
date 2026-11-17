# Layout design

Spek separates **semantic role**, **language realization**, **argumentative organization**, and **format-specific styling**. A layout is not freeform prose: it is a versioned contract that tells the compiler which semantic roles are necessary and how they will be presented.

## Design principles

1. **Typed**: every slot lists `allowed_kinds`. A `thesis` cannot be slipped into a `claim` slot unless the contract explicitly permits it.
2. **Complete**: minimum and maximum slot cardinalities are checked before rendering.
3. **Traceable**: presentation units keep stable semantic identifiers, evidence references, and source hashes.
4. **Epistemically explicit**: the reader can see scope, evidence, qualifiers, and counterarguments.
5. **Language-agnostic structure**: the same source slots are reused in all rendered languages.
6. **Accessible and scannable**: headings, parallel cards, comparisons, and ordered inference paths clarify the document without pretending to synthesize new science.

## Existing layout catalog

| ID | Slot | Expected kind | Cardinality |
| --- | --- | --- | --- |
| result-card | claim | `claim` | 1 |
| result-card | conditions | `scope` | 1 |
| result-card | evidence | `evidence` | 1..4 |
| result-card | uncertainty | `qualification` | 1..2 |
| result-card | implications | `implication` | 0..2 |
| argument-map | thesis | `thesis` | 1 |
| argument-map | premises | `premise` | 1..4 |
| argument-map | inference | `inference` | 1 |
| argument-map | conclusion | `conclusion` | 1 |
| argument-map | objection | `objection` | 1..2 |
| comparison | topic | `question` | 1 |
| comparison | criterion | `criterion` | 1..2 |
| comparison | approach_a | `approach` | 1 |
| comparison | approach_b | `approach` | 1 |
| comparison | synthesis | `conclusion` | 1 |
| comparison | limitations | `qualification` | 1..2 |

Exact field details are authoritative in `layouts/*.json`.

## Anatomy of a layout contract

```json
{
  "format": "kristal.editorial-layout/0.1",
  "id": "result-card",
  "version": "1.0.0",
  "slots": {
    "claim": {"allowed_kinds": ["claim"], "min": 1, "max": 1}
  }
}
```

The above is shortened for illustration; open `layouts/result-card.json` for all mandatory slots.

## How to add a layout today

1. Write a new `layouts/<id>.json` with a unique layout ID and bounded typed slots.
2. Add a renderer branch in `spek/render.py` for `section_html`, `article_tex`, and `article_pdf` as applicable.
3. Add human-language labels to `spek/locale.py` for all supported languages.
4. Add an article section in the example or a dedicated fixture, along with realizations for every required language.
5. Add positive and negative tests in `tests/` (wrong type, missing evidence, missing translation, escaping).
6. Run full tests and visual review of HTML, TeX, and PDF.

**Important:** Layout JSON by itself does not generate arbitrary structures. The current version deliberately has named, audited renderer branches. A future general slot-driven renderer is on the roadmap.

## Formatting versus meaning

A layout decides **where** a finding, proof, and qualification appear—not whether the finding is true. Changing from a two-column desktop card to a mobile stack does not change the semantic claims. Changing which evidence supports a claim **does**, and requires a new validated input build.
