# Getting Started

## Requirements

- Python 3.10 or newer.
- Local checkout of the Spek repository.
- ReportLab for PDF (`pip install -r requirements.txt`). No network is required when building after dependencies are installed.
- Optional XeLaTeX to typeset the emitted `.tex` files into PDFs with a TeX toolchain.

## First run

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m spek check
python -m spek build --out dist --formats html,pdf,tex
python -m spek verify-site dist
python -m http.server 8000 --directory dist
```

Open <http://localhost:8000/>. Use the language links to see English, French, and Italian presentations of the same semantic units.

## Your first article

1. Copy `examples/article.json` and `examples/realizations.json` to your working directory.
2. Give the derived article a unique ID, then define semantic units, evidence and typed section/slot bindings.
3. Supply a short reviewed expression for every referenced realization key and required language.
4. Run `check` with `--source`, `--realizations`, and `--layouts`.
5. Build to a fresh output directory, inspect, verify hashes, and conduct human review.

```bash
python -m spek check --source article.json --realizations realizations.json --layouts layouts
python -m spek build --source article.json --realizations realizations.json \
  --layouts layouts --languages en,fr,it --formats html,tex,pdf --out dist
```

Use [[Layout Catalog]] and [[Article Source Format]] for field-level details. A demonstration build is not publication clearance.

## Try the educational preview (v0.5)

On Windows: `scripts\demo-education.bat`. Elsewhere see [[Ekole Integration]] and [[Kompose Integration]]. All content is fictional and remains local preview only.
