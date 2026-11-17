-- 007_source_authority.sql
-- Médiathèque kOA — consumer-neutral source authority.
--
-- Médiathèque owns source identity, immutable acquisition snapshots and
-- physical representations. Consumer systems (Kristal, EncyK, etc.) keep
-- bindings only; they do not become the persistent source-storage authority.
--
-- The schema-v3 kristal_* source tables are retained for migration and legacy
-- inspection. New application writes must target the source_* tables below.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS source_consumer_registry (
    consumer_system TEXT NOT NULL,
    consumer_instance TEXT NOT NULL,
    consumer_root TEXT,
    source_library_path TEXT,
    source_store_format TEXT,
    source_store_version TEXT,
    consumer_state_id TEXT,
    artifact_type TEXT,
    artifact_status TEXT,
    last_seen_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY (consumer_system, consumer_instance)
);

CREATE INDEX IF NOT EXISTS idx_source_consumer_registry_system
    ON source_consumer_registry(consumer_system);

CREATE TABLE IF NOT EXISTS source_registry (
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

CREATE UNIQUE INDEX IF NOT EXISTS uq_source_registry_canonical_url_key
    ON source_registry(canonical_url_key)
    WHERE canonical_url_key IS NOT NULL AND canonical_url_key <> '';
CREATE INDEX IF NOT EXISTS idx_source_registry_publisher ON source_registry(publisher);
CREATE INDEX IF NOT EXISTS idx_source_registry_status ON source_registry(status);
CREATE INDEX IF NOT EXISTS idx_source_registry_kind ON source_registry(source_kind);

CREATE TABLE IF NOT EXISTS source_bindings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consumer_system TEXT NOT NULL,
    consumer_instance TEXT NOT NULL,
    source_uuid TEXT NOT NULL,
    external_source_id TEXT NOT NULL,
    role TEXT,
    evidence_class TEXT,
    authority_class TEXT,
    category TEXT,
    priority TEXT,
    declared_in_current_consumer INTEGER NOT NULL DEFAULT 1,
    consumer_state_id TEXT,
    binding_metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (consumer_system, consumer_instance)
        REFERENCES source_consumer_registry(consumer_system, consumer_instance)
        ON DELETE CASCADE,
    FOREIGN KEY (source_uuid) REFERENCES source_registry(source_uuid) ON DELETE CASCADE,
    UNIQUE (consumer_system, consumer_instance, external_source_id),
    CHECK (declared_in_current_consumer IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_source_bindings_source_uuid ON source_bindings(source_uuid);
CREATE INDEX IF NOT EXISTS idx_source_bindings_consumer
    ON source_bindings(consumer_system, consumer_instance);
CREATE INDEX IF NOT EXISTS idx_source_bindings_role ON source_bindings(role);
CREATE INDEX IF NOT EXISTS idx_source_bindings_evidence ON source_bindings(evidence_class);
CREATE INDEX IF NOT EXISTS idx_source_bindings_authority ON source_bindings(authority_class);
CREATE INDEX IF NOT EXISTS idx_source_bindings_category ON source_bindings(category);

CREATE TABLE IF NOT EXISTS source_snapshots (
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
    FOREIGN KEY (source_uuid) REFERENCES source_registry(source_uuid) ON DELETE CASCADE,
    UNIQUE (source_uuid, snapshot_id)
);

CREATE INDEX IF NOT EXISTS idx_source_snapshots_source_uuid ON source_snapshots(source_uuid);
CREATE INDEX IF NOT EXISTS idx_source_snapshots_status ON source_snapshots(status);
CREATE INDEX IF NOT EXISTS idx_source_snapshots_retrieved_at ON source_snapshots(retrieved_at);

CREATE TABLE IF NOT EXISTS source_representations (
    representation_uuid TEXT PRIMARY KEY,
    snapshot_uuid TEXT NOT NULL,
    version_uuid TEXT NOT NULL,
    representation_kind TEXT NOT NULL,
    original_relative_path TEXT,
    declared_sha256 TEXT,
    declared_size_bytes INTEGER,
    declared_mime_type TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (snapshot_uuid) REFERENCES source_snapshots(snapshot_uuid) ON DELETE CASCADE,
    FOREIGN KEY (version_uuid) REFERENCES library_rows(version_uuid) ON DELETE RESTRICT,
    UNIQUE (snapshot_uuid, representation_kind, version_uuid),
    CHECK (declared_size_bytes IS NULL OR declared_size_bytes >= 0)
);

CREATE INDEX IF NOT EXISTS idx_source_representations_snapshot_uuid
    ON source_representations(snapshot_uuid);
CREATE INDEX IF NOT EXISTS idx_source_representations_version_uuid
    ON source_representations(version_uuid);
CREATE INDEX IF NOT EXISTS idx_source_representations_kind
    ON source_representations(representation_kind);

CREATE TABLE IF NOT EXISTS source_import_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_uuid TEXT NOT NULL,
    consumer_system TEXT,
    consumer_instance TEXT,
    external_source_id TEXT,
    snapshot_id TEXT,
    representation_kind TEXT,
    source_path TEXT,
    version_uuid TEXT,
    result TEXT NOT NULL,
    message TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_source_import_log_import_uuid ON source_import_log(import_uuid);
CREATE INDEX IF NOT EXISTS idx_source_import_log_consumer
    ON source_import_log(consumer_system, consumer_instance);

-- Non-destructive migration of the schema-v3 Kristal-specific source catalog.
INSERT OR IGNORE INTO source_consumer_registry(
    consumer_system, consumer_instance, consumer_root, source_library_path,
    source_store_format, source_store_version, consumer_state_id,
    artifact_type, artifact_status, last_seen_at, metadata_json
)
SELECT
    'kristal', kristal_id, kristal_root, source_library_path,
    source_store_format, source_store_version, state_id,
    artifact_type, artifact_status, last_seen_at, metadata_json
FROM kristal_registry kr
WHERE kr.source_library_path IS NOT NULL
   OR kr.source_store_format IS NOT NULL
   OR EXISTS (
       SELECT 1 FROM kristal_source_links l WHERE l.kristal_id = kr.kristal_id
   );

INSERT OR IGNORE INTO source_registry(
    source_uuid, canonical_url, canonical_url_key, title, publisher,
    source_kind, source_family, rights_note, status, source_metadata_json,
    created_at, updated_at
)
SELECT
    source_uuid, canonical_url, canonical_url_key, title, publisher,
    source_kind, source_family, rights_note, status, source_metadata_json,
    created_at, updated_at
FROM kristal_sources;

INSERT OR IGNORE INTO source_bindings(
    consumer_system, consumer_instance, source_uuid, external_source_id,
    role, evidence_class, authority_class, category, priority,
    declared_in_current_consumer, consumer_state_id, binding_metadata_json,
    created_at, updated_at
)
SELECT
    'kristal', kristal_id, source_uuid, source_id,
    role, evidence_class, authority_class, category, priority,
    declared_in_current_kristal, kristal_state_id, link_metadata_json,
    created_at, updated_at
FROM kristal_source_links;

INSERT OR IGNORE INTO source_snapshots(
    snapshot_uuid, source_uuid, snapshot_id, retrieved_at, status,
    requested_url, canonical_source_url, final_url, http_status,
    acquisition_method, error, metadata_json, created_at, updated_at
)
SELECT
    snapshot_uuid, source_uuid, snapshot_id, retrieved_at, status,
    requested_url, canonical_source_url, final_url, http_status,
    acquisition_method, error, metadata_json, created_at, updated_at
FROM kristal_source_snapshots;

INSERT OR IGNORE INTO source_representations(
    representation_uuid, snapshot_uuid, version_uuid, representation_kind,
    original_relative_path, declared_sha256, declared_size_bytes,
    declared_mime_type, created_at
)
SELECT
    representation_uuid, snapshot_uuid, version_uuid, representation_kind,
    original_relative_path, declared_sha256, declared_size_bytes,
    declared_mime_type, created_at
FROM kristal_source_representations;

INSERT OR IGNORE INTO source_import_log(
    import_uuid, consumer_system, consumer_instance, external_source_id,
    snapshot_id, representation_kind, source_path, version_uuid, result,
    message, created_at
)
SELECT
    import_uuid, 'kristal', kristal_id, source_id,
    snapshot_id, representation_kind, source_path, version_uuid, result,
    message, created_at
FROM kristal_source_import_log;
