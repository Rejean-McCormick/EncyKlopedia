# 06_GUI/koa_mediatheque_gui/koa_mediatheque/services/manifest_export_service.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from koa_mediatheque.models import KoaMessage, ManifestExportResult

try:
    from koa_mediatheque.constants import APP_PUBLIC_NAME, APP_COMPONENT
except ImportError:
    APP_PUBLIC_NAME = "Médiathèque kOA"
    APP_COMPONENT = "koa_mediatheque"

try:
    from koa_mediatheque.schema import utc_now_iso
except ImportError:
    from datetime import datetime, timezone

    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


try:
    from koa_mediatheque.repositories.library_rows_repository import list_library_rows
except ImportError:

    def list_library_rows(connection, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        connection.row_factory = _dict_row_factory
        cursor = connection.execute("SELECT * FROM library_rows ORDER BY updated_at DESC, id DESC")
        return [dict(row) for row in cursor.fetchall()]


try:
    from koa_mediatheque.services.audit_service import write_audit_log
except ImportError:

    def write_audit_log(
        connection,
        *,
        action: str,
        entity_type: str,
        entity_uuid: str | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        actor: str = "local_user",
        note: str = "",
    ):
        return None


try:
    from koa_mediatheque.validation.blocking_rules import (
        is_public_export_blocked,
        is_uckk_export_blocked,
    )
except ImportError:

    def is_public_export_blocked(metadata: dict[str, Any]) -> bool:
        return _fallback_public_export_blocked(metadata)

    def is_uckk_export_blocked(metadata: dict[str, Any]) -> bool:
        return _fallback_uckk_export_blocked(metadata)


MANIFEST_FILENAME = "manifest.json"

EXPORT_TYPE_VALUES = {
    "xlsx_inventory",
    "koa_manifest",
    "uckkarchive_candidate",
    "public_review_package",
    "backup_snapshot",
}

_PUBLIC_EXPORT_TYPES = {
    "public_review_package",
}

_UCKK_EXPORT_TYPES = {
    "uckkarchive_candidate",
}

_JSON_TEXT_FIELDS = {
    "collections_json",
    "tags_json",
    "relations_json",
    "content_flags_json",
}


def export_manifest(
    connection,
    output_dir: str | Path,
    *,
    export_type: str,
    filters: dict[str, Any] | None = None,
    actor: str = "local_user",
    reason: str = "",
) -> ManifestExportResult:
    """
    Export a canonical Médiathèque kOA manifest.json.

    The manifest is metadata-only. It does not copy files and does not bypass
    rights, visibility, validation, restriction, redaction, or export policy.
    """
    export_uuid = str(uuid4())
    normalized_export_type = _normalize_export_type(export_type)
    output_path = Path(output_dir).expanduser() / MANIFEST_FILENAME
    warnings: list[KoaMessage] = []
    errors: list[KoaMessage] = []

    if normalized_export_type not in EXPORT_TYPE_VALUES:
        return ManifestExportResult(
            export_uuid=export_uuid,
            manifest_path=str(output_path),
            export_type=normalized_export_type,
            row_count=0,
            warnings=[],
            errors=[
                KoaMessage(
                    code="ERR_INVALID_EXPORT_TYPE",
                    severity="blocking",
                    field="export_type",
                    message=(
                        "Type d'export manifest invalide. Valeurs permises : "
                        + ", ".join(sorted(EXPORT_TYPE_VALUES))
                    ),
                    details={"export_type": export_type},
                )
            ],
        )

    try:
        rows = list_library_rows(connection, filters=filters)
    except Exception as exc:
        return ManifestExportResult(
            export_uuid=export_uuid,
            manifest_path=str(output_path),
            export_type=normalized_export_type,
            row_count=0,
            warnings=[],
            errors=[
                KoaMessage(
                    code="ERR_MANIFEST_ROW_QUERY_FAILED",
                    severity="blocking",
                    field=None,
                    message=f"Impossible de lire library_rows pour le manifest : {exc}",
                )
            ],
        )

    eligible_rows, eligibility_warnings, eligibility_errors = _filter_rows_for_export_type(
        rows,
        export_type=normalized_export_type,
    )
    warnings.extend(eligibility_warnings)
    errors.extend(eligibility_errors)

    if errors:
        return ManifestExportResult(
            export_uuid=export_uuid,
            manifest_path=str(output_path),
            export_type=normalized_export_type,
            row_count=0,
            warnings=warnings,
            errors=errors,
        )

    try:
        manifest = build_manifest_dict(
            eligible_rows,
            export_uuid=export_uuid,
            export_type=normalized_export_type,
            actor=actor,
            reason=reason,
        )

        manifest["filters"] = filters or {}
        manifest["source_row_count"] = len(rows)
        manifest["excluded_row_count"] = len(rows) - len(eligible_rows)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        _safe_write_audit_log(
            connection,
            export_uuid=export_uuid,
            export_type=normalized_export_type,
            manifest_path=output_path,
            row_count=len(eligible_rows),
            actor=actor,
            reason=reason,
            manifest=manifest,
        )

        return ManifestExportResult(
            export_uuid=export_uuid,
            manifest_path=str(output_path),
            export_type=normalized_export_type,
            row_count=len(eligible_rows),
            warnings=warnings,
            errors=[],
        )

    except Exception as exc:
        return ManifestExportResult(
            export_uuid=export_uuid,
            manifest_path=str(output_path),
            export_type=normalized_export_type,
            row_count=0,
            warnings=warnings,
            errors=[
                KoaMessage(
                    code="ERR_MANIFEST_EXPORT_FAILED",
                    severity="blocking",
                    field=None,
                    message=f"Export manifest impossible : {exc}",
                )
            ],
        )


def build_manifest_dict(
    rows: list[dict[str, Any]],
    *,
    export_uuid: str,
    export_type: str,
    actor: str,
    reason: str,
) -> dict[str, Any]:
    """
    Build the canonical manifest dictionary.

    Required contents include app identity, export identity, row count, media
    UUIDs, version UUIDs, file hashes, sizes, MIME types, visibility, public
    state, restrictions, suitability, provenance, collections, tags, relations,
    validation state, and export policy.
    """
    normalized_rows = [_manifest_row(row) for row in rows]

    return {
        "app_name": APP_PUBLIC_NAME,
        "app_component": APP_COMPONENT,
        "manifest_filename": MANIFEST_FILENAME,
        "export_uuid": export_uuid,
        "export_type": export_type,
        "export_timestamp": utc_now_iso(),
        "export_actor": actor,
        "export_reason": reason,
        "row_count": len(normalized_rows),
        "media_uuids": _unique_sorted(row.get("media_uuid") for row in rows),
        "version_uuids": _unique_sorted(row.get("version_uuid") for row in rows),
        "file_hashes": _unique_sorted(row.get("sha256") for row in rows),
        "file_sizes": _file_size_index(rows),
        "mime_types": _unique_sorted(row.get("mimetype") for row in rows),
        "visibility_values": _unique_sorted(row.get("visibility") for row in rows),
        "public_state_values": _unique_sorted(row.get("public_state") for row in rows),
        "restricted_flags": _restricted_flag_summary(rows),
        "audience_suitability_values": _unique_sorted(
            row.get("audience_suitability") for row in rows
        ),
        "provenance_values": _unique_sorted(row.get("provenance") for row in rows),
        "validation_state_values": _unique_sorted(
            row.get("canonical_validation_state") for row in rows
        ),
        "export_policy_values": {
            "export_to_uckk": _unique_sorted(row.get("export_to_uckk") for row in rows),
            "export_to_public": _unique_sorted(row.get("export_to_public") for row in rows),
            "target_export_allowed": _unique_sorted(
                row.get("target_export_allowed") for row in rows
            ),
            "target_system": _unique_sorted(row.get("target_system") for row in rows),
        },
        "collections": _unique_sorted_from_json_field(rows, "collections_json"),
        "tags": _unique_sorted_from_json_field(rows, "tags_json"),
        "relations": _unique_sorted_from_json_field(rows, "relations_json"),
        "content_flags": _unique_sorted_from_json_field(rows, "content_flags_json"),
        "rows": normalized_rows,
    }


def _manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "media_uuid": row.get("media_uuid"),
        "version_uuid": row.get("version_uuid"),
        "title": row.get("title"),
        "subtitle": row.get("subtitle"),
        "description": row.get("description"),
        "summary": row.get("summary"),
        "file": {
            "original_path": row.get("original_path"),
            "storage_path": row.get("storage_path"),
            "filename": row.get("filename"),
            "extension": row.get("extension"),
            "mimetype": row.get("mimetype"),
            "filesize": row.get("filesize"),
            "sha256": row.get("sha256"),
            "filearea": row.get("filearea"),
            "media_type": row.get("media_type"),
            "language": row.get("language"),
        },
        "classification": {
            "library_scope": row.get("library_scope"),
            "uckk_relevance": row.get("uckk_relevance"),
            "target_system": row.get("target_system"),
            "target_export_allowed": row.get("target_export_allowed"),
        },
        "access": {
            "public_state": row.get("public_state"),
            "visibility": row.get("visibility"),
            "access_level": row.get("access_level"),
        },
        "source_and_rights": {
            "ownership_scope": row.get("ownership_scope"),
            "source_type": row.get("source_type"),
            "source_ownership": row.get("source_ownership"),
            "rights_status": row.get("rights_status"),
            "rights_note": row.get("rights_note"),
        },
        "restriction_and_sensitivity": {
            "restriction_state": row.get("restriction_state"),
            "restriction_reason": row.get("restriction_reason"),
            "redaction_required": row.get("redaction_required"),
            "content_flags": _json_text_to_list(row.get("content_flags_json")),
            "audience_suitability": row.get("audience_suitability"),
        },
        "lifecycle": {
            "status": row.get("status"),
            "provenance": row.get("provenance"),
        },
        "validation": {
            "ai_validation_state": row.get("ai_validation_state"),
            "ai_confidence": row.get("ai_confidence"),
            "canonical_validation_state": row.get("canonical_validation_state"),
            "human_review_required": row.get("human_review_required"),
            "review_queue": row.get("review_queue"),
            "review_reason": row.get("review_reason"),
        },
        "collections": _json_text_to_list(row.get("collections_json")),
        "tags": _json_text_to_list(row.get("tags_json")),
        "relations": _json_text_to_list(row.get("relations_json")),
        "export_policy": {
            "export_to_uckk": row.get("export_to_uckk"),
            "export_to_public": row.get("export_to_public"),
            "export_policy_note": row.get("export_policy_note"),
        },
        "audit": {
            "import_batch": row.get("import_batch"),
            "notes": row.get("notes"),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        },
    }


def _filter_rows_for_export_type(
    rows: list[dict[str, Any]],
    *,
    export_type: str,
) -> tuple[list[dict[str, Any]], list[KoaMessage], list[KoaMessage]]:
    warnings: list[KoaMessage] = []
    errors: list[KoaMessage] = []

    if export_type not in _PUBLIC_EXPORT_TYPES and export_type not in _UCKK_EXPORT_TYPES:
        return rows, warnings, errors

    eligible_rows: list[dict[str, Any]] = []
    blocked_rows: list[dict[str, Any]] = []

    for row in rows:
        if export_type in _PUBLIC_EXPORT_TYPES and is_public_export_blocked(row):
            blocked_rows.append(row)
            continue

        if export_type in _UCKK_EXPORT_TYPES and is_uckk_export_blocked(row):
            blocked_rows.append(row)
            continue

        eligible_rows.append(row)

    if blocked_rows:
        errors.append(
            KoaMessage(
                code="ERR_MANIFEST_EXPORT_BLOCKED",
                severity="blocking",
                field="export_type",
                message=(
                    f"Export {export_type} bloqué : certaines lignes ne respectent pas "
                    "les règles de droits, visibilité, restriction, revue humaine ou politique d'export."
                ),
                details={
                    "blocked_count": len(blocked_rows),
                    "blocked_version_uuids": [
                        row.get("version_uuid")
                        for row in blocked_rows
                        if row.get("version_uuid")
                    ],
                },
            )
        )

    return eligible_rows, warnings, errors


def _fallback_public_export_blocked(row: dict[str, Any]) -> bool:
    if str(row.get("export_to_public", "no")).lower() != "yes":
        return True

    if str(row.get("public_state", "unknown")).lower() != "public":
        return True

    if str(row.get("visibility", "private")).lower() != "public":
        return True

    if str(row.get("rights_status", "unknown")).lower() in {"unknown", "third_party"}:
        return True

    if str(row.get("restriction_state", "none")).lower() not in {"none", ""}:
        return True

    if _int_bool(row.get("human_review_required")) == 1:
        return True

    return False


def _fallback_uckk_export_blocked(row: dict[str, Any]) -> bool:
    if str(row.get("export_to_uckk", "no")).lower() != "yes":
        return True

    if str(row.get("target_system", "none")).lower() != "uckkarchive":
        return True

    if str(row.get("uckk_relevance", "unknown")).lower() in {"not_uckk", "unknown"}:
        return True

    if _int_bool(row.get("target_export_allowed")) != 1:
        return True

    if str(row.get("rights_status", "unknown")).lower() == "unknown":
        return True

    if _int_bool(row.get("human_review_required")) == 1:
        return True

    return False


def _restricted_flag_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    restricted_rows = []

    for row in rows:
        restriction_state = str(row.get("restriction_state") or "none").lower()
        visibility = str(row.get("visibility") or "").lower()
        access_level = str(row.get("access_level") or "").lower()
        redaction_required = _int_bool(row.get("redaction_required"))

        if (
            restriction_state not in {"", "none"}
            or visibility in {"restricted", "restricted_integrity", "restricted_cultural"}
            or access_level in {"restricted", "confidential"}
            or redaction_required == 1
        ):
            restricted_rows.append(row)

    return {
        "restricted_count": len(restricted_rows),
        "restricted_version_uuids": [
            row.get("version_uuid")
            for row in restricted_rows
            if row.get("version_uuid")
        ],
        "restriction_states": _unique_sorted(
            row.get("restriction_state") for row in restricted_rows
        ),
        "redaction_required_count": sum(
            1 for row in rows if _int_bool(row.get("redaction_required")) == 1
        ),
        "human_review_required_count": sum(
            1 for row in rows if _int_bool(row.get("human_review_required")) == 1
        ),
    }


def _file_size_index(rows: list[dict[str, Any]]) -> dict[str, int | None]:
    index: dict[str, int | None] = {}

    for row in rows:
        version_uuid = row.get("version_uuid")
        if not version_uuid:
            continue
        index[str(version_uuid)] = _int_or_none(row.get("filesize"))

    return index


def _unique_sorted_from_json_field(rows: list[dict[str, Any]], field_name: str) -> list[str]:
    values: list[Any] = []

    for row in rows:
        values.extend(_json_text_to_list(row.get(field_name)))

    return _unique_sorted(values)


def _json_text_to_list(value: Any) -> list[Any]:
    if value is None:
        return []

    if isinstance(value, list):
        return _clean_list(value)

    if isinstance(value, tuple | set):
        return _clean_list(list(value))

    if not isinstance(value, str):
        return [value]

    stripped = value.strip()
    if not stripped:
        return []

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return [
            item.strip()
            for item in stripped.split(";")
            if item.strip()
        ]

    if isinstance(parsed, list):
        return _clean_list(parsed)

    return [parsed]


def _clean_list(values: list[Any]) -> list[Any]:
    cleaned: list[Any] = []

    for value in values:
        if value is None:
            continue

        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                cleaned.append(stripped)
            continue

        cleaned.append(value)

    return cleaned


def _unique_sorted(values: Any) -> list[str]:
    cleaned: set[str] = set()

    for value in values:
        if value is None:
            continue

        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                cleaned.add(stripped)
            continue

        cleaned.add(str(value))

    return sorted(cleaned)


def _normalize_export_type(export_type: str) -> str:
    return str(export_type or "").strip().lower()


def _int_bool(value: Any) -> int:
    if isinstance(value, bool):
        return 1 if value else 0

    if isinstance(value, int):
        return 1 if value == 1 else 0

    if isinstance(value, float):
        return 1 if value == 1.0 else 0

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "oui"}:
            return 1
        if normalized in {"0", "false", "no", "non"}:
            return 0

    return 0


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return int(float(stripped.replace(",", ".")))
        except ValueError:
            return None

    return None


def _safe_write_audit_log(
    connection,
    *,
    export_uuid: str,
    export_type: str,
    manifest_path: Path,
    row_count: int,
    actor: str,
    reason: str,
    manifest: dict[str, Any],
) -> None:
    try:
        write_audit_log(
            connection,
            action="manifest_exported",
            entity_type="manifest_export",
            entity_uuid=export_uuid,
            before=None,
            after={
                "export_uuid": export_uuid,
                "export_type": export_type,
                "manifest_path": str(manifest_path),
                "row_count": row_count,
                "actor": actor,
                "reason": reason,
                "manifest_summary": {
                    "media_uuids": manifest.get("media_uuids", []),
                    "version_uuids": manifest.get("version_uuids", []),
                    "row_count": manifest.get("row_count", 0),
                },
            },
            actor=actor,
            note="Canonical manifest.json exported.",
        )
    except Exception:
        return


def _dict_row_factory(cursor, row):
    return {
        cursor.description[index][0]: value
        for index, value in enumerate(row)
    }