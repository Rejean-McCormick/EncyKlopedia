"""
Canonical constants for Médiathèque kOA.

This module is the shared source for identity variables, paths, table names,
column names, controlled values, XLSX structure, JSON field contracts, session
keys, and export constants.

Other modules must import these constants instead of duplicating lists locally.
"""

from __future__ import annotations

from typing import Final


# ---------------------------------------------------------------------------
# Application identity
# ---------------------------------------------------------------------------

APP_PUBLIC_NAME: Final[str] = "Médiathèque kOA"
APP_SHORT_NAME: Final[str] = "kOA"
APP_TECHNICAL_NAME: Final[str] = "koa-mediatheque"
APP_COMPONENT: Final[str] = "koa_mediatheque"
APP_DB_FILENAME: Final[str] = "koa_mediatheque.sqlite"
APP_DOC_MODE: Final[str] = "final_state_specification"
APP_DOC_AUDIENCE: Final[str] = "ai_only"
APP_PRIMARY_LANGUAGE: Final[str] = "fr"
APP_STORAGE_MODEL: Final[str] = "local_filesystem"
APP_DB_MODEL: Final[str] = "sqlite_single_sheet_with_support_logs"


# ---------------------------------------------------------------------------
# Canonical root and directory names
# ---------------------------------------------------------------------------

KOA_ROOT: Final[str] = "KOA_MEDIATHEQUE"
KOA_DB_DIR: Final[str] = "01_DB"
KOA_DB_PATH: Final[str] = "01_DB/koa_mediatheque.sqlite"
KOA_STORAGE_DIR: Final[str] = "02_STORAGE"
KOA_IMPORTS_DIR: Final[str] = "03_IMPORTS"
KOA_EXPORTS_DIR: Final[str] = "04_EXPORTS"
KOA_TOOLS_DIR: Final[str] = "05_TOOLS"
KOA_GUI_DIR: Final[str] = "06_GUI"
KOA_BACKUPS_DIR: Final[str] = "07_BACKUPS"
KOA_LOGS_DIR: Final[str] = "08_LOGS"
KOA_DOCS_DIR: Final[str] = "docs"

SCHEMA_VERSIONS_DIR: Final[str] = "schema_versions"


# ---------------------------------------------------------------------------
# Canonical local storage areas
# ---------------------------------------------------------------------------

MEDIA_ORIGINAL_FILEAREA: Final[str] = "media_original"
MEDIA_PREVIEW_FILEAREA: Final[str] = "media_preview"
MEDIA_THUMBNAIL_FILEAREA: Final[str] = "media_thumbnail"
MEDIA_DERIVATIVE_FILEAREA: Final[str] = "media_derivative"
MEDIA_CAPTION_FILEAREA: Final[str] = "media_caption"
MEDIA_TRANSCRIPT_FILEAREA: Final[str] = "media_transcript"
MEDIA_ATTACHMENT_FILEAREA: Final[str] = "media_attachment"
CONTENT_REVIEW_FILES_FILEAREA: Final[str] = "content_review_files"
EXTERNAL_WORK_REFERENCE_FILES_FILEAREA: Final[str] = "external_work_reference_files"
CULTURAL_PROTOCOL_FILES_FILEAREA: Final[str] = "cultural_protocol_files"
SOURCE_FILES_FILEAREA: Final[str] = "source_files"
# Legacy schema-v3 filearea; existing rows remain valid but new source imports use source_files.
KRISTAL_SOURCE_FILES_FILEAREA: Final[str] = "kristal_source_files"

STORAGE_FILEAREAS: Final[tuple[str, ...]] = (
    MEDIA_ORIGINAL_FILEAREA,
    MEDIA_PREVIEW_FILEAREA,
    MEDIA_THUMBNAIL_FILEAREA,
    MEDIA_DERIVATIVE_FILEAREA,
    MEDIA_CAPTION_FILEAREA,
    MEDIA_TRANSCRIPT_FILEAREA,
    MEDIA_ATTACHMENT_FILEAREA,
    CONTENT_REVIEW_FILES_FILEAREA,
    EXTERNAL_WORK_REFERENCE_FILES_FILEAREA,
    CULTURAL_PROTOCOL_FILES_FILEAREA,
    SOURCE_FILES_FILEAREA,
    KRISTAL_SOURCE_FILES_FILEAREA,
)

DEFAULT_FILEAREA: Final[str] = MEDIA_ORIGINAL_FILEAREA


# ---------------------------------------------------------------------------
# Import/export subdirectories
# ---------------------------------------------------------------------------

IMPORT_GOOGLE_DRIVE_RAW_DIR: Final[str] = "google_drive_raw"
IMPORT_GOOGLE_DRIVE_SCANNED_DIR: Final[str] = "google_drive_scanned"
IMPORT_AI_GENERATED_DOCS_DIR: Final[str] = "ai_generated_docs"
IMPORT_PENDING_REVIEW_DIR: Final[str] = "pending_review"

IMPORT_SUBDIRS: Final[tuple[str, ...]] = (
    IMPORT_GOOGLE_DRIVE_RAW_DIR,
    IMPORT_GOOGLE_DRIVE_SCANNED_DIR,
    IMPORT_AI_GENERATED_DOCS_DIR,
    IMPORT_PENDING_REVIEW_DIR,
)

EXPORT_XLSX_DIR: Final[str] = "xlsx"
EXPORT_MANIFESTS_DIR: Final[str] = "manifests"
EXPORT_UCKKARCHIVE_DIR: Final[str] = "uckkarchive"
EXPORT_PUBLIC_REVIEW_DIR: Final[str] = "public_review"

EXPORT_SUBDIRS: Final[tuple[str, ...]] = (
    EXPORT_XLSX_DIR,
    EXPORT_MANIFESTS_DIR,
    EXPORT_UCKKARCHIVE_DIR,
    EXPORT_PUBLIC_REVIEW_DIR,
)


# ---------------------------------------------------------------------------
# Database tables
# ---------------------------------------------------------------------------

TABLE_LIBRARY_ROWS: Final[str] = "library_rows"
TABLE_CHATGPT_INTAKE_LOG: Final[str] = "chatgpt_intake_log"
TABLE_XLSX_IMPORT_LOG: Final[str] = "xlsx_import_log"
TABLE_FILE_SCAN_LOG: Final[str] = "file_scan_log"
TABLE_AUDIT_LOG: Final[str] = "audit_log"
TABLE_SCHEMA_META: Final[str] = "schema_meta"
TABLE_KRISTAL_REGISTRY: Final[str] = "kristal_registry"
TABLE_KRISTAL_SOURCES: Final[str] = "kristal_sources"
TABLE_KRISTAL_SOURCE_LINKS: Final[str] = "kristal_source_links"
TABLE_KRISTAL_SOURCE_SNAPSHOTS: Final[str] = "kristal_source_snapshots"
TABLE_KRISTAL_SOURCE_REPRESENTATIONS: Final[str] = "kristal_source_representations"
TABLE_KRISTAL_SOURCE_IMPORT_LOG: Final[str] = "kristal_source_import_log"
TABLE_SOURCE_CONSUMER_REGISTRY: Final[str] = "source_consumer_registry"
TABLE_SOURCE_REGISTRY: Final[str] = "source_registry"
TABLE_SOURCE_BINDINGS: Final[str] = "source_bindings"
TABLE_SOURCE_SNAPSHOTS: Final[str] = "source_snapshots"
TABLE_SOURCE_REPRESENTATIONS: Final[str] = "source_representations"
TABLE_SOURCE_IMPORT_LOG: Final[str] = "source_import_log"

CORE_TABLES: Final[tuple[str, ...]] = (
    TABLE_LIBRARY_ROWS,
    TABLE_CHATGPT_INTAKE_LOG,
    TABLE_XLSX_IMPORT_LOG,
    TABLE_FILE_SCAN_LOG,
    TABLE_AUDIT_LOG,
    TABLE_SCHEMA_META,
    TABLE_KRISTAL_REGISTRY,
    TABLE_KRISTAL_SOURCES,
    TABLE_KRISTAL_SOURCE_LINKS,
    TABLE_KRISTAL_SOURCE_SNAPSHOTS,
    TABLE_KRISTAL_SOURCE_REPRESENTATIONS,
    TABLE_KRISTAL_SOURCE_IMPORT_LOG,
    TABLE_SOURCE_CONSUMER_REGISTRY,
    TABLE_SOURCE_REGISTRY,
    TABLE_SOURCE_BINDINGS,
    TABLE_SOURCE_SNAPSHOTS,
    TABLE_SOURCE_REPRESENTATIONS,
    TABLE_SOURCE_IMPORT_LOG,
)

OPTIONAL_FUTURE_TABLES: Final[tuple[str, ...]] = (
    "normalized_media",
    "normalized_media_version",
    "normalized_collections",
    "normalized_tags",
    "normalized_relations",
    "normalized_sources",
)


# ---------------------------------------------------------------------------
# library_rows columns
# ---------------------------------------------------------------------------

LIBRARY_ROW_COLUMNS: Final[tuple[str, ...]] = (
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
)

LIBRARY_ROW_INSERT_COLUMNS: Final[tuple[str, ...]] = tuple(
    column for column in LIBRARY_ROW_COLUMNS if column != "id"
)

IDENTITY_COLUMNS: Final[tuple[str, ...]] = (
    "id",
    "media_uuid",
    "version_uuid",
)

FILE_FACT_COLUMNS: Final[tuple[str, ...]] = (
    "original_path",
    "storage_path",
    "filename",
    "extension",
    "mimetype",
    "filesize",
    "sha256",
    "filearea",
)

DESCRIPTION_COLUMNS: Final[tuple[str, ...]] = (
    "title",
    "subtitle",
    "description",
    "summary",
    "language",
    "media_type",
)

CLASSIFICATION_COLUMNS: Final[tuple[str, ...]] = (
    "library_scope",
    "uckk_relevance",
    "target_system",
    "target_export_allowed",
)

PUBLIC_ACCESS_COLUMNS: Final[tuple[str, ...]] = (
    "public_state",
    "visibility",
    "access_level",
)

SOURCE_RIGHTS_COLUMNS: Final[tuple[str, ...]] = (
    "ownership_scope",
    "source_type",
    "source_ownership",
    "rights_status",
    "rights_note",
)

RESTRICTION_COLUMNS: Final[tuple[str, ...]] = (
    "restriction_state",
    "restriction_reason",
    "redaction_required",
    "audience_suitability",
    "content_flags_json",
)

LIFECYCLE_COLUMNS: Final[tuple[str, ...]] = (
    "status",
)

VALIDATION_COLUMNS: Final[tuple[str, ...]] = (
    "provenance",
    "ai_validation_state",
    "ai_confidence",
    "canonical_validation_state",
    "human_review_required",
    "review_queue",
    "review_reason",
)

COLLECTION_TAG_RELATION_COLUMNS: Final[tuple[str, ...]] = (
    "collections_json",
    "tags_json",
    "relations_json",
)

EXPORT_POLICY_COLUMNS: Final[tuple[str, ...]] = (
    "export_to_uckk",
    "export_to_public",
    "export_policy_note",
)

AUDIT_COLUMNS: Final[tuple[str, ...]] = (
    "import_batch",
    "notes",
    "created_at",
    "updated_at",
)


# ---------------------------------------------------------------------------
# Support table columns
# ---------------------------------------------------------------------------

SCHEMA_META_COLUMNS: Final[tuple[str, ...]] = (
    "key",
    "value",
    "updated_at",
)

CHATGPT_INTAKE_LOG_COLUMNS: Final[tuple[str, ...]] = (
    "id",
    "version_uuid",
    "file_path",
    "prompt_template",
    "raw_response",
    "parsed_json",
    "validation_status",
    "validation_errors",
    "created_at",
)

XLSX_IMPORT_LOG_COLUMNS: Final[tuple[str, ...]] = (
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
)

FILE_SCAN_LOG_COLUMNS: Final[tuple[str, ...]] = (
    "id",
    "scan_uuid",
    "file_path",
    "sha256",
    "filesize",
    "mimetype",
    "status",
    "message",
    "created_at",
)

AUDIT_LOG_COLUMNS: Final[tuple[str, ...]] = (
    "id",
    "actor",
    "action",
    "entity_type",
    "entity_uuid",
    "before_json",
    "after_json",
    "note",
    "created_at",
)


# ---------------------------------------------------------------------------
# Required insertion and protected fields
# ---------------------------------------------------------------------------

REQUIRED_INSERTION_FIELDS: Final[tuple[str, ...]] = (
    "media_uuid",
    "version_uuid",
    "title",
    "original_path",
    "filename",
    "media_type",
    "library_scope",
    "public_state",
    "visibility",
    "source_type",
    "source_ownership",
    "rights_status",
    "status",
    "provenance",
    "ai_validation_state",
    "canonical_validation_state",
)

TECHNICAL_PROTECTED_FIELDS: Final[tuple[str, ...]] = (
    "filename",
    "extension",
    "mimetype",
    "filesize",
    "sha256",
    "storage_path",
    "created_at",
    "updated_at",
)

APP_ENRICHED_FIELDS: Final[tuple[str, ...]] = (
    "media_uuid",
    "version_uuid",
    "original_path",
    "storage_path",
    "filename",
    "extension",
    "mimetype",
    "filesize",
    "sha256",
    "filearea",
    "created_at",
    "updated_at",
    "import_batch",
)

EDITABLE_LIBRARY_ROW_FIELDS: Final[tuple[str, ...]] = (
    "title",
    "subtitle",
    "description",
    "summary",
    "media_type",
    "language",
    "collections_json",
    "tags_json",
    "relations_json",
    "content_flags_json",
    "notes",
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
    "human_review_required",
    "review_queue",
    "review_reason",
    "audience_suitability",
    "export_to_uckk",
    "export_to_public",
    "export_policy_note",
)


# ---------------------------------------------------------------------------
# Controlled values
# ---------------------------------------------------------------------------

MEDIA_STATUS_VALUES: Final[tuple[str, ...]] = (
    "draft",
    "submitted",
    "active",
    "restricted",
    "superseded",
    "archived",
    "deleted_soft",
)

CANONICAL_VALIDATION_VALUES: Final[tuple[str, ...]] = (
    "unverified",
    "human_reviewed",
    "verified",
    "contested",
    "invalidated",
    "archived",
)

LOCAL_AI_VALIDATION_VALUES: Final[tuple[str, ...]] = (
    "ai_validated",
    "ai_classified_needs_review",
    "ai_uncertain",
    "ai_rejected",
)

VISIBILITY_VALUES: Final[tuple[str, ...]] = (
    "private",
    "user",
    "group",
    "course",
    "cohort",
    "program",
    "institution",
    "public",
    "restricted",
    "restricted_integrity",
    "restricted_cultural",
)

PUBLIC_STATE_VALUES: Final[tuple[str, ...]] = (
    "public",
    "non_public",
    "private",
    "restricted",
    "confidential",
    "unknown",
)

ACCESS_LEVEL_VALUES: Final[tuple[str, ...]] = (
    "private",
    "limited",
    "internal",
    "public",
    "restricted",
    "confidential",
    "unknown",
)

LIBRARY_SCOPE_VALUES: Final[tuple[str, ...]] = (
    "koa",
)

UCKK_RELEVANCE_VALUES: Final[tuple[str, ...]] = (
    "uckk_core",
    "uckk_related",
    "uckk_reference",
    "not_uckk",
    "unknown",
)

TARGET_SYSTEM_VALUES: Final[tuple[str, ...]] = (
    "none",
    "uckkarchive",
    "other",
)

TARGET_EXPORT_ALLOWED_VALUES: Final[tuple[int, ...]] = (
    0,
    1,
)

EXPORT_DECISION_VALUES: Final[tuple[str, ...]] = (
    "yes",
    "no",
    "maybe",
    "review_required",
)

MEDIA_TYPE_VALUES: Final[tuple[str, ...]] = (
    "document",
    "pdf",
    "image",
    "audio",
    "video",
    "transcript",
    "spreadsheet",
    "presentation",
    "source_package",
    "external_reference",
    "other",
)

SOURCE_TYPE_VALUES: Final[tuple[str, ...]] = (
    "produced_by_uckk",
    "submitted_to_uckk",
    "imported",
    "external_reference_only",
    "licensed_external",
    "public_domain",
    "fair_use_reference",
    "restricted_reference",
    "unknown",
)

SOURCE_OWNERSHIP_VALUES: Final[tuple[str, ...]] = (
    "uckk_created",
    "uckk_commissioned",
    "member_submitted",
    "partner_submitted",
    "external_reference",
    "third_party_copyright",
    "public_domain",
    "open_license",
    "unknown_source",
)

OWNERSHIP_SCOPE_VALUES: Final[tuple[str, ...]] = (
    "uckk_owned",
    "koa_owned",
    "personal",
    "third_party",
    "public_domain",
    "open_license",
    "unknown",
)

RIGHTS_STATUS_VALUES: Final[tuple[str, ...]] = (
    "owned",
    "licensed",
    "open_license",
    "public_domain",
    "fair_use_reference",
    "third_party",
    "unknown",
)

RESTRICTION_STATE_VALUES: Final[tuple[str, ...]] = (
    "none",
    "possible",
    "restricted",
    "confidential",
    "cultural",
    "integrity",
    "privacy",
    "copyright",
    "unknown",
)

AUDIENCE_SUITABILITY_VALUES: Final[tuple[str, ...]] = (
    "general",
    "guided",
    "mature",
    "restricted",
    "restricted_cultural",
    "restricted_integrity",
    "staff_only",
    "unknown",
)

CONTENT_FLAG_VALUES: Final[tuple[str, ...]] = (
    "sexual_violence",
    "violence",
    "racism",
    "colonial_violence",
    "death",
    "self_harm",
    "substance_use",
    "nudity",
    "explicit_language",
    "culturally_sensitive",
    "sacred_content",
    "ceremonial_content",
    "restricted_knowledge",
    "grief_or_mourning",
    "requires_context",
    "not_for_children",
    "privacy_sensitive",
    "copyright_uncertain",
    "non_public",
    "confidential",
)

RELATION_TYPE_VALUES: Final[tuple[str, ...]] = (
    "belongs_to_collection",
    "is_derivative_of",
    "is_translation_of",
    "is_excerpt_of",
    "is_source_for",
    "replaces",
    "references",
    "duplicates",
    "references_external_work",
    "contains_content_marker",
    "related_to",
)

PROVENANCE_VALUES: Final[tuple[str, ...]] = (
    "human",
    "ai_assisted",
    "imported",
    "system",
    "archive",
    "assembly",
    "challenge",
    "integrity",
    "media",
    "external_work",
    "content_review",
)

LANGUAGE_VALUES: Final[tuple[str, ...]] = (
    "fr",
    "en",
    "und",
    "unknown",
)


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_MEDIA_TYPE: Final[str] = "document"
DEFAULT_LANGUAGE: Final[str] = "fr"
DEFAULT_LIBRARY_SCOPE: Final[str] = "koa"
DEFAULT_UCKK_RELEVANCE: Final[str] = "unknown"
DEFAULT_TARGET_SYSTEM: Final[str] = "none"
DEFAULT_TARGET_EXPORT_ALLOWED: Final[int] = 0
DEFAULT_PUBLIC_STATE: Final[str] = "unknown"
DEFAULT_VISIBILITY: Final[str] = "private"
DEFAULT_ACCESS_LEVEL: Final[str] = "private"
DEFAULT_OWNERSHIP_SCOPE: Final[str] = "unknown"
DEFAULT_SOURCE_TYPE: Final[str] = "unknown"
DEFAULT_SOURCE_OWNERSHIP: Final[str] = "unknown_source"
DEFAULT_RIGHTS_STATUS: Final[str] = "unknown"
DEFAULT_RESTRICTION_STATE: Final[str] = "none"
DEFAULT_REDACTION_REQUIRED: Final[int] = 0
DEFAULT_STATUS: Final[str] = "active"
DEFAULT_PROVENANCE: Final[str] = "ai_assisted"
DEFAULT_AI_VALIDATION_STATE: Final[str] = "ai_uncertain"
DEFAULT_CANONICAL_VALIDATION_STATE: Final[str] = "unverified"
DEFAULT_HUMAN_REVIEW_REQUIRED: Final[int] = 0
DEFAULT_AUDIENCE_SUITABILITY: Final[str] = "unknown"
DEFAULT_EXPORT_TO_UCKK: Final[str] = "no"
DEFAULT_EXPORT_TO_PUBLIC: Final[str] = "no"
DEFAULT_JSON_ARRAY_TEXT: Final[str] = "[]"


# ---------------------------------------------------------------------------
# JSON contract
# ---------------------------------------------------------------------------

CHATGPT_JSON_REQUIRED_FIELDS: Final[tuple[str, ...]] = (
    "title",
    "description",
    "summary",
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
    "restriction_state",
    "redaction_required",
    "status",
    "provenance",
    "ai_validation_state",
    "ai_confidence",
    "canonical_validation_state",
    "human_review_required",
    "review_queue",
    "collections",
    "tags",
    "relations",
    "content_flags",
    "audience_suitability",
    "export_to_uckk",
    "export_to_public",
    "notes",
)

CHATGPT_JSON_OPTIONAL_FIELDS: Final[tuple[str, ...]] = (
    "subtitle",
    "rights_note",
    "restriction_reason",
    "review_reason",
    "export_policy_note",
)

JSON_STRING_FIELDS: Final[tuple[str, ...]] = (
    "title",
    "subtitle",
    "description",
    "summary",
    "media_type",
    "language",
    "library_scope",
    "uckk_relevance",
    "target_system",
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
    "status",
    "provenance",
    "ai_validation_state",
    "canonical_validation_state",
    "review_queue",
    "review_reason",
    "audience_suitability",
    "export_to_uckk",
    "export_to_public",
    "export_policy_note",
    "notes",
)

JSON_BOOLEAN_FIELDS: Final[tuple[str, ...]] = (
    "target_export_allowed",
    "redaction_required",
    "human_review_required",
)

JSON_NUMBER_FIELDS: Final[tuple[str, ...]] = (
    "ai_confidence",
)

JSON_ARRAY_FIELDS: Final[tuple[str, ...]] = (
    "collections",
    "tags",
    "relations",
    "content_flags",
)

SQLITE_JSON_TEXT_FIELDS: Final[tuple[str, ...]] = (
    "collections_json",
    "tags_json",
    "relations_json",
    "content_flags_json",
)

JSON_TO_SQLITE_JSON_TEXT_FIELD_MAP: Final[dict[str, str]] = {
    "collections": "collections_json",
    "tags": "tags_json",
    "relations": "relations_json",
    "content_flags": "content_flags_json",
}

SQLITE_JSON_TEXT_TO_JSON_FIELD_MAP: Final[dict[str, str]] = {
    value: key for key, value in JSON_TO_SQLITE_JSON_TEXT_FIELD_MAP.items()
}

ENUM_FIELD_VALUES: Final[dict[str, tuple[str, ...]]] = {
    "media_type": MEDIA_TYPE_VALUES,
    "language": LANGUAGE_VALUES,
    "library_scope": LIBRARY_SCOPE_VALUES,
    "uckk_relevance": UCKK_RELEVANCE_VALUES,
    "target_system": TARGET_SYSTEM_VALUES,
    "public_state": PUBLIC_STATE_VALUES,
    "visibility": VISIBILITY_VALUES,
    "access_level": ACCESS_LEVEL_VALUES,
    "ownership_scope": OWNERSHIP_SCOPE_VALUES,
    "source_type": SOURCE_TYPE_VALUES,
    "source_ownership": SOURCE_OWNERSHIP_VALUES,
    "rights_status": RIGHTS_STATUS_VALUES,
    "restriction_state": RESTRICTION_STATE_VALUES,
    "status": MEDIA_STATUS_VALUES,
    "provenance": PROVENANCE_VALUES,
    "ai_validation_state": LOCAL_AI_VALIDATION_VALUES,
    "canonical_validation_state": CANONICAL_VALIDATION_VALUES,
    "audience_suitability": AUDIENCE_SUITABILITY_VALUES,
    "export_to_uckk": EXPORT_DECISION_VALUES,
    "export_to_public": EXPORT_DECISION_VALUES,
}


# ---------------------------------------------------------------------------
# XLSX contract
# ---------------------------------------------------------------------------

XLSX_SHEET_LIBRARY: Final[str] = "Library"
XLSX_SHEET_LISTS: Final[str] = "Lists"
XLSX_SHEET_IMPORT_REPORT: Final[str] = "Import_Report"
XLSX_SHEET_README: Final[str] = "Readme"
XLSX_SHEET_CHANGE_PREVIEW: Final[str] = "Change_Preview"

XLSX_REQUIRED_SHEETS: Final[tuple[str, ...]] = (
    XLSX_SHEET_LIBRARY,
    XLSX_SHEET_LISTS,
    XLSX_SHEET_IMPORT_REPORT,
)

XLSX_OPTIONAL_SHEETS: Final[tuple[str, ...]] = (
    XLSX_SHEET_README,
    XLSX_SHEET_CHANGE_PREVIEW,
)

XLSX_LIBRARY_COLUMNS: Final[tuple[str, ...]] = (
    "action",
    "media_uuid",
    "version_uuid",
    "title",
    "subtitle",
    "description",
    "summary",
    "filename",
    "original_path",
    "storage_path",
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
    "collections",
    "tags",
    "relations",
    "content_flags",
    "audience_suitability",
    "export_to_uckk",
    "export_to_public",
    "export_policy_note",
    "notes",
    "sha256",
    "filesize",
    "mimetype",
    "updated_at",
)

XLSX_PROTECTED_COLUMNS: Final[tuple[str, ...]] = (
    "media_uuid",
    "version_uuid",
    "filename",
    "original_path",
    "storage_path",
    "sha256",
    "filesize",
    "mimetype",
    "updated_at",
)

XLSX_ACTION_COLUMN: Final[str] = "action"

XLSX_ACTION_VALUES: Final[tuple[str, ...]] = (
    "update",
    "ignore",
    "archive",
    "new",
)

XLSX_IMPORT_MODES: Final[tuple[str, ...]] = (
    "normal",
    "repair",
    "dry_run",
)

XLSX_DEFAULT_ACTION: Final[str] = "update"


# ---------------------------------------------------------------------------
# Storage/copy modes
# ---------------------------------------------------------------------------

COPY_MODE_REFERENCE_ONLY: Final[str] = "reference_only"
COPY_MODE_COPY_TO_STORAGE: Final[str] = "copy_to_storage"
COPY_MODE_COPY_AND_RENAME: Final[str] = "copy_and_rename"

COPY_MODE_VALUES: Final[tuple[str, ...]] = (
    COPY_MODE_REFERENCE_ONLY,
    COPY_MODE_COPY_TO_STORAGE,
    COPY_MODE_COPY_AND_RENAME,
)


# ---------------------------------------------------------------------------
# Manifest/export contract
# ---------------------------------------------------------------------------

MANIFEST_FILENAME: Final[str] = "manifest.json"

EXPORT_TYPE_VALUES: Final[tuple[str, ...]] = (
    "xlsx_inventory",
    "koa_manifest",
    "uckkarchive_candidate",
    "public_review_package",
    "backup_snapshot",
)

DEFAULT_EXPORT_TYPE: Final[str] = "koa_manifest"


# ---------------------------------------------------------------------------
# Audit actions and entity types
# ---------------------------------------------------------------------------

AUDIT_ACTION_VALUES: Final[tuple[str, ...]] = (
    "database_initialized",
    "library_row_inserted",
    "library_row_updated",
    "library_row_archived",
    "chatgpt_intake_validated",
    "chatgpt_intake_integrated",
    "xlsx_exported",
    "xlsx_import_previewed",
    "xlsx_import_applied",
    "manifest_exported",
    "file_scanned",
    "file_copied_to_storage",
    "duplicate_detected",
    "backup_created",
    "repair_applied",
    "settings_updated",
)

AUDIT_ENTITY_TYPE_VALUES: Final[tuple[str, ...]] = (
    "database",
    "library_row",
    "media_uuid",
    "version_uuid",
    "chatgpt_intake",
    "xlsx_import",
    "manifest_export",
    "file",
    "backup",
    "settings",
)


# ---------------------------------------------------------------------------
# Result severities and validation statuses
# ---------------------------------------------------------------------------

MESSAGE_SEVERITY_VALUES: Final[tuple[str, ...]] = (
    "info",
    "warning",
    "error",
    "blocking",
)

VALIDATION_STATUS_VALUES: Final[tuple[str, ...]] = (
    "valid",
    "valid_with_warnings",
    "blocked",
    "invalid",
)


# ---------------------------------------------------------------------------
# Streamlit session state keys
# ---------------------------------------------------------------------------

SS_DB_PATH: Final[str] = "koa_db_path"
SS_STORAGE_ROOT: Final[str] = "koa_storage_root"
SS_IMPORTS_ROOT: Final[str] = "koa_imports_root"
SS_EXPORTS_ROOT: Final[str] = "koa_exports_root"
SS_BACKUP_ROOT: Final[str] = "koa_backup_root"
SS_SELECTED_VERSION_UUID: Final[str] = "koa_selected_version_uuid"
SS_SELECTED_MEDIA_UUID: Final[str] = "koa_selected_media_uuid"
SS_SELECTED_FILE_PATH: Final[str] = "koa_selected_file_path"
SS_CURRENT_FILTERS: Final[str] = "koa_current_filters"
SS_CHATGPT_RAW_RESPONSE: Final[str] = "koa_chatgpt_raw_response"
SS_CHATGPT_VALIDATION_RESULT: Final[str] = "koa_chatgpt_validation_result"
SS_CHATGPT_PREVIEW_ROW: Final[str] = "koa_chatgpt_preview_row"
SS_XLSX_IMPORT_PREVIEW: Final[str] = "koa_xlsx_import_preview"
SS_LAST_OPERATION_RESULT: Final[str] = "koa_last_operation_result"

STREAMLIT_SESSION_KEYS: Final[tuple[str, ...]] = (
    SS_DB_PATH,
    SS_STORAGE_ROOT,
    SS_IMPORTS_ROOT,
    SS_EXPORTS_ROOT,
    SS_BACKUP_ROOT,
    SS_SELECTED_VERSION_UUID,
    SS_SELECTED_MEDIA_UUID,
    SS_SELECTED_FILE_PATH,
    SS_CURRENT_FILTERS,
    SS_CHATGPT_RAW_RESPONSE,
    SS_CHATGPT_VALIDATION_RESULT,
    SS_CHATGPT_PREVIEW_ROW,
    SS_XLSX_IMPORT_PREVIEW,
    SS_LAST_OPERATION_RESULT,
)


# ---------------------------------------------------------------------------
# GUI labels required by the specification
# ---------------------------------------------------------------------------

GUI_LABEL_COPY_CHATGPT_TEMPLATE: Final[str] = "Copier template ChatGPT"
GUI_LABEL_PASTE_CHATGPT_RESPONSE: Final[str] = "Coller réponse ChatGPT"
GUI_LABEL_VALIDATE_JSON: Final[str] = "Valider JSON"
GUI_LABEL_PREVIEW_ENTRY: Final[str] = "Prévisualiser entrée"
GUI_LABEL_VALIDATE_AND_INTEGRATE: Final[str] = "Valider et intégrer"


# ---------------------------------------------------------------------------
# PowerShell scripts
# ---------------------------------------------------------------------------

PS7_SCRIPT_NAMES: Final[tuple[str, ...]] = (
    "Initialize-KoaMediathequeDb.ps1",
    "Add-KoaLibraryRow.ps1",
    "Export-KoaLibraryXlsx.ps1",
    "Import-KoaLibraryXlsx.ps1",
    "Compare-KoaLibraryXlsx.ps1",
    "Export-KoaManifest.ps1",
    "Backup-KoaMediathequeDb.ps1",
    "Repair-KoaLibraryRows.ps1",
    "Scan-KoaFiles.ps1",
    "Find-KoaDuplicates.ps1",
)

PS7_ADD_ROW_MODES: Final[tuple[str, ...]] = (
    "InsertNew",
    "UpdateExisting",
    "Upsert",
    "DryRun",
)


# ---------------------------------------------------------------------------
# Date/time conventions
# ---------------------------------------------------------------------------

UTC_TIMESTAMP_FORMAT_DESCRIPTION: Final[str] = "YYYY-MM-DDTHH:MM:SSZ"
BACKUP_FILENAME_PREFIX: Final[str] = "koa_mediatheque"


# ---------------------------------------------------------------------------
# Normalization aliases
# ---------------------------------------------------------------------------

VISIBILITY_NORMALIZATION_ALIASES: Final[dict[str, str]] = {
    "institutional": "institution",
}

BOOLEAN_TRUE_STRINGS: Final[tuple[str, ...]] = (
    "1",
    "true",
    "yes",
    "oui",
)

BOOLEAN_FALSE_STRINGS: Final[tuple[str, ...]] = (
    "0",
    "false",
    "no",
    "non",
    "",
)

