# Spek template library

Every publication **category** lives under `template_library/<category>/`.
This is one root-level namespace, not a set of peer `*-templates` directories.

- `wiki/`: implemented Arketype-to-Spek Wiki profiles; `archetype-profiles.json` is normative for this integration.
- `rhetorical/`: implemented local versioned recursive templates for organization of SemantiK phrases (no prose generation).
- `educational/`, `scientific/`, `report/`, `book/`: reserved families, not production engines.

Each category contains a `category.json` descriptor (`spek.template-category/1.0`).
`python -m spek list-template-categories` reports which are implemented vs reserved.
A directory by itself does **not** activate a renderer, a language runtime, or a publication authorization.

Reusable typed primitives remain under the separate `layouts/` root directory.
SemantiK produces phrasing; Spek composes approved inputs; the Manager holds publication authority.

Legacy `wiki-templates/` is superseded by `template_library/wiki/`.
The installer removes only the two known legacy files if their SHA-256 fingerprints are unchanged.
Customized legacy files block migration rather than being overwritten or deleted.
