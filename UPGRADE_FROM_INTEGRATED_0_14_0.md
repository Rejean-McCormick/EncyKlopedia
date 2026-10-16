# EncyK 0.14.0 — Clean rebuild, standalone Skope alignment

This ZIP is a **complete clean EncyK code tree**, rebuilt from the most recent
full EncyK source snapshot furnished to this conversation (`0.13.17`, 2026-10-14),
**not** an overlay to extract on top of an existing EncyK checkout. The old
embedded Skope is **absent**. Skope Standalone 0.14.1 remains an independent
application.

## Installation on Windows (PowerShell 7)

1. Stop any EncyK manager processes and the *old* integrated Skope launcher;
   Skope Standalone may continue running on port 8767.
2. Keep all existing D: data and Kristal workspaces untouched. Rename the old
   *code repository directory* on C: to a clearly named backup. Verify the old
   code directory is not a reparse-point itself before renaming (the D: data
   junctions within the repo should not be followed).
3. Create an **empty** `C:\mycode\EncyKlopedia\EncyKlopedia` directory. Extract
   this ZIP's **contents** directly into it (so `MANIFEST.json` is at the root).
4. Check the code and source/disk separation before creating data links:

```powershell
$repo = 'C:\mycode\EncyKlopedia\EncyKlopedia'
Set-Location $repo
python -B '.\00_system\tools\validate_repo.py'
pwsh -NoProfile -ExecutionPolicy Bypass -File '.\configure_data_on_D.ps1'
```

5. Review the plan and **only then**, if the new repo needs D: junctions, run:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File '.\configure_data_on_D.ps1' -Apply
```

6. Use `EncyKlopedia_Manager.cmd` and open the **5 · Skope externe** tab.

**Do not extract this full ZIP into the old folder as an overlay:** ZIP extraction
alone does not delete obsolete `00_system/tools/skope/` or `Lancer_Skope.pyw`.
Do not delete anything under `D:\EncyKlopedia` or existing Kristal folders.

## EncyK's responsibilities after decoupling

- Wikidata Manager and global compact SQLite indexing (unchanged).
- Scope Builder, root discovery and lossless Wikidata JSON extraction (unchanged).
- Fast-access reader and existing compressed dump sidecars (unchanged).
- Médiathèque source-evidence handoff v2 (unchanged; updated release validation).
- **NEW:** optional standalone Skope HTTP client that pulls completed inventories
  as external noncanonical source intakes with validated QIDs and SHA-256.

No Skope server, UI, wizard or Python package is shipped inside EncyK.
The **density visualizer** belongs to Skope Standalone, not EncyK.

## Limitations

- The bridge downloads completed QID ZIP results. It **does not** retrieve the
  full original Wikidata JSON evidence chunks; their location may be referenced
  in author-campaign metadata, not independently verified by this pull.
- The bridge does not convert QIDs automatically into a frozen EncyK scope or
  accepted Médiathèque publication. A future explicit conversion contract can
  be implemented on top of the imported QID files.
- Live Windows operation with your 125 GiB SQLite and local Skope service has
  not been executed in this environment. All tests use small fixtures, plus one
  previously supplied real completed Skope inventory ZIP.
