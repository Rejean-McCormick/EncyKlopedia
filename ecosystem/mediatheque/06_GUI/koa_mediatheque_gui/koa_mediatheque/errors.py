# 06_GUI/koa_mediatheque_gui/koa_mediatheque/errors.py
# Médiathèque kOA — shared error and warning codes

# ---------------------------------------------------------------------------
# JSON / metadata validation errors
# ---------------------------------------------------------------------------

ERR_JSON_PARSE = "ERR_JSON_PARSE"
ERR_REQUIRED_FIELD = "ERR_REQUIRED_FIELD"
ERR_INVALID_ENUM = "ERR_INVALID_ENUM"
ERR_INVALID_TYPE = "ERR_INVALID_TYPE"

# ---------------------------------------------------------------------------
# Blocking validation errors
# ---------------------------------------------------------------------------

ERR_BLOCKED_VERIFIED = "ERR_BLOCKED_VERIFIED"
ERR_BLOCKED_PUBLIC_EXPORT = "ERR_BLOCKED_PUBLIC_EXPORT"
ERR_BLOCKED_UCKK_EXPORT = "ERR_BLOCKED_UCKK_EXPORT"
ERR_REVIEW_REQUIRED = "ERR_REVIEW_REQUIRED"

# ---------------------------------------------------------------------------
# File / database / schema errors
# ---------------------------------------------------------------------------

ERR_FILE_NOT_FOUND = "ERR_FILE_NOT_FOUND"
ERR_DB_NOT_FOUND = "ERR_DB_NOT_FOUND"
ERR_DB_SCHEMA = "ERR_DB_SCHEMA"

# ---------------------------------------------------------------------------
# XLSX import errors
# ---------------------------------------------------------------------------

ERR_PROTECTED_FIELD_UPDATE = "ERR_PROTECTED_FIELD_UPDATE"
ERR_VERSION_UUID_MISSING = "ERR_VERSION_UUID_MISSING"
ERR_VERSION_UUID_DUPLICATE = "ERR_VERSION_UUID_DUPLICATE"
ERR_XLSX_MISSING_SHEET = "ERR_XLSX_MISSING_SHEET"
ERR_XLSX_INVALID_ACTION = "ERR_XLSX_INVALID_ACTION"

# ---------------------------------------------------------------------------
# Shared warnings
# ---------------------------------------------------------------------------

WARN_DUPLICATE_SHA256 = "WARN_DUPLICATE_SHA256"
WARN_UNKNOWN_RIGHTS = "WARN_UNKNOWN_RIGHTS"
WARN_UNKNOWN_SOURCE = "WARN_UNKNOWN_SOURCE"
WARN_RESTRICTED_CONTENT = "WARN_RESTRICTED_CONTENT"
WARN_EXTERNAL_REFERENCE = "WARN_EXTERNAL_REFERENCE"
WARN_STORAGE_COPY_SKIPPED = "WARN_STORAGE_COPY_SKIPPED"
WARN_FIELD_NORMALIZED = "WARN_FIELD_NORMALIZED"