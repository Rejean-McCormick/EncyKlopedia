-- schemas/sqlite/002_indexes.sql
-- Médiathèque kOA — SQLite indexes
-- Keep this file separate from table creation and triggers.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- library_rows: identity and technical lookup
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_library_rows_media_uuid
    ON library_rows(media_uuid);

CREATE INDEX IF NOT EXISTS idx_library_rows_version_uuid
    ON library_rows(version_uuid);

CREATE INDEX IF NOT EXISTS idx_library_rows_sha256
    ON library_rows(sha256);

CREATE INDEX IF NOT EXISTS idx_library_rows_import_batch
    ON library_rows(import_batch);

-- ---------------------------------------------------------------------------
-- library_rows: common GUI filters
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_library_rows_status
    ON library_rows(status);

CREATE INDEX IF NOT EXISTS idx_library_rows_visibility
    ON library_rows(visibility);

CREATE INDEX IF NOT EXISTS idx_library_rows_public_state
    ON library_rows(public_state);

CREATE INDEX IF NOT EXISTS idx_library_rows_access_level
    ON library_rows(access_level);

CREATE INDEX IF NOT EXISTS idx_library_rows_media_type
    ON library_rows(media_type);

CREATE INDEX IF NOT EXISTS idx_library_rows_language
    ON library_rows(language);

-- ---------------------------------------------------------------------------
-- library_rows: kOA / UCKK / export filters
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_library_rows_library_scope
    ON library_rows(library_scope);

CREATE INDEX IF NOT EXISTS idx_library_rows_uckk_relevance
    ON library_rows(uckk_relevance);

CREATE INDEX IF NOT EXISTS idx_library_rows_target_system
    ON library_rows(target_system);

CREATE INDEX IF NOT EXISTS idx_library_rows_target_export_allowed
    ON library_rows(target_export_allowed);

CREATE INDEX IF NOT EXISTS idx_library_rows_export_to_uckk
    ON library_rows(export_to_uckk);

CREATE INDEX IF NOT EXISTS idx_library_rows_export_to_public
    ON library_rows(export_to_public);

-- ---------------------------------------------------------------------------
-- library_rows: source, rights, restriction, review
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_library_rows_source_type
    ON library_rows(source_type);

CREATE INDEX IF NOT EXISTS idx_library_rows_source_ownership
    ON library_rows(source_ownership);

CREATE INDEX IF NOT EXISTS idx_library_rows_ownership_scope
    ON library_rows(ownership_scope);

CREATE INDEX IF NOT EXISTS idx_library_rows_rights_status
    ON library_rows(rights_status);

CREATE INDEX IF NOT EXISTS idx_library_rows_restriction_state
    ON library_rows(restriction_state);

CREATE INDEX IF NOT EXISTS idx_library_rows_review
    ON library_rows(human_review_required, review_queue);

CREATE INDEX IF NOT EXISTS idx_library_rows_canonical_validation_state
    ON library_rows(canonical_validation_state);

CREATE INDEX IF NOT EXISTS idx_library_rows_ai_validation_state
    ON library_rows(ai_validation_state);

-- ---------------------------------------------------------------------------
-- library_rows: sorting and recent activity
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_library_rows_title
    ON library_rows(title);

CREATE INDEX IF NOT EXISTS idx_library_rows_created_at
    ON library_rows(created_at);

CREATE INDEX IF NOT EXISTS idx_library_rows_updated_at
    ON library_rows(updated_at);

-- ---------------------------------------------------------------------------
-- chatgpt_intake_log
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_chatgpt_intake_log_version_uuid
    ON chatgpt_intake_log(version_uuid);

CREATE INDEX IF NOT EXISTS idx_chatgpt_intake_log_validation_status
    ON chatgpt_intake_log(validation_status);

CREATE INDEX IF NOT EXISTS idx_chatgpt_intake_log_created_at
    ON chatgpt_intake_log(created_at);

-- ---------------------------------------------------------------------------
-- xlsx_import_log
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_xlsx_import_log_import_uuid
    ON xlsx_import_log(import_uuid);

CREATE INDEX IF NOT EXISTS idx_xlsx_import_log_version_uuid
    ON xlsx_import_log(version_uuid);

CREATE INDEX IF NOT EXISTS idx_xlsx_import_log_result
    ON xlsx_import_log(result);

CREATE INDEX IF NOT EXISTS idx_xlsx_import_log_created_at
    ON xlsx_import_log(created_at);

-- ---------------------------------------------------------------------------
-- file_scan_log
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_file_scan_log_scan_uuid
    ON file_scan_log(scan_uuid);

CREATE INDEX IF NOT EXISTS idx_file_scan_log_sha256
    ON file_scan_log(sha256);

CREATE INDEX IF NOT EXISTS idx_file_scan_log_status
    ON file_scan_log(status);

CREATE INDEX IF NOT EXISTS idx_file_scan_log_created_at
    ON file_scan_log(created_at);

-- ---------------------------------------------------------------------------
-- audit_log
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_audit_log_action
    ON audit_log(action);

CREATE INDEX IF NOT EXISTS idx_audit_log_entity
    ON audit_log(entity_type, entity_uuid);

CREATE INDEX IF NOT EXISTS idx_audit_log_actor
    ON audit_log(actor);

CREATE INDEX IF NOT EXISTS idx_audit_log_created_at
    ON audit_log(created_at);

-- ---------------------------------------------------------------------------
-- schema_meta
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_schema_meta_updated_at
    ON schema_meta(updated_at);