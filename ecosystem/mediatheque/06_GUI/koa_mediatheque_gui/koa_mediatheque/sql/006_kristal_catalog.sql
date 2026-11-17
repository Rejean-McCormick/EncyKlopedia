-- 006_kristal_catalog.sql
-- Médiathèque kOA — local content catalog of Kristal corpora.
-- No UCKK publication tables live in the local Médiathèque application.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS kristal_artifacts (
    kristal_uuid TEXT PRIMARY KEY,
    kristal_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    domain TEXT,
    corpus_kind TEXT NOT NULL DEFAULT 'knowledge_artifact',
    canonical_root_path TEXT,
    canonical_locator TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL DEFAULT 'working',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (kristal_id) REFERENCES kristal_registry(kristal_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_kristal_artifacts_status ON kristal_artifacts(lifecycle_status);
CREATE INDEX IF NOT EXISTS idx_kristal_artifacts_domain ON kristal_artifacts(domain);

CREATE TABLE IF NOT EXISTS kristal_versions (
    kristal_version_uuid TEXT PRIMARY KEY,
    kristal_uuid TEXT NOT NULL,
    version_label TEXT NOT NULL,
    state_id TEXT,
    release_id TEXT,
    corpus_hash_algorithm TEXT NOT NULL DEFAULT 'sha256',
    corpus_hash TEXT NOT NULL,
    manifest_path TEXT,
    status TEXT NOT NULL DEFAULT 'working',
    source_count INTEGER NOT NULL DEFAULT 0,
    corpus_file_count INTEGER NOT NULL DEFAULT 0,
    corpus_bytes INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    observed_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (kristal_uuid) REFERENCES kristal_artifacts(kristal_uuid) ON DELETE CASCADE,
    UNIQUE (kristal_uuid, corpus_hash),
    CHECK (corpus_hash_algorithm = 'sha256'),
    CHECK (length(corpus_hash) = 64),
    CHECK (source_count >= 0),
    CHECK (corpus_file_count >= 0),
    CHECK (corpus_bytes >= 0)
);
CREATE INDEX IF NOT EXISTS idx_kristal_versions_artifact ON kristal_versions(kristal_uuid);
CREATE INDEX IF NOT EXISTS idx_kristal_versions_status ON kristal_versions(status);
CREATE INDEX IF NOT EXISTS idx_kristal_versions_state_id ON kristal_versions(state_id);
CREATE INDEX IF NOT EXISTS idx_kristal_versions_release_id ON kristal_versions(release_id);
