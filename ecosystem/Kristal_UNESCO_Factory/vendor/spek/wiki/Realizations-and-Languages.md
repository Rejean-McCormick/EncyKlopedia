# Realizations and Languages

Each used realization key must have **one non-empty entry for every requested language**. A source can use the same unit IDs for all languages, but must not assume that a short expression is automatically accurate in another language.

## Realization shape

```json
{
  "format": "kristal.layout-realizations/0.1",
  "entries": {
    "unit.claim": {
      "en": {"text": "A short expression.", "status": "fixture", "provider": "manual_demo"},
      "fr": {"text": "Un énoncé bref.", "status": "fixture", "provider": "manual_demo"},
      "it": {"text": "Un enunciato breve.", "status": "fixture", "provider": "manual_demo"}
    }
  }
}
```

Entries can declare `fixture`, `reviewed`, or `qualified`. **These are input declarations, not independently authenticated facts.** Qualified entries must include a nonempty `runtime_set_id`; production workflows also require independent language and disclosure approvals.

## Strict no-fallback behavior

- Missing English, French, or Italian entries block the build when that language is requested.
- Unrecognized languages block compilation (0.1 supports only `en`, `fr`, `it`).
- The imported historical SemantiK fixture never invents missing translations.
- Translating label text does **not** change the unit IDs or evidence references.

## Future qualification

An independently verified SemantiK integration should pin the RuntimeSet, preserve request identity, validate terminology, and record signed or otherwise authenticated review outcomes. Spek cannot perform that verification today.
