# 16 — AI Coding Rules

**Project:** Médiathèque kOA  
**Technical name:** `koa-mediatheque`  
**Status:** AI-only final target specification  
**Audience:** AI coding conversations only  
**Rule:** All implementation conversations must start from `01_alignment_variables.md`.

---

## 1. Start rule

Every AI coding conversation must begin by reading:

```text
docs/01_alignment_variables.md
```

---

## 2. Naming rule

Use exact names:

```text
Médiathèque kOA
koa-mediatheque
koa_mediatheque
koa_mediatheque.sqlite
library_rows
chatgpt_intake_log
xlsx_import_log
```

Do not rename to UCKK Library, local library manager, media ledger, or other names.

---

## 3. Simplicity rule

Prefer:

```text
one main table
SQLite
PowerShell 7
Streamlit or compact desktop GUI
XLSX round-trip
JSON intake
```

Avoid complex web servers, remote DB dependencies, heavy permissions engines, multi-user architecture, and unnecessary normalization.

---

## 4. Safety rule

Do not let ChatGPT overwrite technical file facts.

Do not let XLSX deletion delete DB rows.

Do not mark canonical validation as verified by default.

Do not assume UCKK relevance, public status, or rights.

---

## 5. Implementation order

```text
1. Initialize SQLite schema
2. Add-KoaLibraryRow.ps1
3. ChatGPT JSON validator
4. GUI ChatGPT Intake
5. Library table view
6. XLSX export
7. XLSX import preview/apply
8. Manifest export
9. Duplicate detection
10. Repair tools
```
