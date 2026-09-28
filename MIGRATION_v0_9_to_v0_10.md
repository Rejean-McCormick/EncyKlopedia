# Migration v0.9 → v0.10

The existing completed `wikidata.compact.sqlite` is preserved. Do **not** rebuild it.

After installing v0.10:

```powershell
cd D:\EncyKlopedia
.\finalize_wikidata_index.ps1 -Threads 8
```

For the current completed v3 database this is idempotent and should skip all three indexes; it only normalizes metadata/optimizer state.

The current `.json.bz2` dump cannot provide fast random access unless an `indexed_bzip2` backend is importable. v0.10 therefore refuses to silently rescan the entire production dump during evidence extraction. To explicitly accept that cost:

```powershell
.\auto_after_index.ps1 -Scope catholic-pilot -AllowFullScan
```

For future dumps prefer `.json.gz` + `rapidgzip`; fresh global builds create the QID locator in the same pass.
