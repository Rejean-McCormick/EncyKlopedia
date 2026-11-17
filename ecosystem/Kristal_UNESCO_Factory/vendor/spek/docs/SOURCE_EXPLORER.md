# Source Explorer — Spek 0.3

Spek's Source Explorer places a **per-card "Explore source" control** inside each HTML card. The normal reading view stays concise; opening one card reveals **structured** semantic, linguistic, and provenance details. There is no raw JSON in the reader interface.

## What a card exposes

1. **Semantic source** — stable unit ID, role, epistemic qualification, document origin, and the supplied Kristal state reference (or an explicit "Not supplied").
2. **Language realization** — phrase key, provider, status, optional request identity and RuntimeSet.
3. **Words and attributes** — surface tokens with character offsets, optional lemma, part of speech, morphological features, lexeme/semantic identifiers and GF-function references.
4. **Evidence and references** — linked evidence descriptions, types/statuses and locators.
5. **Provenance** — fingerprint of the input article source. The full source/realization/layout fingerprints remain in the page footer and the build manifest.

A card with multiple items (for example, two premises or two evidence objects) has **one toggle**, but separate source records for each member.

## Important: surface segmentation is not linguistic analysis

When a realization supplies no token metadata, Spek **only segments the visible phrase for display**. It does not derive lemmata, part of speech, semantic senses, agreement, GF abstract syntax, or morphology. In the explorer these attributes say **Not supplied** and each token is marked **Surface only**.

The demonstration includes *two manually annotated tokens* in each language for one evidence phrase. These fields are marked `manual_fixture`, **not** output from a certified SemantiK GF/PGF RuntimeSet.

## Optional token annotations

Entries in `examples/realizations.json` may include partial annotations:

```json
{
  "text": "Declarative contracts ...",
  "status": "fixture",
  "provider": "manual_demo_fixture",
  "tokens": [
    {
      "surface": "Declarative",
      "start": 0,
      "end": 11,
      "lemma": "declarative",
      "pos": "ADJ",
      "features": {},
      "annotation_status": "manual_fixture"
    }
  ]
}
```

`start` is inclusive and `end` exclusive, using Python Unicode code-point indices. The token's surface **must equal** `text[start:end]`, and its span must equal a full display token. A token may optionally have `lexeme_ref`, `semantic_ref`, or `gf_function`, but Spek never populates those from guesses. Every annotation requires one of `manual_fixture`, `reviewed`, or `qualified`. Qualified token annotations require a qualified realization, and **do not confer independent scientific or linguistic certification**.

The compiler rejects duplicate or inconsistent token spans and unsafe/malformed annotation fields. Text and attributes are escaped in HTML.

## Accessibility and offline operation

Each card has a native HTML `<details>`/`<summary>` fallback that works **without JavaScript**. For browsers with JavaScript enabled, a small bundled script upgrades the same control into a full-width, keyboard-accessible native `<dialog>` panel, with a Close button and Escape-key dismissal. This makes the word-attribute table readable without compressing it into a narrow evidence card. Both modes work completely offline, without network calls, accounts or browser extensions. Mobile word tables scroll **inside** the panel.

## Scope

Source Explorer is a **web-reader capability** in v0.3. PDF and LaTeX retain their current inline semantic trace, while the common `spek.document/0.3` projection and `document.json` sidecars retain the richer token and evidence data. No public publication, certification, or external state activation is performed by opening a source panel.
