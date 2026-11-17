-- schemas/sqlite/003_triggers.sql
-- Médiathèque kOA — SQLite triggers
-- Keep this file separate from table creation, indexes, and schema_meta seed data.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- library_rows.updated_at maintenance
-- ---------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_library_rows_updated_at
AFTER UPDATE ON library_rows
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE library_rows
    SET updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    WHERE id = OLD.id;
END;

-- ---------------------------------------------------------------------------
-- schema_meta.updated_at maintenance
-- ---------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_schema_meta_updated_at
AFTER UPDATE ON schema_meta
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE schema_meta
    SET updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    WHERE key = OLD.key;
END;