# Layout Authoring

Spek's contracts encode **semantics required for a representation**; CSS and format-specific rendering are separate.

## Contract shape

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

This is a deliberately shortened example. A real contract needs its full set of slots, as in `layouts/result-card.json`.

## Safe authoring process

1. Define the reader's purpose and the logical flow.
2. Define required and optional typed slots and cardinality.
3. Decide how proof, applicability, uncertainty, objections, and provenance are visible.
4. Add a renderer branch in `spek/render.py` for HTML, TeX, and PDF.
5. Add label translations in `spek/locale.py`.
6. Create representative source + realization fixtures and negative tests.
7. Compare reading order, identity, and omissions across formats and languages.

## Layout versioning

Breaking changes to required slots or meaning should produce a new version. Visual changes that preserve meaning can be evaluated separately. Version IDs in the output manifest permit regression comparisons.

## Current limitation

The JSON layout library is **not yet** a generic interpreter for arbitrary custom designs. Three named renderer implementations are provided. Generalized rendering is planned but not implied.
