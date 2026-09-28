# v0.8 — direct evidence pipeline

- Global compact SQLite is now optional, not mandatory.
- Added discovery backends: `auto`, `index`, `raw`.
- Raw mode can resolve names and discover people-centred scopes directly from the Wikidata dump.
- Added `04_extract_evidence.py`: one direct sequential dump scan for the union of frozen scopes, writing complete selected entity JSON.
- Entity vault is now optional cache only.
- Per-project SQLite is now optional (`--build-query-index`) and is no longer required by UCKK Mediatheque or Da'at handoff.
- UCKK Mediatheque candidates are generated directly from lossless evidence.
- Da'at handoff v3 is rooted directly in frozen scope + evidence, with optional indexes only as derived conveniences.
- Added Interaction Kernel reference docs from the supplied kOA snapshot; no IK runtime/conformance is claimed.
- Catholic pilot has explicit verified Wikidata roots Q8018 and Q9438.
- Added `direct_to_kristal.ps1` for an explicitly DB-free discovery path.
