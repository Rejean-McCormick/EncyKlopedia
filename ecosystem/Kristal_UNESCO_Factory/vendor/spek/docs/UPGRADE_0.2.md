# Upgrading Spek 0.1 to 0.2

Spek 0.2 is a local rendering and semantic-fidelity release. It retains the **0.1 input and layout JSON format identifiers**, so existing valid `examples/article.json`, `examples/realizations.json` and the three layout contracts remain compatible.

## What changed

- A `spek/document.py` projection (`spek.document/0.2`) is constructed from the validated `Compiled` model for **each language**. All three renderers consume the same projection.
- Every exported unit now carries an **ID, kind, epistemic/evidence status, evidence reference IDs, and evidence locator when applicable**. HTML exposes `data-*` attributes and visible trace lines; PDF and LaTeX render visible trace lines.
- The compiler writes `fr/document.json`, `en/document.json`, and `it/document.json`, with the exact published per-language section/slot graph. As a result, a complete FR/EN/IT HTML+PDF+TeX demo now has **13 hashed output files**, not 10.
- PDF pagination spacing and trace grouping were corrected. The sample French PDF is verified to fit on two pages on the Linux test environment and checked in automated tests.
- PDF fonts are discovered from installed system TrueType fonts, or specified via environment variables; missing Unicode glyphs cause an explicit error rather than silent substitution.
- All three HTML pages link to whichever formats are included in the build, as well as the intermediate JSON.
- Labels including Source / Realizations / Layouts are localized FR, EN, IT. Comparison criteria are no longer double-prefixed in PDF.
- Tests now validate PDF page count, unit IDs, hashes, semantics and format links. The `pypdf` dependency is required for these checks.

## Upgrade commands — Windows PowerShell

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m spek check
# If you already have a verified dist from v0.1, Spek validates it first and replaces it atomically.
python -m spek build --out dist --formats html,pdf,tex
python -m spek verify-site dist
python -m http.server 8000 --directory dist
```

Inspect `http://localhost:8000/fr/`, `http://localhost:8000/en/`, `http://localhost:8000/it/` and use the new PDF, LaTeX and JSON links.

## Unchanged boundaries

Build success is not scientific validation or permission to publish. The sample source is a demonstration fixture. This release does not verify canonical JCS commitments, certify SemantiK/GF RuntimeSets, or authorize public GitHub deployment. Human linguistic and scientific review remain required.

## Known limitations

- Only three built-in editorial layout renderers are implemented; contract-defined arbitrary layout execution is not supported.
- No automatic text generation or paragraph realization is introduced.
- Complex scripts, right-to-left shaping and cross-platform pixel-identical PDFs are not guaranteed.
- PDF card content of extraordinary length may need to be split into smaller semantic units.
- Document model `spek.document/0.2` is a **derived inspectable artifact**, not a new Kristal canonical object.
