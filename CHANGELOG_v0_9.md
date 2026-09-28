# v0.9 — Fast Engine

- Added optional `orjson`, `rapidgzip`, and `indexed_bzip2` backends with standard-library fallbacks.
- Added automatic physical-core thread recommendation.
- Added binary QID locator (`qid-locator.bin`) for direct raw-entity access.
- Added narrow reverse-edge accelerator (`P50`, `P170` by default).
- Added reusable gzip/bzip2 decompressor block indexes when the installed backend supports them.
- Added `fast` scope-discovery backend; `auto` now chooses global index → fast access → raw scan.
- Evidence extraction automatically uses Fast Access random reads when possible and falls back to a single sequential scan when not.
- Future dump discovery supports both `.json.gz` and `.json.bz2`; `auto` prefers gzip when rapidgzip is installed.
- Compact global index builder now supports gzip/bzip2/plain through the shared fast backend and uses `orjson` when present.
- Added performance GUI controls and PowerShell shortcuts.
- Bundled the supplied Interaction-Kernel snapshot for contract/runtime/TCK reference; upstream remains authority.
