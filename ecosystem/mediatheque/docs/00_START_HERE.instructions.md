# 00 — START HERE

**Project:** Médiathèque kOA  
**Technical name:** `koa-mediatheque`  
**Status:** AI-only final target specification  
**Audience:** AI coding conversations only  
**Rule:** All implementation conversations must start from `01_alignment_variables.md`.

---

## 1. Purpose

This documentation set defines the final target behavior for **Médiathèque kOA**, a local media/document cataloging application.

The app is intentionally simple from the user's perspective:

```text
SQLite database that behaves like an Excel sheet
PowerShell 7 writes controlled records
small GUI reads, filters, previews, exports, imports
ChatGPT produces classification JSON through a copied template
XLSX round-trip allows bulk editing
```

The app is not a full UCKK system. It is a general local media/document library. Some records may target UCKK export; others may be non-UCKK, private, non-public, personal, third-party, uncertain, or not exportable.

---

## 2. Non-negotiable architecture

```text
Médiathèque kOA = local SQLite catalog + local file storage + ChatGPT intake + XLSX round-trip + small GUI.
```

SQLite is the source of truth.

XLSX is a bulk-edit interface.

The GUI is a viewer/controller, not a separate authority.

ChatGPT produces structured metadata suggestions and local AI validation.

The app recalculates technical facts locally: hashes, sizes, paths, MIME types, timestamps.

---

## 3. Required generation order

Generate or inspect documents in this order:

```text
1. 01_alignment_variables.md
2. 02_app_definition.md
3. 03_folder_architecture.md
4. 04_sqlite_data_model.md
5. 05_library_row_schema.md
6. 06_classification_taxonomy.md
7. 07_chatgpt_intake.md
8. 08_chatgpt_template.md
9. 09_json_validation.md
10. 10_ps7_contract.md
11. 11_xlsx_roundtrip.md
12. 12_gui_spec.md
13. 13_storage_hashing_duplicates.md
14. 14_manifest_export.md
15. 15_audit_logs.md
16. 16_ai_coding_rules.md
17. 17_test_matrix.md
```

---

## 4. Required alignment rule

Every file in this documentation set must align with `01_alignment_variables.md`.

If any document conflicts with `01_alignment_variables.md`, the other document is wrong and must be updated.

---

## 5. Scope boundary

This documentation is for implementation and code generation. It is not user help, marketing copy, release notes, or a historical discussion.

The documentation must remain descriptive and final-state oriented.
