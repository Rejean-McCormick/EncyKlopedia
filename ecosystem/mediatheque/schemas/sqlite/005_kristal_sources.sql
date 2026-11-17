-- 005_kristal_sources.sql
-- Médiathèque kOA — normalized Kristal local-source catalog.
-- library_rows remains the source of truth for physical local files.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS kristal_registry (
    kristal_id TEXT PRIMARY KEY,
    kristal_root TEXT,
    source_library_path TEXT,
    source_store_format TEXT,
    source_store_version TEXT,
    state_id TEXT,
    artifact_type TEXT,
    artifact_status TEXT,
    last_seen_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS kristal_sources (
    source_uuid TEXT PRIMARY KEY,
    canonical_url TEXT,
    canonical_url_key TEXT,
    title TEXT NOT NULL,
    publisher TEXT,
    source_kind TEXT NOT NULL DEFAULT 'unknown',
    source_family TEXT,
    rights_note TEXT,
    status TEXT NOT NULL DEFAULT 'declared',
    source_metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_kristal_sources_canonical_url_key
    ON kristal_sources(canonical_url_key)
    WHERE canonical_url_key IS NOT NULL AND canonical_url_key <> '';
CREATE INDEX IF NOT EXISTS idx_kristal_sources_publisher ON kristal_sources(publisher);
CREATE INDEX IF NOT EXISTS idx_kristal_sources_status ON kristal_sources(status);
CREATE INDEX IF NOT EXISTS idx_kristal_sources_kind ON kristal_sources(source_kind);

CREATE TABLE IF NOT EXISTS kristal_source_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kristal_id TEXT NOT NULL,
    source_uuid TEXT NOT NULL,
    source_id TEXT NOT NULL,
    role TEXT,
    evidence_class TEXT,
    authority_class TEXT,
    category TEXT,
    priority TEXT,
    declared_in_current_kristal INTEGER NOT NULL DEFAULT 1,
    kristal_state_id TEXT,
    link_metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (kristal_id) REFERENCES kristal_registry(kristal_id) ON DELETE CASCADE,
    FOREIGN KEY (source_uuid) REFERENCES kristal_sources(source_uuid) ON DELETE CASCADE,
    UNIQUE (kristal_id, source_id),
    CHECK (declared_in_current_kristal IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_kristal_source_links_source_uuid
    ON kristal_source_links(source_uuid);
CREATE INDEX IF NOT EXISTS idx_kristal_source_links_kristal_id
    ON kristal_source_links(kristal_id);
CREATE INDEX IF NOT EXISTS idx_kristal_source_links_role
    ON kristal_source_links(role);
CREATE INDEX IF NOT EXISTS idx_kristal_source_links_evidence
    ON kristal_source_links(evidence_class);
CREATE INDEX IF NOT EXISTS idx_kristal_source_links_authority
    ON kristal_source_links(authority_class);
CREATE INDEX IF NOT EXISTS idx_kristal_source_links_category
    ON kristal_source_links(category);

CREATE TABLE IF NOT EXISTS kristal_source_snapshots (
    snapshot_uuid TEXT PRIMARY KEY,
    source_uuid TEXT NOT NULL,
    snapshot_id TEXT NOT NULL,
    retrieved_at TEXT,
    status TEXT NOT NULL DEFAULT 'declared',
    requested_url TEXT,
    canonical_source_url TEXT,
    final_url TEXT,
    http_status INTEGER,
    acquisition_method TEXT,
    error TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (source_uuid) REFERENCES kristal_sources(source_uuid) ON DELETE CASCADE,
    UNIQUE (source_uuid, snapshot_id)
);

CREATE INDEX IF NOT EXISTS idx_kristal_source_snapshots_source_uuid
    ON kristal_source_snapshots(source_uuid);
CREATE INDEX IF NOT EXISTS idx_kristal_source_snapshots_status
    ON kristal_source_snapshots(status);
CREATE INDEX IF NOT EXISTS idx_kristal_source_snapshots_retrieved_at
    ON kristal_source_snapshots(retrieved_at);

CREATE TABLE IF NOT EXISTS kristal_source_representations (
    representation_uuid TEXT PRIMARY KEY,
    snapshot_uuid TEXT NOT NULL,
    version_uuid TEXT NOT NULL,
    representation_kind TEXT NOT NULL,
    original_relative_path TEXT,
    declared_sha256 TEXT,
    declared_size_bytes INTEGER,
    declared_mime_type TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (snapshot_uuid) REFERENCES kristal_source_snapshots(snapshot_uuid) ON DELETE CASCADE,
    FOREIGN KEY (version_uuid) REFERENCES library_rows(version_uuid) ON DELETE RESTRICT,
    UNIQUE (snapshot_uuid, representation_kind, version_uuid),
    CHECK (declared_size_bytes IS NULL OR declared_size_bytes >= 0)
);

CREATE INDEX IF NOT EXISTS idx_kristal_source_representations_snapshot_uuid
    ON kristal_source_representations(snapshot_uuid);
CREATE INDEX IF NOT EXISTS idx_kristal_source_representations_version_uuid
    ON kristal_source_representations(version_uuid);
CREATE INDEX IF NOT EXISTS idx_kristal_source_representations_kind
    ON kristal_source_representations(representation_kind);

CREATE TABLE IF NOT EXISTS kristal_source_import_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_uuid TEXT NOT NULL,
    kristal_id TEXT,
    source_id TEXT,
    snapshot_id TEXT,
    representation_kind TEXT,
    source_path TEXT,
    version_uuid TEXT,
    result TEXT NOT NULL,
    message TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_kristal_source_import_log_import_uuid
    ON kristal_source_import_log(import_uuid);
CREATE INDEX IF NOT EXISTS idx_kristal_source_import_log_kristal_id
    ON kristal_source_import_log(kristal_id);
