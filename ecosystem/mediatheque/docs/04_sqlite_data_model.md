# 04 — SQLite Data Model

**Project:** Médiathèque kOA  
**Technical name:** `koa-mediatheque`  
**Status:** AI-only final target specification  
**Audience:** AI coding conversations only  
**Rule:** All implementation conversations must start from `01_alignment_variables.md`.

---

## 1. Design decision

Use one canonical table for the user's mental model.

```text
library_rows = Excel-like canonical inventory table
```

Use support tables only for logs, imports, backups, and schema metadata.

---

## 2. Required schema

```sql
CREATE TABLE schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE library_rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_uuid TEXT NOT NULL,
    version_uuid TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    subtitle TEXT,
    description TEXT,
    summary TEXT,
    original_path TEXT NOT NULL,
    storage_path TEXT,
    filename TEXT NOT NULL,
    extension TEXT,
    mimetype TEXT,
    filesize INTEGER,
    sha256 TEXT,
    filearea TEXT DEFAULT 'media_original',
    media_type TEXT DEFAULT 'document',
    language TEXT DEFAULT 'fr',
    library_scope TEXT DEFAULT 'koa',
    uckk_relevance TEXT DEFAULT 'unknown',
    target_system TEXT DEFAULT 'none',
    target_export_allowed INTEGER DEFAULT 0,
    public_state TEXT DEFAULT 'unknown',
    visibility TEXT DEFAULT 'private',
    access_level TEXT DEFAULT 'private',
    ownership_scope TEXT DEFAULT 'unknown',
    source_type TEXT DEFAULT 'unknown',
    source_ownership TEXT DEFAULT 'unknown_source',
    rights_status TEXT DEFAULT 'unknown',
    rights_note TEXT,
    restriction_state TEXT DEFAULT 'none',
    restriction_reason TEXT,
    redaction_required INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    provenance TEXT DEFAULT 'ai_assisted',
    ai_validation_state TEXT DEFAULT 'ai_uncertain',
    ai_confidence REAL,
    canonical_validation_state TEXT DEFAULT 'unverified',
    human_review_required INTEGER DEFAULT 0,
    review_queue TEXT,
    review_reason TEXT,
    collections_json TEXT DEFAULT '[]',
    tags_json TEXT DEFAULT '[]',
    relations_json TEXT DEFAULT '[]',
    content_flags_json TEXT DEFAULT '[]',
    audience_suitability TEXT DEFAULT 'unknown',
    export_to_uckk TEXT DEFAULT 'no',
    export_to_public TEXT DEFAULT 'no',
    export_policy_note TEXT,
    import_batch TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

Required indexes:

```sql
CREATE INDEX idx_library_rows_media_uuid ON library_rows(media_uuid);
CREATE INDEX idx_library_rows_version_uuid ON library_rows(version_uuid);
CREATE INDEX idx_library_rows_sha256 ON library_rows(sha256);
CREATE INDEX idx_library_rows_status ON library_rows(status);
CREATE INDEX idx_library_rows_visibility ON library_rows(visibility);
CREATE INDEX idx_library_rows_uckk_relevance ON library_rows(uckk_relevance);
CREATE INDEX idx_library_rows_public_state ON library_rows(public_state);
CREATE INDEX idx_library_rows_review ON library_rows(human_review_required, review_queue);
```

Support tables:

```sql
CREATE TABLE chatgpt_intake_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_uuid TEXT,
    file_path TEXT,
    prompt_template TEXT,
    raw_response TEXT,
    parsed_json TEXT,
    validation_status TEXT,
    validation_errors TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE xlsx_import_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_uuid TEXT NOT NULL,
    xlsx_path TEXT NOT NULL,
    mode TEXT NOT NULL,
    row_number INTEGER,
    version_uuid TEXT,
    result TEXT,
    message TEXT,
    changed_fields TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE file_scan_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_uuid TEXT NOT NULL,
    file_path TEXT NOT NULL,
    sha256 TEXT,
    filesize INTEGER,
    mimetype TEXT,
    status TEXT,
    message TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_uuid TEXT,
    before_json TEXT,
    after_json TEXT,
    note TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

The user's source of truth remains the readable `library_rows` table.
