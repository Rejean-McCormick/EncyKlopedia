# EncyKlopedia v0.9 — optimized architecture

## Principle

Global data stays broad and cheap; project evidence stays complete and lossless.

```text
raw Wikidata dump = source evidence
optional compact.sqlite = broad discovery map
optional Fast Access = performance locator/reverse cache
project scope = selected QIDs
lossless entity extraction = complete Wikidata JSON
DaaT = mapping boundary
Kristal = epistemic structures/lifecycle
```

## Performance architecture

1. Prefer `json.gz` for future dumps.
2. Use `rapidgzip` multi-core when available; fall back safely.
3. Use `orjson` for parsing when available.
4. Build an optional `qid-locator.bin` and narrow reverse relation cache.
5. Use direct random access for discovery/evidence when possible.
6. Never normalize the selected raw entity before the evidence snapshot.
7. Keep the full compact SQLite optional; keep project SQLite optional.

## Interaction Kernel

The supplied IK snapshot is bundled for local contract/runtime/TCK reference. It remains a separate authority and is not silently modified by EncyKlopedia.
