# Rendering and Semantic Fidelity — 0.2

Spek's editorial form must never cause a loss of scientific identity. Since v0.2, rendering proceeds from a single typed, language-specific projection: **`SpekDocument`** (`spek.document/0.2`).

## One model, multiple readers

```text
validated source + realizations + layout contracts
                         |
                         v
            project_document(model, lang)
                         |
                   SpekDocument
              /          |           \
           HTML         PDF         XeLaTeX
                         |
                  document.json
```

Every unit has the same `id`, `kind`, epistemic or evidence `status`, `evidence_refs`, optional `locator`, and realized text in the three renderers. This is a presentation-level consistency guarantee; it does not certify a Kristal state or prove translation equivalence.

The generated `fr/document.json`, `en/document.json`, and `it/document.json` make the typed projection independently inspectable. All generated files are inventoried in `manifest.json` using SHA-256.

## Readability

- Result cards group multiple evidence references rather than scattering a single third card.
- Comparison criteria carry a single label (not `Criterion: Criterion ...`).
- PDF traceability blocks stay together; the French sample no longer creates an almost-empty third page in the tested environment.
- Language-specific HTML pages offer PDF, LaTeX and JSON links when those files exist.
- All interface labels are localized in FR/EN/IT, including provenance labels.

## Fonts

The PDF generator never silently falls back to built-in Helvetica. It uses installed TrueType fonts and checks Unicode glyph coverage before rendering. On Windows it tries Segoe UI or Arial. Override with `SPEK_FONT_REGULAR` and `SPEK_FONT_BOLD` paths when necessary. For instructions, see `docs/FONTS.md` in the source repository. Fonts are not bundled.

## Repeatable verification

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m spek build --out dist --formats html,pdf,tex
python -m spek verify-site dist
```

The test suite checks the semantic slots against all renderers, PDF extraction and paging, Unicode refusal behavior, localization, manifest integrity and protected publication boundaries.

## Release boundaries

The code remains an experimental derived publishing adapter. No canonical mutations, state activation, cross-language certification, or public publishing rights are implied by a successful build.

## New in 0.3

The per-card [[Source Explorer]] presents the same source identities as structured HTML, with optional validated word annotations. When annotations are absent, only the surface tokens are shown; morphology is never inferred. The richer projection is now `spek.document/0.3` and existing PDF/LaTeX traceability is retained.
