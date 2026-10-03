# Migration v0.7 → v0.8

The v0.8 patch is safe to overlay on an existing `D:\EncyKlopedia` tree. It does not require deleting the raw Wikidata dump or the in-progress/completed compact SQLite.

## Keep

- `10_sources/wikidata/dumps/current/*`
- `30_working/wikidata/wikidata.compact.sqlite`
- existing seeds and source packages
- existing evidence/handoffs

The current global index remains useful if allowed to finish, but it is no longer a prerequisite.

## New default

```powershell
cd D:\EncyKlopedia
.\harvest_to_kristal.ps1 -Scope catholic-pilot
```

`auto` uses the global index only when it is complete; otherwise it chooses raw-dump discovery.

Force the no-global-DB path:

```powershell
.\direct_to_kristal.ps1 -Scope catholic-pilot
```

Avoid running a raw multi-pass discovery at the same time as the long global-index build unless you accept extra CPU/disk contention.

## Optional conveniences

```powershell
# Build a per-project query SQLite too
.\harvest_to_kristal.ps1 -Scope catholic-pilot -BuildQueryIndex

# Cache selected raw entities for later scopes
.\harvest_to_kristal.ps1 -Scope catholic-pilot -CacheVault

# Deliberately wait for/use the global index accelerator
.\auto_after_index.ps1 -Scope catholic-pilot
```
