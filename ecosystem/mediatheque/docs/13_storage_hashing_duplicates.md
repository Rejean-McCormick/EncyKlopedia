# 13 — Storage, Hashing, and Duplicates

**Project:** Médiathèque kOA  
**Technical name:** `koa-mediatheque`  
**Status:** AI-only final target specification  
**Audience:** AI coding conversations only  
**Rule:** All implementation conversations must start from `01_alignment_variables.md`.

---

## 1. File fact authority

The app is the authority for technical file facts.

ChatGPT and XLSX are not authorities for:

```text
sha256
filesize
mimetype
filename
extension
storage_path
```

---

## 2. Hashing rule

Use SHA-256 for all local files.

```text
sha256 = lowercase hex SHA-256 content hash
```

---

## 3. Copy modes

```text
reference_only = keep original_path only
copy_to_storage = copy file to 02_STORAGE/<filearea>
copy_and_rename = copy to storage with canonical filename
```

Default:

```text
copy_to_storage
```

---

## 4. Duplicate detection

Exact duplicate:

```text
same sha256
```

Probable version:

```text
similar title
same extension family
near path
similar filename
same topic suggested by ChatGPT
```

The app may warn but must not automatically merge.
