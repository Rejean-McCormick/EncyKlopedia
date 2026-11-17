# Article Source Format

The article source is a **derived editorial adapter**, not the canonical Kristal data format.

## Main sections

- `format`: `kristal.layout-article-source/0.1`.
- `article`: `id`, `title_key`, `subtitle_key`, `abstract_key`.
- `source`: origin, optional pinned v9 reference, review declarations.
- `units`: stable identifiers, kinds, realization keys, epistemic statuses, evidence references.
- `evidence`: ID, realization key, locator and evidence status.
- `sections`: ordered ID, heading realization key, chosen layout, slot→unit/evidence bindings.

## Minimal binding example

```json
{
  "id": "section.finding",
  "layout": "result-card",
  "heading_key": "heading.finding",
  "slots": {
    "claim": "unit.claim",
    "conditions": "unit.scope",
    "evidence": ["evidence.one"],
    "uncertainty": "unit.limit"
  }
}
```

These IDs must refer to declared units/evidence of the right kind. All heading/text realization keys need all selected languages. Slots reject missing mandatory members and extra role names. The full working fixture is `examples/article.json`.

## Evidential obligations

A result card's evidence must also appear in its claim's evidence references. Argument maps need an evidence-linked premise. An `unknown` or unreviewed status must not be silently promoted to a proved conclusion.

## Source identity

The optional `--state-snapshot` mode compares a pinned state reference and claimed digest to supplied v9 snapshot **metadata**. This is **not** a cryptographic rehash of a Kristal JCS commitment. See [[Epistemic and Security Boundaries]].
