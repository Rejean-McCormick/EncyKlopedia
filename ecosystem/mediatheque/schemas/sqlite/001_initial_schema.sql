-- schemas/sqlite/001_initial_schema.sql
-- Médiathèque kOA — initial SQLite schema
-- Source of truth: library_rows
-- Support tables: schema_meta, chatgpt_intake_log, xlsx_import_log, file_scan_log, audit_log

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS library_rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identity
    media_uuid TEXT NOT NULL,
    version_uuid TEXT NOT NULL UNIQUE,

    -- Description
    title TEXT NOT NULL,
    subtitle TEXT,
    description TEXT,
    summary TEXT,

    -- File facts
    original_path TEXT NOT NULL,
    storage_path TEXT,
    filename TEXT NOT NULL,
    extension TEXT,
    mimetype TEXT,
    filesize INTEGER,
    sha256 TEXT,
    filearea TEXT NOT NULL DEFAULT 'media_original',

    -- Media and language
    media_type TEXT NOT NULL DEFAULT 'document',
    language TEXT NOT NULL DEFAULT 'fr',

    -- kOA / UCKK classification
    library_scope TEXT NOT NULL DEFAULT 'koa',
    uckk_relevance TEXT NOT NULL DEFAULT 'unknown',
    target_system TEXT NOT NULL DEFAULT 'none',
    target_export_allowed INTEGER NOT NULL DEFAULT 0,

    -- Public / non-public classification
    public_state TEXT NOT NULL DEFAULT 'unknown',
    visibility TEXT NOT NULL DEFAULT 'private',
    access_level TEXT NOT NULL DEFAULT 'private',

    -- Source and rights
    ownership_scope TEXT NOT NULL DEFAULT 'unknown',
    source_type TEXT NOT NULL DEFAULT 'unknown',
    source_ownership TEXT NOT NULL DEFAULT 'unknown_source',
    rights_status TEXT NOT NULL DEFAULT 'unknown',
    rights_note TEXT,

    -- Restriction and sensitivity
    restriction_state TEXT NOT NULL DEFAULT 'none',
    restriction_reason TEXT,
    redaction_required INTEGER NOT NULL DEFAULT 0,

    -- Lifecycle status
    status TEXT NOT NULL DEFAULT 'active',
    provenance TEXT NOT NULL DEFAULT 'ai_assisted',

    -- AI / local validation
    ai_validation_state TEXT NOT NULL DEFAULT 'ai_uncertain',
    ai_confidence REAL,
    canonical_validation_state TEXT NOT NULL DEFAULT 'unverified',
    human_review_required INTEGER NOT NULL DEFAULT 0,
    review_queue TEXT,
    review_reason TEXT,

    -- Collections / tags / relations
    collections_json TEXT NOT NULL DEFAULT '[]',
    tags_json TEXT NOT NULL DEFAULT '[]',
    relations_json TEXT NOT NULL DEFAULT '[]',
    content_flags_json TEXT NOT NULL DEFAULT '[]',
    audience_suitability TEXT NOT NULL DEFAULT 'unknown',

    -- Export policy
    export_to_uckk TEXT NOT NULL DEFAULT 'no',
    export_to_public TEXT NOT NULL DEFAULT 'no',
    export_policy_note TEXT,

    -- Import / notes
    import_batch TEXT,
    notes TEXT,

    -- Audit fields
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),

    CHECK (filesize IS NULL OR filesize >= 0),
    CHECK (ai_confidence IS NULL OR (ai_confidence >= 0.0 AND ai_confidence <= 1.0)),
    CHECK (target_export_allowed IN (0, 1)),
    CHECK (redaction_required IN (0, 1)),
    CHECK (human_review_required IN (0, 1))
);

CREATE TABLE IF NOT EXISTS chatgpt_intake_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_uuid TEXT,
    file_path TEXT,
    prompt_template TEXT,
    raw_response TEXT,
    parsed_json TEXT,
    validation_status TEXT,
    validation_errors TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS xlsx_import_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_uuid TEXT NOT NULL,
    xlsx_path TEXT NOT NULL,
    mode TEXT NOT NULL,
    row_number INTEGER,
    version_uuid TEXT,
    result TEXT,
    message TEXT,
    changed_fields TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS file_scan_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_uuid TEXT NOT NULL,
    file_path TEXT NOT NULL,
    sha256 TEXT,
    filesize INTEGER,
    mimetype TEXT,
    status TEXT,
    message TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),

    CHECK (filesize IS NULL OR filesize >= 0)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_uuid TEXT,
    before_json TEXT,
    after_json TEXT,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);