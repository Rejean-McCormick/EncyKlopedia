# EncyK Fast Engine — 0.12

The performance layer is an **optional accelerator**. It never becomes evidence or epistemic authority.

## Fast path

```text
Wikidata .json.gz
      ↓ rapidgzip (multi-core)
minimal one-pass Fast Access build
      ├── qid-locator.bin       QID → decoded byte offset/line length
      ├── fast-index.sqlite     only selected reverse relations (P50/P170 by default)
      └── compression.gzindex   rapidgzip block index
            ↓
scope discovery
            ↓ direct random reads
lossless raw Wikidata entities
            ↓
Médiathèque handoff
```

The locator is deliberately not a semantic database. It says **where the raw entity is**, not what the entity means.

## Recommended Windows/Python 3.14 setup

```powershell
cd C:\mycode\EncyKlopedia\EncyKlopedia
.\optimize_performance.ps1
.\benchmark_wikidata.ps1
.\prepare_fast_access.ps1
```

`optimize_performance.ps1` installs optional `orjson` and `rapidgzip` into the current Python environment. If installation is impossible, all pipelines retain standard-library fallbacks.

### Existing `.json.bz2`

It remains supported. `indexed_bzip2` is used automatically if importable. On Windows CPython 3.14, a prebuilt wheel may not be available, so the standard `bz2` fallback remains valid. Do not restart a long-running existing compact-index build merely to enable v0.9.

### New dumps

For future downloads, `.json.gz` is preferred because `rapidgzip` can parallelize decompression and provide indexed random access on ordinary gzip files.

## Fast Access size

The QID locator uses 16 bytes per numeric QID slot and is truncated to the highest QID observed. At roughly 160 million QIDs, that is about 2.4 GiB. The reverse SQLite contains only configured reverse properties, not every Wikidata claim.

## Reverse properties

Defaults:

- `P50` author — essential for `work → author → person` discovery.
- `P170` creator — useful for broader authored/created works.

Add more only when a project actually needs reverse lookup. Outgoing relations are read losslessly from the raw entity itself.

## Threads

`0` means automatic. EncyKlopedia prefers physical cores from `00_system/config/environment.json` and caps the default at 12. On the known Ryzen 7 5800HS machine this resolves to 8 worker threads.


## Consolidation

The Global Discovery Index now serves reverse relation lookup. `build_fast_access.py` therefore focuses on the QID locator and decompressor seek index and does **not** build a duplicate P50/P170 SQLite when the global index is available.

Production-size sequential evidence scans are no longer automatic. If the current decompressor cannot random-seek the dump, evidence extraction stops before spending hours scanning. Use `-AllowFullScan` only when that cost is intentional. Small test dumps remain automatic.

Fresh global builds emit `qid-locator.bin` in the same pass as `wikidata.compact.sqlite`; supported decompressor seek indexes are exported in that pass too.
