# EncyK ↔ Skope standalone — pull-only bridge v1.0

**Producer**: Skope standalone v0.14.1 (not vendored in EncyK).
**Consumer**: EncyK v0.14.0 (`00_system/integrations/skope_bridge.py`).
**Transport**: GET over `http://127.0.0.1:8767`, or another explicitly configured loopback port.
**Trust model**: remote local process is independent and *not authority for source claims*.

## Supported GET routes

- `/api/config`, `/api/meta` — read-only server/config/index context.
- `/api/large/latest`, `/api/large/status?job=<32 hex>` — completed QID inventory status.
- `/api/large/result.zip?job=<32 hex>` — bounded Skope QID result ZIP.
- `/api/author-campaign/latest`, `/api/author-campaign/status?job=<32 hex>` — optional person and works metadata.
- `/api/extract/latest` — optional extraction status and reported evidence path; original JSON blobs are **not** downloaded through this bridge.

The bridge does NOT call `/api/large/start`, `/api/extract/start`, `/api/author-campaign/start`, or mutate any Skope job.

## Data model

The client accepts only completed jobs. It validates QID inventory ordering,
count, source manifest (when supplied), ZIP entry whitelist/CRC, byte caps,
hex job IDs, and the Skope status. An explicit *pull* writes:

`D:\EncyKlopedia\20_evidence\external-intake\skope\<job-id>\`

- `results.zip` — exact Skope result bytes, SHA-256 in receipt.
- `selected-qids.jsonl` — validated, unique QIDs (sorted by numeric ID).
- `recipe.json` — original Skope selection intent (no execution).
- Optional `summary.json`, `matched-people.jsonl`, `unresolved-people.jsonl`, `author-work-links.jsonl`, `provenance-manifest.json`.
- `receipt.json` — `encyk.skope-pull/1.0` receipt; versioned, with source job metadata, checksum and explicit limitations.

Import is immutable and idempotent. A previous import with changed bytes fails instead of overwriting it.
No Kristal canon, original Wikidata dump, EncyK SQLite, Skope runtime, or accepted source catalog is modified by the bridge.

## Rights and upstream ownership

An extracted inventory is a **selection list**, not Wikidata complete source evidence.
Original full source JSON (including statements/references) may already exist
under the independent Skope evidence root; a reported path is not an independently verified source record.
Promotion to EncyK's separate scope freeze/extraction/Médiathèque handoff pipeline
requires an explicit future conversion and validation step. No automatic canon write.
