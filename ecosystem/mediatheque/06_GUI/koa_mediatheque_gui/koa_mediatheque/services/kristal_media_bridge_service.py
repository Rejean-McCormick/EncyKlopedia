"""Médiathèque kOA ↔ Interaction Kernel ↔ DaaT ↔ Kristal/Kristall media bridge.

Médiathèque kOA keeps ownership of local bytes, physical versions and integrity
facts. The bridge exports owner-preserving immutable ``ArtifactRef`` and
``ExportManifest`` documents using the stable IK 1.1 artifact schemas. DaaT
(machine id ``daat``) is only the optional admission/explicit contract-mapping
boundary; it does not own source bytes or Kristall semantic identity.

The portable Kristal interface remains ``kristal_state/6.0`` while Kristall v7
is additive above it.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote, unquote
from uuid import uuid4

from koa_mediatheque.models import KoaMessage, OperationResult
from koa_mediatheque.repositories.library_rows_repository import (
    get_library_row_by_version_uuid,
    list_library_rows,
    update_library_row_by_version_uuid,
)
from koa_mediatheque.schema import APP_COMPONENT, APP_PUBLIC_NAME, utc_now_iso
from koa_mediatheque.services.audit_service import write_audit_log

IK_SCHEMA_VERSION = "1.1"
IK_BASELINE_VERSION = "2.0.0-dev.2"
DAAT_HUMAN_NAME = "DaaT"
DAAT_SYSTEM_ID = "daat"
KRISTAL_PORTABLE_STANDARD_VERSION = "6.0.0"
KRISTAL_PORTABLE_CONTRACT = "kristal_state/6.0"
KRISTALL_DESIGN_BASELINE = "7.0.0-draft.3.2"
# Backward-compatible alias used by existing callers.
KRISTAL_STANDARD_VERSION = KRISTAL_PORTABLE_STANDARD_VERSION
BRIDGE_PROFILE = "koa.mediatheque.kristal-media/1.1.0"
BRIDGE_INTEGRITY_PROFILE = "koa.mediatheque.export-manifest/jcs-rfc8785+sha256/v1"
ARTIFACT_TYPE = "koa.media"
KRISTAL_RELATION_PREFIX = "kristal:"
LOCATOR_PREFIX = "koa-media://version/"
ARTIFACT_REFS_FILENAME = "kristal-artifact-refs.json"
EXPORT_MANIFEST_FILENAME = "kristal-export-manifest.json"

_SHA256_RE = re.compile(r"^(?:sha256:)?([a-f0-9]{64})$")
_RELATION_KIND_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
_MAX_IJSON_INTEGER = 9007199254740991


class KristalBridgeError(ValueError):
    """Raised for invalid bridge data that must fail closed."""


def make_kristal_relation(kind: str, identifier: str) -> str:
    """Build the canonical ``kristal:<kind>:<identifier>`` relation string."""
    normalized_kind = str(kind or "").strip().lower()
    normalized_identifier = str(identifier or "").strip()

    if not _RELATION_KIND_RE.fullmatch(normalized_kind):
        raise KristalBridgeError(
            "Kristal relation kind must match [a-z0-9][a-z0-9._-]{0,79}."
        )
    if not normalized_identifier:
        raise KristalBridgeError("Kristal relation identifier is required.")
    if any(ord(char) < 0x20 for char in normalized_identifier):
        raise KristalBridgeError("Kristal relation identifier contains control characters.")

    return f"{KRISTAL_RELATION_PREFIX}{normalized_kind}:{normalized_identifier}"


def get_kristal_relations(row: Mapping[str, Any]) -> list[str]:
    """Return normalized Kristal relation strings from one library row."""
    return [
        relation
        for relation in _json_text_to_list(row.get("relations_json"))
        if isinstance(relation, str) and relation.startswith(KRISTAL_RELATION_PREFIX)
    ]


def is_kristal_linked(row: Mapping[str, Any]) -> bool:
    """Return True when the row carries at least one explicit Kristal relation."""
    return bool(get_kristal_relations(row))


def link_media_to_kristal(
    connection,
    version_uuid: str,
    *,
    relation_kind: str,
    relation_id: str,
    actor: str = "local_user",
) -> OperationResult:
    """Add one explicit Kristal relation to an existing media version."""
    row = get_library_row_by_version_uuid(connection, str(version_uuid or "").strip())
    if row is None:
        return _failure(
            operation="link_media_to_kristal",
            result="not_found",
            code="ERR_KRISTAL_MEDIA_NOT_FOUND",
            message="Aucune version média ne correspond au version_uuid fourni.",
            version_uuid=version_uuid or None,
        )

    try:
        relation = make_kristal_relation(relation_kind, relation_id)
    except KristalBridgeError as exc:
        return _failure(
            operation="link_media_to_kristal",
            result="invalid_relation",
            code="ERR_KRISTAL_RELATION",
            message=str(exc),
            version_uuid=str(row.get("version_uuid") or "") or None,
            media_uuid=str(row.get("media_uuid") or "") or None,
        )

    relations = _json_text_to_list(row.get("relations_json"))
    if relation in relations:
        return OperationResult(
            success=True,
            operation="link_media_to_kristal",
            result="already_linked",
            entity_type="library_row",
            entity_uuid=str(row.get("version_uuid") or "") or None,
            media_uuid=str(row.get("media_uuid") or "") or None,
            version_uuid=str(row.get("version_uuid") or "") or None,
            data={"relation": relation, "row": row},
        )

    new_relations = [*relations, relation]
    update_result = update_library_row_by_version_uuid(
        connection,
        str(row["version_uuid"]),
        {"relations_json": json.dumps(new_relations, ensure_ascii=False)},
        actor=actor,
    )
    if not update_result.success:
        return update_result

    _safe_audit(
        connection,
        actor=actor,
        version_uuid=str(row["version_uuid"]),
        before={"relations": relations},
        after={"relations": new_relations, "kristal_relation_added": relation},
        note="Kristal media relation added through the local bridge.",
    )

    updated_row = get_library_row_by_version_uuid(connection, str(row["version_uuid"]))

    return OperationResult(
        success=True,
        operation="link_media_to_kristal",
        result="linked",
        entity_type="library_row",
        entity_uuid=str(row["version_uuid"]),
        media_uuid=str(row.get("media_uuid") or "") or None,
        version_uuid=str(row["version_uuid"]),
        data={
            "relation": relation,
            "relations": new_relations,
            "row": updated_row,
        },
        warnings=list(update_result.warnings),
        errors=[],
    )


def build_artifact_ref(
    row: Mapping[str, Any],
    *,
    owner_instance: str | None = None,
    owner_organization: str | None = None,
) -> dict[str, Any]:
    """Build an IK 1.1 ArtifactRef without exposing a local filesystem path."""
    media_uuid = _required_text(row, "media_uuid")
    version_uuid = _required_text(row, "version_uuid")
    digest = _normalize_sha256(row.get("sha256"))

    owner: dict[str, Any] = {"system": APP_COMPONENT}
    if owner_instance:
        owner["instance"] = owner_instance
    if owner_organization:
        owner["organization"] = owner_organization

    content: dict[str, Any] = {"contract_ref": BRIDGE_PROFILE}
    mimetype = _optional_text(row.get("mimetype"))
    if mimetype:
        content["media_type"] = mimetype

    artifact_ref: dict[str, Any] = {
        "owner": owner,
        "artifact_type": ARTIFACT_TYPE,
        "artifact_id": _media_artifact_id(media_uuid),
        "version": version_uuid,
        "integrity": {"algorithm": "sha256", "digest": digest},
        "locator": {"ref": _locator_for_version(version_uuid)},
        "content": content,
        "scope": _drop_none(
            {
                "library_scope": row.get("library_scope"),
                "media_type": row.get("media_type"),
                "kristal_relations": get_kristal_relations(row),
            }
        ),
        "provenance": _drop_none(
            {
                "source_system": APP_COMPONENT,
                "source_table": "library_rows",
                "local_provenance": row.get("provenance"),
            }
        ),
        "access": _drop_none(
            {
                "public_state": row.get("public_state"),
                "visibility": row.get("visibility"),
                "access_level": row.get("access_level"),
                "rights_status": row.get("rights_status"),
                "restriction_state": row.get("restriction_state"),
            }
        ),
    }
    validate_artifact_ref(artifact_ref)
    return artifact_ref


def build_export_manifest(
    rows: list[Mapping[str, Any]],
    *,
    export_uuid: str,
    snapshot_at: str,
    source_revision: str | None = None,
    producer_instance: str | None = None,
    producer_organization: str | None = None,
) -> dict[str, Any]:
    """Build and validate a source-owned IK 1.1 ExportManifest."""
    if not rows:
        raise KristalBridgeError("At least one Kristal-linked media row is required.")
    if len(rows) > 1000:
        raise KristalBridgeError("A Kristal media export may contain at most 1000 subjects.")

    refs = [
        build_artifact_ref(
            row,
            owner_instance=producer_instance,
            owner_organization=producer_organization,
        )
        for row in rows
    ]

    producer: dict[str, Any] = {"system": APP_COMPONENT}
    if producer_instance:
        producer["instance"] = producer_instance
    if producer_organization:
        producer["organization"] = producer_organization

    subjects: list[dict[str, str]] = []
    seen_subjects: set[str] = set()
    for artifact_ref in refs:
        artifact_id = artifact_ref["artifact_id"]
        if artifact_id not in seen_subjects:
            seen_subjects.add(artifact_id)
            subjects.append({"type": "media", "id": artifact_id})

    items = [
        {
            "type": artifact_ref["artifact_type"],
            "ref": artifact_ref["locator"]["ref"],
            "digest": f"sha256:{_normalize_sha256(artifact_ref['integrity']['digest'])}",
        }
        for artifact_ref in refs
    ]

    manifest: dict[str, Any] = {
        "id": f"urn:koa-mediatheque:export:{export_uuid}",
        "profile": BRIDGE_PROFILE,
        "producer": producer,
        "snapshot_at": snapshot_at,
        "scope": {
            "kind": "kristal-linked-local-media",
            "row_count": len(rows),
            "relation_prefix": KRISTAL_RELATION_PREFIX,
        },
        "subjects": subjects,
        "items": items,
        "intended_use": ["kristal-input", "local-media-resolution"],
        "provenance": {
            "source_owner": APP_COMPONENT,
            "source_table": "library_rows",
            "source_application": APP_PUBLIC_NAME,
            "kristal_standard": KRISTAL_STANDARD_VERSION,
            "kristal_portable_standard": KRISTAL_PORTABLE_STANDARD_VERSION,
            "kristal_portable_contract": KRISTAL_PORTABLE_CONTRACT,
            "kristall_design_baseline": KRISTALL_DESIGN_BASELINE,
            "interaction_kernel": IK_BASELINE_VERSION,
            "interaction_kernel_schema": IK_SCHEMA_VERSION,
            "daat": {"human_name": DAAT_HUMAN_NAME, "system": DAAT_SYSTEM_ID},
            "integrity_profile": BRIDGE_INTEGRITY_PROFILE,
            "integrity_hash_target": "manifest object with top-level integrity omitted",
        },
    }
    if source_revision:
        manifest["source_revision"] = source_revision

    digest = hashlib.sha256(_jcs_canonicalize(manifest).encode("utf-8")).hexdigest()
    manifest["integrity"] = {"algorithm": "sha256", "digest": f"sha256:{digest}"}
    validate_export_manifest(manifest)
    return manifest


def export_kristal_media_bundle(
    connection,
    output_dir: str | Path,
    *,
    filters: dict[str, Any] | None = None,
    actor: str = "local_user",
    reason: str = "",
    producer_instance: str | None = None,
    producer_organization: str | None = None,
) -> OperationResult:
    """Export all explicitly Kristal-linked local media as IK boundary artifacts."""
    operation = "export_kristal_media_bundle"
    export_uuid = str(uuid4())
    output_root = Path(output_dir).expanduser()
    refs_path = output_root / ARTIFACT_REFS_FILENAME
    manifest_path = output_root / EXPORT_MANIFEST_FILENAME

    query_filters = dict(filters or {})
    query_filters.setdefault("limit", 10_000)
    query_filters.setdefault("offset", 0)

    try:
        source_rows = list_library_rows(connection, filters=query_filters)
    except Exception as exc:
        return _failure(
            operation=operation,
            result="query_failed",
            code="ERR_KRISTAL_EXPORT_QUERY",
            message=f"Impossible de lire library_rows : {exc}",
            details={"exception_type": type(exc).__name__},
        )

    rows = [row for row in source_rows if is_kristal_linked(row)]
    if not rows:
        return _failure(
            operation=operation,
            result="no_linked_media",
            code="ERR_KRISTAL_NO_LINKED_MEDIA",
            message=(
                "Aucun média explicitement lié à Kristal. Ajoutez une relation "
                "kristal:<kind>:<id> dans relations_json avant l’export."
            ),
            details={"source_row_count": len(source_rows)},
        )

    invalid_rows: list[dict[str, str]] = []
    for row in rows:
        try:
            _required_text(row, "media_uuid")
            _required_text(row, "version_uuid")
            _normalize_sha256(row.get("sha256"))
        except KristalBridgeError as exc:
            invalid_rows.append(
                {
                    "version_uuid": str(row.get("version_uuid") or ""),
                    "reason": str(exc),
                }
            )

    if invalid_rows:
        return _failure(
            operation=operation,
            result="invalid_linked_media",
            code="ERR_KRISTAL_EXPORT_INTEGRITY",
            message="L’export Kristal exige un SHA-256 local valide pour chaque média lié.",
            details={"invalid_rows": invalid_rows},
        )

    snapshot_at = utc_now_iso()
    try:
        artifact_refs = [
            build_artifact_ref(
                row,
                owner_instance=producer_instance,
                owner_organization=producer_organization,
            )
            for row in rows
        ]
        manifest = build_export_manifest(
            rows,
            export_uuid=export_uuid,
            snapshot_at=snapshot_at,
            source_revision=f"library_rows@{snapshot_at}",
            producer_instance=producer_instance,
            producer_organization=producer_organization,
        )

        output_root.mkdir(parents=True, exist_ok=True)
        refs_path.write_text(
            json.dumps(
                {
                    "profile": BRIDGE_PROFILE,
                    "export_id": manifest["id"],
                    "artifact_refs": artifact_refs,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    except Exception as exc:
        return _failure(
            operation=operation,
            result="export_failed",
            code="ERR_KRISTAL_EXPORT_FAILED",
            message=f"Export du pont média Kristal impossible : {exc}",
            details={"exception_type": type(exc).__name__},
        )

    _safe_audit(
        connection,
        actor=actor,
        version_uuid=export_uuid,
        before=None,
        after={
            "export_type": "kristal_media_bridge",
            "export_uuid": export_uuid,
            "row_count": len(rows),
            "manifest_path": str(manifest_path),
            "artifact_refs_path": str(refs_path),
            "reason": reason,
        },
        note="Kristal media bridge export created.",
        entity_type="manifest_export",
        action="manifest_exported",
    )

    return OperationResult(
        success=True,
        operation=operation,
        result="exported",
        entity_type="manifest_export",
        entity_uuid=export_uuid,
        path=str(manifest_path),
        data={
            "export_uuid": export_uuid,
            "row_count": len(rows),
            "source_row_count": len(source_rows),
            "manifest_path": str(manifest_path),
            "artifact_refs_path": str(refs_path),
            "profile": BRIDGE_PROFILE,
            "kristal_standard": KRISTAL_STANDARD_VERSION,
            "kristal_portable_standard": KRISTAL_PORTABLE_STANDARD_VERSION,
            "kristal_portable_contract": KRISTAL_PORTABLE_CONTRACT,
            "kristall_design_baseline": KRISTALL_DESIGN_BASELINE,
            "interaction_kernel": IK_BASELINE_VERSION,
            "interaction_kernel_schema": IK_SCHEMA_VERSION,
            "daat": {"human_name": DAAT_HUMAN_NAME, "system": DAAT_SYSTEM_ID},
        },
    )


def resolve_koa_media_locator(connection, locator_ref: str) -> dict[str, Any] | None:
    """Resolve a local opaque ``koa-media://`` locator back to a library row."""
    normalized = str(locator_ref or "").strip()
    if not normalized.startswith(LOCATOR_PREFIX):
        return None
    encoded_version = normalized[len(LOCATOR_PREFIX) :]
    if not encoded_version:
        return None
    version_uuid = unquote(encoded_version)
    return get_library_row_by_version_uuid(connection, version_uuid)


def validate_artifact_ref(artifact_ref: Mapping[str, Any]) -> None:
    """Validate against the pinned IK 1.1 ArtifactRef JSON Schema."""
    _validate_with_bundled_schema("artifact-ref.schema.json", artifact_ref)


def validate_export_manifest(manifest: Mapping[str, Any]) -> None:
    """Validate against the pinned IK 1.1 ExportManifest JSON Schema."""
    _validate_with_bundled_schema("export-manifest.schema.json", manifest)


def _validate_with_bundled_schema(filename: str, value: Mapping[str, Any]) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:  # pragma: no cover - dependency contract
        raise KristalBridgeError(
            "jsonschema is required for Kristal bridge contract validation."
        ) from exc

    schema_path = _contracts_dir() / filename
    if not schema_path.is_file():
        raise KristalBridgeError(f"Pinned Kristal/IK schema not found: {schema_path}")

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(dict(value)), key=lambda error: list(error.path))
    if errors:
        summary = "; ".join(error.message for error in errors[:5])
        raise KristalBridgeError(f"IK {IK_SCHEMA_VERSION} schema validation failed: {summary}")


def _contracts_dir() -> Path:
    here = Path(__file__).resolve()

    packaged = here.parents[1] / "contracts" / "kristal_ik_1_1"
    if packaged.is_dir():
        return packaged

    for parent in here.parents:
        candidate = parent / "contracts" / f"kristal-ik-{IK_SCHEMA_VERSION}"
        if candidate.is_dir():
            return candidate
    raise KristalBridgeError("Pinned Kristal/IK contracts directory is missing.")


def _media_artifact_id(media_uuid: str) -> str:
    return f"urn:koa-mediatheque:media:{quote(media_uuid, safe='')}"


def _locator_for_version(version_uuid: str) -> str:
    return f"{LOCATOR_PREFIX}{quote(version_uuid, safe='')}"


def _normalize_sha256(value: Any) -> str:
    text = str(value or "").strip().lower()
    match = _SHA256_RE.fullmatch(text)
    if not match:
        raise KristalBridgeError("sha256 must be a lowercase 64-character SHA-256 digest.")
    return match.group(1)


def _required_text(row: Mapping[str, Any], field_name: str) -> str:
    value = _optional_text(row.get(field_name))
    if not value:
        raise KristalBridgeError(f"{field_name} is required for Kristal media export.")
    return value


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _drop_none(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item is not None}


def _json_text_to_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)

    text = str(value).strip()
    if not text:
        return []

    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return [item.strip() for item in text.split(";") if item.strip()]

    if isinstance(parsed, list):
        return parsed
    if parsed is None:
        return []
    return [parsed]


def _safe_audit(
    connection,
    *,
    actor: str,
    version_uuid: str,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
    note: str,
    action: str = "library_row_updated",
    entity_type: str = "library_row",
) -> None:
    try:
        write_audit_log(
            connection,
            action=action,
            entity_type=entity_type,
            entity_uuid=version_uuid,
            before=before,
            after=after,
            actor=actor,
            note=note,
        )
    except Exception:
        # The source operation remains valid even if audit logging itself fails.
        pass


def _failure(
    *,
    operation: str,
    result: str,
    code: str,
    message: str,
    version_uuid: str | None = None,
    media_uuid: str | None = None,
    details: dict[str, Any] | None = None,
) -> OperationResult:
    return OperationResult(
        success=False,
        operation=operation,
        result=result,
        entity_type="library_row" if version_uuid else None,
        entity_uuid=version_uuid,
        media_uuid=media_uuid,
        version_uuid=version_uuid,
        errors=[
            KoaMessage(
                code=code,
                severity="blocking",
                message=message,
                details=details or {},
            )
        ],
    )


# Minimal RFC 8785 JCS implementation, aligned with the supplied IK runtime.
def _validate_jcs_string(value: str) -> None:
    for char in value:
        if 0xD800 <= ord(char) <= 0xDFFF:
            raise KristalBridgeError("lone surrogate is not valid I-JSON")


def _jcs_string(value: str) -> str:
    _validate_jcs_string(value)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _utf16_sort_key(value: str) -> bytes:
    _validate_jcs_string(value)
    return value.encode("utf-16-be")


def _jcs_number(value: int | float) -> str:
    if isinstance(value, bool):
        raise KristalBridgeError("boolean is not a number")
    if isinstance(value, int):
        if abs(value) > _MAX_IJSON_INTEGER:
            raise KristalBridgeError("integer is outside the interoperable I-JSON range")
        return str(value)
    if not math.isfinite(value):
        raise KristalBridgeError("non-finite number is not valid I-JSON")
    if value == 0.0:
        return "0"

    negative = value < 0
    number = -value if negative else value
    raw = repr(number).lower()
    if "e" in raw:
        mantissa, exponent_text = raw.split("e", 1)
        exponent = int(exponent_text)
    else:
        mantissa, exponent = raw, 0

    if "." in mantissa:
        before, after = mantissa.split(".", 1)
        digits = before + after
        decimal_pos = len(before) + exponent
    else:
        digits = mantissa
        decimal_pos = len(mantissa) + exponent

    while len(digits) > 1 and digits[0] == "0":
        digits = digits[1:]
        decimal_pos -= 1
    while len(digits) > 1 and digits[-1] == "0":
        digits = digits[:-1]

    scientific_exponent = decimal_pos - 1
    if 1e-6 <= number < 1e21:
        if decimal_pos <= 0:
            rendered = "0." + ("0" * (-decimal_pos)) + digits
        elif decimal_pos >= len(digits):
            rendered = digits + ("0" * (decimal_pos - len(digits)))
        else:
            rendered = digits[:decimal_pos] + "." + digits[decimal_pos:]
    else:
        rendered_mantissa = digits if len(digits) == 1 else digits[0] + "." + digits[1:]
        sign = "+" if scientific_exponent >= 0 else ""
        rendered = f"{rendered_mantissa}e{sign}{scientific_exponent}"
    return "-" + rendered if negative else rendered


def _jcs_canonicalize(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return _jcs_string(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _jcs_number(value)
    if isinstance(value, list):
        return "[" + ",".join(_jcs_canonicalize(item) for item in value) + "]"
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise KristalBridgeError("JSON object keys must be strings")
        keys = sorted(value, key=_utf16_sort_key)
        return "{" + ",".join(
            _jcs_string(key) + ":" + _jcs_canonicalize(value[key]) for key in keys
        ) + "}"
    raise KristalBridgeError(f"unsupported JSON value type: {type(value).__name__}")
