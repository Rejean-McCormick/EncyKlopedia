# 06_GUI/koa_mediatheque_gui/koa_mediatheque/models.py
# Médiathèque kOA — shared dataclasses

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from typing import Any


@dataclass
class KoaMessage:
    code: str
    severity: str  # info | warning | error | blocking
    message: str
    field: str | None = None
    row_number: int | None = None
    details: dict[str, Any] = dataclass_field(default_factory=dict)


@dataclass
class OperationResult:
    success: bool
    operation: str
    result: str
    entity_type: str | None = None
    entity_uuid: str | None = None
    media_uuid: str | None = None
    version_uuid: str | None = None
    path: str | None = None
    data: dict[str, Any] = dataclass_field(default_factory=dict)
    warnings: list[KoaMessage] = dataclass_field(default_factory=list)
    errors: list[KoaMessage] = dataclass_field(default_factory=list)


@dataclass
class ValidationResult:
    is_valid: bool
    is_blocked: bool
    normalized_data: dict[str, Any] = dataclass_field(default_factory=dict)
    warnings: list[KoaMessage] = dataclass_field(default_factory=list)
    errors: list[KoaMessage] = dataclass_field(default_factory=list)


@dataclass
class FileFacts:
    original_path: str
    filename: str
    extension: str
    mimetype: str | None
    filesize: int | None
    sha256: str | None


@dataclass
class LibraryRow:
    data: dict[str, Any]


@dataclass
class ImportPreview:
    import_uuid: str
    source_path: str
    rows_total: int
    rows_update: int
    rows_new: int
    rows_archive: int
    rows_ignore: int
    rows_blocked: int
    changes: list[dict[str, Any]]
    warnings: list[KoaMessage]
    errors: list[KoaMessage]


@dataclass
class ManifestExportResult:
    export_uuid: str
    manifest_path: str
    export_type: str
    row_count: int
    warnings: list[KoaMessage]
    errors: list[KoaMessage]