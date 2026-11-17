# 06_GUI/koa_mediatheque_gui/koa_mediatheque/schema.py
# Médiathèque kOA — schema constants, timestamps, UUID helpers

from __future__ import annotations

import uuid
from datetime import datetime, timezone


SCHEMA_ID = "koa_mediatheque_schema"
SCHEMA_VERSION = 4

APP_PUBLIC_NAME = "Médiathèque kOA"
APP_SHORT_NAME = "kOA"
APP_TECHNICAL_NAME = "koa-mediatheque"
APP_COMPONENT = "koa_mediatheque"
APP_DB_FILENAME = "koa_mediatheque.sqlite"

TIMESTAMP_FORMAT_DESCRIPTION = "UTC ISO 8601 without microseconds: YYYY-MM-DDTHH:MM:SSZ"
UUID_FORMAT_DESCRIPTION = "uuid4 string"

SCHEMA_FILES = [
    "001_initial_schema.sql",
    "002_indexes.sql",
    "003_triggers.sql",
    "004_seed_schema_meta.sql",
    "005_kristal_sources.sql",
    "006_kristal_catalog.sql",
    "007_source_authority.sql",
]

MAIN_TABLE = "library_rows"

SUPPORT_TABLES = [
    "chatgpt_intake_log",
    "xlsx_import_log",
    "file_scan_log",
    "audit_log",
    "schema_meta",
    "kristal_registry",
    "kristal_sources",
    "kristal_source_links",
    "kristal_source_snapshots",
    "kristal_source_representations",
    "kristal_source_import_log",
    "kristal_artifacts",
    "kristal_versions",
    "source_consumer_registry",
    "source_registry",
    "source_bindings",
    "source_snapshots",
    "source_representations",
    "source_import_log",
]

REQUIRED_TABLES = [
    MAIN_TABLE,
    *SUPPORT_TABLES,
]

LIBRARY_ROW_COLUMNS = [
    "id",
    "media_uuid",
    "version_uuid",
    "title",
    "subtitle",
    "description",
    "summary",
    "original_path",
    "storage_path",
    "filename",
    "extension",
    "mimetype",
    "filesize",
    "sha256",
    "filearea",
    "media_type",
    "language",
    "library_scope",
    "uckk_relevance",
    "target_system",
    "target_export_allowed",
    "public_state",
    "visibility",
    "access_level",
    "ownership_scope",
    "source_type",
    "source_ownership",
    "rights_status",
    "rights_note",
    "restriction_state",
    "restriction_reason",
    "redaction_required",
    "status",
    "provenance",
    "ai_validation_state",
    "ai_confidence",
    "canonical_validation_state",
    "human_review_required",
    "review_queue",
    "review_reason",
    "collections_json",
    "tags_json",
    "relations_json",
    "content_flags_json",
    "audience_suitability",
    "export_to_uckk",
    "export_to_public",
    "export_policy_note",
    "import_batch",
    "notes",
    "created_at",
    "updated_at",
]

SCHEMA_META_KEYS = [
    "app_public_name",
    "app_short_name",
    "app_technical_name",
    "app_component",
    "app_db_filename",
    "app_doc_mode",
    "app_doc_audience",
    "app_primary_language",
    "app_storage_model",
    "app_db_model",
    "schema_id",
    "schema_version",
    "schema_created_by",
    "schema_source_of_truth",
    "koa_root",
    "koa_db_dir",
    "koa_db_path",
    "koa_storage_dir",
    "koa_imports_dir",
    "koa_exports_dir",
    "koa_tools_dir",
    "koa_gui_dir",
    "koa_docs_dir",
    "main_table",
    "support_tables",
    "timestamp_format",
    "uuid_format",
    "manifest_filename",
]

LOG_TABLE_COLUMNS = {
    "schema_meta": [
        "key",
        "value",
        "updated_at",
    ],
    "chatgpt_intake_log": [
        "id",
        "version_uuid",
        "file_path",
        "prompt_template",
        "raw_response",
        "parsed_json",
        "validation_status",
        "validation_errors",
        "created_at",
    ],
    "xlsx_import_log": [
        "id",
        "import_uuid",
        "xlsx_path",
        "mode",
        "row_number",
        "version_uuid",
        "result",
        "message",
        "changed_fields",
        "created_at",
    ],
    "file_scan_log": [
        "id",
        "scan_uuid",
        "file_path",
        "sha256",
        "filesize",
        "mimetype",
        "status",
        "message",
        "created_at",
    ],
    "audit_log": [
        "id",
        "actor",
        "action",
        "entity_type",
        "entity_uuid",
        "before_json",
        "after_json",
        "note",
        "created_at",
    ],
}


def utc_now_iso() -> str:
    """
    Return the canonical Médiathèque kOA timestamp format.

    Format:
    UTC ISO 8601 without microseconds: YYYY-MM-DDTHH:MM:SSZ
    """
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def generate_uuid() -> str:
    """
    Return a UUID4 string for media_uuid, version_uuid, import_uuid, scan_uuid,
    export_uuid, or other local portable identities.
    """
    return str(uuid.uuid4())


def get_initial_schema_meta() -> dict[str, str]:
    """
    Return the canonical initial schema_meta values.

    The SQL seed file remains authoritative for database initialization.
    This helper gives Python code and tests the same values without parsing SQL.
    """
    return {
        "app_public_name": APP_PUBLIC_NAME,
        "app_short_name": APP_SHORT_NAME,
        "app_technical_name": APP_TECHNICAL_NAME,
        "app_component": APP_COMPONENT,
        "app_db_filename": APP_DB_FILENAME,
        "app_doc_mode": "final_state_specification",
        "app_doc_audience": "ai_only",
        "app_primary_language": "fr",
        "app_storage_model": "local_filesystem",
        "app_db_model": "sqlite_single_sheet_with_support_logs",
        "schema_id": SCHEMA_ID,
        "schema_version": str(SCHEMA_VERSION),
        "schema_created_by": "Médiathèque kOA initial schema",
        "schema_source_of_truth": MAIN_TABLE,
        "koa_root": "KOA_MEDIATHEQUE",
        "koa_db_dir": "01_DB",
        "koa_db_path": "01_DB/koa_mediatheque.sqlite",
        "koa_storage_dir": "02_STORAGE",
        "koa_imports_dir": "03_IMPORTS",
        "koa_exports_dir": "04_EXPORTS",
        "koa_tools_dir": "05_TOOLS",
        "koa_gui_dir": "06_GUI",
        "koa_docs_dir": "docs",
        "main_table": MAIN_TABLE,
        "support_tables": ",".join(SUPPORT_TABLES),
        "timestamp_format": TIMESTAMP_FORMAT_DESCRIPTION,
        "uuid_format": UUID_FORMAT_DESCRIPTION,
        "manifest_filename": "manifest.json",
    }


def get_required_table_columns() -> dict[str, list[str]]:
    """
    Return required table-column expectations for lightweight schema checks.
    """
    return {
        MAIN_TABLE: LIBRARY_ROW_COLUMNS,
        **LOG_TABLE_COLUMNS,
    }