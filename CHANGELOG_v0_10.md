# EncyKlopedia v0.10 — Index Engine consolidation

## Performance / reliability

- Global SQLite finalization is restartable with `--finalize-only`.
- Removed redundant `entity_edge(subject_id,property_id)` and `chronology(subject_id,property_id)` secondary indexes; the WITHOUT ROWID primary keys already cover those prefixes.
- Canonical global secondary indexes are now only:
  - `idx_name_norm(name.norm)`
  - `idx_presence_property(property_id,subject_id)`
  - `idx_edge_target_property(target_id,property_id,subject_id)`
- `PRAGMA optimize` replaces unconditional full `ANALYZE` in normal builds.
- Large CREATE INDEX operations use SQLite worker threads, disk TEMP, larger cache/mmap and progress heartbeats.
- Fresh global builds generate `qid-locator.bin` in the same dump pass. When the decompressor supports it, the compression seek index is exported in that pass too.
- A completed global index with the required indexes is reused immediately; relaunching the pipeline no longer rescans the dump.

## Scope / evidence

- Evidence extraction reuses the entity vault first, then random access, then only performs a full sequential dump scan when explicitly allowed.
- Production-size full scans are no longer silent. Use `--allow-full-scan` / `-AllowFullScan` to opt in. Small test dumps remain automatic.
- Reverse relation lookup uses the Global Discovery Index when present; the old P50/P170 reverse sidecar SQLite is no longer built by default.
- Scope discovery metadata is fetched in batches instead of one SQL query per entity.
- Optional project SQLite builds use batched `executemany`, a disposable `.tmp` DB with fast pragmas, then atomic rename. Full ANALYZE is removed.

## Compatibility

- Raw Wikidata remains the evidence source.
- Global/project SQLite, QID locator, compression indexes and vault remain derived accelerators.
- No writes are made directly into `40_kristal` by these changes.
