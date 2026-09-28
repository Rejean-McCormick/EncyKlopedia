# Migration v0.8 → v0.9

Extract the v0.9 patch over the existing `D:\EncyKlopedia` root.

Existing assets are preserved:

- current `.json.bz2` dump;
- ongoing/finished `wikidata.compact.sqlite`;
- scopes and evidence snapshots;
- Mediatheque candidates;
- Da'at handoffs.

Recommended once after upgrading:

```powershell
cd D:\EncyKlopedia
.\optimize_performance.ps1
.\benchmark_wikidata.ps1
```

Do **not** restart a compact-index process already running merely to gain v0.9. Let it finish. For the next Wikidata snapshot, prefer `.json.gz` and build Fast Access once if repeated scope work is expected.
