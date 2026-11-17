-- schemas/sqlite/004_seed_schema_meta.sql
-- Médiathèque kOA — initial schema metadata seed
-- Keep this file separate from table creation, indexes, and triggers.

PRAGMA foreign_keys = ON;

INSERT INTO schema_meta (key, value, updated_at)
VALUES
    ('app_public_name', 'Médiathèque kOA', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('app_short_name', 'kOA', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('app_technical_name', 'koa-mediatheque', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('app_component', 'koa_mediatheque', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('app_db_filename', 'koa_mediatheque.sqlite', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('app_doc_mode', 'final_state_specification', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('app_doc_audience', 'ai_only', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('app_primary_language', 'fr', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('app_storage_model', 'local_filesystem', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('app_db_model', 'sqlite_single_sheet_with_support_logs', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),

    ('schema_id', 'koa_mediatheque_schema', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('schema_version', '1', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('schema_created_by', 'Médiathèque kOA initial schema', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('schema_source_of_truth', 'library_rows', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),

    ('koa_root', 'KOA_MEDIATHEQUE', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('koa_db_dir', '01_DB', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('koa_db_path', '01_DB/koa_mediatheque.sqlite', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('koa_storage_dir', '02_STORAGE', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('koa_imports_dir', '03_IMPORTS', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('koa_exports_dir', '04_EXPORTS', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('koa_tools_dir', '05_TOOLS', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('koa_gui_dir', '06_GUI', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('koa_docs_dir', 'docs', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),

    ('main_table', 'library_rows', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('support_tables', 'chatgpt_intake_log,xlsx_import_log,file_scan_log,audit_log,schema_meta,kristal_registry,kristal_sources,kristal_source_links,kristal_source_snapshots,kristal_source_representations,kristal_source_import_log,kristal_artifacts,kristal_versions,source_consumer_registry,source_registry,source_bindings,source_snapshots,source_representations,source_import_log', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),

    ('timestamp_format', 'UTC ISO 8601 without microseconds: YYYY-MM-DDTHH:MM:SSZ', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('uuid_format', 'uuid4 string', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('manifest_filename', 'manifest.json', strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
ON CONFLICT(key) DO UPDATE SET
    value = excluded.value,
    updated_at = excluded.updated_at;