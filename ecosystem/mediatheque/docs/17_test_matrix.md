# 17 — Test Matrix

**Project:** Médiathèque kOA  
**Technical name:** `koa-mediatheque`  
**Status:** AI-only final target specification  
**Audience:** AI coding conversations only  
**Rule:** All implementation conversations must start from `01_alignment_variables.md`.

---

## 1. Database tests

```text
DB initializes successfully
schema_meta populated
library_rows insert works
version_uuid uniqueness enforced
indexes exist
updated_at updates on row update
```

---

## 2. ChatGPT intake tests

```text
valid JSON imports
invalid JSON blocked
missing required field blocked
invalid enum blocked
canonical_validation_state verified blocked without override
unknown rights forces review
not_uckk forces export_to_uckk no unless override
non-public blocks export_to_public yes
raw ChatGPT response logged
```

---

## 3. File tests

```text
file path exists check
sha256 calculated
filesize calculated
mimetype guessed
copy_to_storage works
reference_only works
missing file blocked unless external_reference
exact duplicate detected by sha256
```

---

## 4. XLSX tests

```text
export creates Library sheet
export creates Lists sheet
export creates Import_Report sheet
semicolon fields round-trip to JSON arrays
protected field changes rejected
version_uuid matching updates row
deleted XLSX row does not delete DB row
Apply creates DB backup
import log created
```

---

## 5. GUI and manifest tests

```text
library table loads
filters work
open file works
open folder works
copy template works
paste JSON validation works
preview row works
validate and integrate inserts row
export filtered XLSX works
import preview displays changes
manifest includes UUIDs and hashes
public export blocks non-public rows
UCKK export blocks not_uckk rows
```
