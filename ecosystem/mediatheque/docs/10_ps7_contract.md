# 10 — PowerShell 7 Contract

**Project:** Médiathèque kOA  
**Technical name:** `koa-mediatheque`  
**Status:** AI-only final target specification  
**Audience:** AI coding conversations only  
**Rule:** All implementation conversations must start from `01_alignment_variables.md`.

---

## 1. Purpose

PowerShell 7 scripts provide deterministic writes and imports to SQLite.

The GUI may call these scripts or equivalent internal functions.

---

## 2. Required scripts

```text
Initialize-KoaMediathequeDb.ps1
Add-KoaLibraryRow.ps1
Export-KoaLibraryXlsx.ps1
Import-KoaLibraryXlsx.ps1
Compare-KoaLibraryXlsx.ps1
Export-KoaManifest.ps1
Backup-KoaMediathequeDb.ps1
Repair-KoaLibraryRows.ps1
```

---

## 3. Add row command

```powershell
.\05_TOOLS\Add-KoaLibraryRow.ps1 `
  -DbPath ".\01_DB\koa_mediatheque.sqlite" `
  -FilePath "C:\path\to\file.pdf" `
  -MetadataJson $MetadataJson `
  -StorageRoot ".\02_STORAGE" `
  -ImportBatch "manual_chatgpt_2026_06" `
  -Mode "InsertNew" `
  -CopyFile
```

---

## 4. Script behavior

The script must parse JSON, validate required fields, recalculate file facts, generate UUIDs when missing, copy file if requested, write `library_rows`, write logs, and return JSON to stdout.

Every script must return:

```json
{
  "success": true,
  "operation": "Add-KoaLibraryRow",
  "result": "inserted",
  "version_uuid": "",
  "media_uuid": "",
  "warnings": [],
  "errors": []
}
```
