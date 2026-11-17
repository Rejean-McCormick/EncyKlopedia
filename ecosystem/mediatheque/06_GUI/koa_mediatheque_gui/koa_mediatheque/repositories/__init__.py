# 06_GUI/koa_mediatheque_gui/koa_mediatheque/repositories/__init__.py
"""SQLite repository layer for Médiathèque kOA.

Repositories are intentionally thin:
- receive an already-open sqlite3.Connection;
- never own or close the connection;
- execute SQL and return dictionaries or OperationResult objects;
- do not perform business validation, file hashing, storage copying, XLSX parsing,
  or Streamlit UI work.

Public functions are lazy-loaded to avoid import-order problems while the project
is implemented in parallel.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any


_REPOSITORY_EXPORTS: dict[str, str] = {
    # library_rows_repository.py
    "list_library_rows": "library_rows_repository",
    "get_library_row_by_id": "library_rows_repository",
    "get_library_row_by_version_uuid": "library_rows_repository",
    "get_library_rows_by_media_uuid": "library_rows_repository",
    "get_library_rows_by_sha256": "library_rows_repository",
    "insert_library_row": "library_rows_repository",
    "update_library_row_by_version_uuid": "library_rows_repository",
    "soft_delete_library_row": "library_rows_repository",

    # schema_meta_repository.py
    "get_schema_meta": "schema_meta_repository",
    "set_schema_meta": "schema_meta_repository",
    "list_schema_meta": "schema_meta_repository",

    # chatgpt_intake_log_repository.py
    "insert_chatgpt_intake_log": "chatgpt_intake_log_repository",
    "list_chatgpt_intake_log": "chatgpt_intake_log_repository",

    # xlsx_import_log_repository.py
    "insert_xlsx_import_log": "xlsx_import_log_repository",
    "list_xlsx_import_log": "xlsx_import_log_repository",

    # file_scan_log_repository.py
    "insert_file_scan_log": "file_scan_log_repository",
    "list_file_scan_log": "file_scan_log_repository",

    # audit_log_repository.py
    "insert_audit_log": "audit_log_repository",
    "list_audit_log": "audit_log_repository",
}


REPOSITORY_MODULES: tuple[str, ...] = (
    "library_rows_repository",
    "schema_meta_repository",
    "chatgpt_intake_log_repository",
    "xlsx_import_log_repository",
    "file_scan_log_repository",
    "audit_log_repository",
)


__all__ = (
    "REPOSITORY_MODULES",
    *_REPOSITORY_EXPORTS.keys(),
)


def __getattr__(name: str) -> Any:
    """Lazy-load public repository functions.

    This keeps `import koa_mediatheque.repositories` safe even when individual
    repository modules are being developed independently.
    """
    module_name = _REPOSITORY_EXPORTS.get(name)

    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(f"{__name__}.{module_name}")
    value = getattr(module, name)

    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return public names exposed by this package."""
    return sorted(set(globals()) | set(__all__))