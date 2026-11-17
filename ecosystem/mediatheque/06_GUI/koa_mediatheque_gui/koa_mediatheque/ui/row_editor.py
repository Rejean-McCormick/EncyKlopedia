# 06_GUI/koa_mediatheque_gui/koa_mediatheque/ui/row_editor.py
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any
from koa_mediatheque.workspace import resolve_content_path


SS_DB_PATH = "koa_db_path"
SS_LAST_OPERATION_RESULT = "koa_last_operation_result"
SS_SELECTED_VERSION_UUID = "koa_selected_version_uuid"
SS_SELECTED_MEDIA_UUID = "koa_selected_media_uuid"
SS_SELECTED_FILE_PATH = "koa_selected_file_path"

PROTECTED_FIELDS = [
    "id",
    "media_uuid",
    "version_uuid",
    "original_path",
    "storage_path",
    "filename",
    "extension",
    "mimetype",
    "filesize",
    "sha256",
    "created_at",
    "updated_at",
]

TEXTAREA_FIELDS = {
    "description",
    "summary",
    "rights_note",
    "restriction_reason",
    "review_reason",
    "export_policy_note",
    "notes",
    "collections_json",
    "tags_json",
    "relations_json",
    "content_flags_json",
}

INTEGER_FIELDS = {
    "target_export_allowed",
    "redaction_required",
    "human_review_required",
}

FLOAT_FIELDS = {
    "ai_confidence",
}

FALLBACK_ALLOWED_VALUES: dict[str, list[Any]] = {
    "filearea": [
        "media_original",
        "media_preview",
        "media_thumbnail",
        "media_derivative",
        "media_caption",
        "media_transcript",
        "media_attachment",
        "content_review_files",
        "external_work_reference_files",
        "cultural_protocol_files",
    ],
    "media_type": [
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
    ],
    "library_scope": ["koa"],
    "uckk_relevance": [
        "uckk_core",
        "uckk_related",
        "uckk_reference",
        "not_uckk",
        "unknown",
    ],
    "target_system": ["none", "uckkarchive", "other"],
    "target_export_allowed": [0, 1],
    "public_state": [
        "public",
        "non_public",
        "private",
        "restricted",
        "confidential",
        "unknown",
    ],
    "visibility": [
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
    ],
    "access_level": [
        "private",
        "limited",
        "internal",
        "public",
        "restricted",
        "confidential",
        "unknown",
    ],
    "ownership_scope": [
        "uckk_owned",
        "koa_owned",
        "personal",
        "third_party",
        "public_domain",
        "open_license",
        "unknown",
    ],
    "source_type": [
        "produced_by_uckk",
        "submitted_to_uckk",
        "imported",
        "external_reference_only",
        "licensed_external",
        "public_domain",
        "fair_use_reference",
        "restricted_reference",
        "unknown",
    ],
    "source_ownership": [
        "uckk_created",
        "uckk_commissioned",
        "member_submitted",
        "partner_submitted",
        "external_reference",
        "third_party_copyright",
        "public_domain",
        "open_license",
        "unknown_source",
    ],
    "rights_status": [
        "owned",
        "licensed",
        "open_license",
        "public_domain",
        "fair_use_reference",
        "third_party",
        "unknown",
    ],
    "restriction_state": [
        "none",
        "possible",
        "restricted",
        "confidential",
        "cultural",
        "integrity",
        "privacy",
        "copyright",
        "unknown",
    ],
    "redaction_required": [0, 1],
    "status": [
        "draft",
        "submitted",
        "active",
        "restricted",
        "superseded",
        "archived",
        "deleted_soft",
    ],
    "provenance": [
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
    ],
    "ai_validation_state": [
        "ai_validated",
        "ai_classified_needs_review",
        "ai_uncertain",
        "ai_rejected",
    ],
    "canonical_validation_state": [
        "unverified",
        "human_reviewed",
        "verified",
        "contested",
        "invalidated",
        "archived",
    ],
    "human_review_required": [0, 1],
    "audience_suitability": [
        "general",
        "guided",
        "mature",
        "restricted",
        "restricted_cultural",
        "restricted_integrity",
        "staff_only",
        "unknown",
    ],
    "export_to_uckk": ["yes", "no", "maybe", "review_required"],
    "export_to_public": ["yes", "no", "maybe", "review_required"],
}


FIELD_GROUPS: dict[str, list[str]] = {
    "Description": [
        "title",
        "subtitle",
        "description",
        "summary",
        "media_type",
        "language",
        "status",
    ],
    "Classification kOA / UCKK": [
        "library_scope",
        "uckk_relevance",
        "target_system",
        "target_export_allowed",
        "export_to_uckk",
    ],
    "Accès public / visibilité": [
        "public_state",
        "visibility",
        "access_level",
        "export_to_public",
    ],
    "Source et droits": [
        "ownership_scope",
        "source_type",
        "source_ownership",
        "rights_status",
        "rights_note",
    ],
    "Restrictions et revue": [
        "restriction_state",
        "restriction_reason",
        "redaction_required",
        "audience_suitability",
        "human_review_required",
        "review_queue",
        "review_reason",
    ],
    "Validation": [
        "provenance",
        "ai_validation_state",
        "ai_confidence",
        "canonical_validation_state",
    ],
    "Collections / tags / relations": [
        "collections_json",
        "tags_json",
        "relations_json",
        "content_flags_json",
    ],
    "Import / notes": [
        "filearea",
        "import_batch",
        "export_policy_note",
        "notes",
    ],
}


def _st():
    import streamlit as st

    return st


def _safe_container(*, border: bool = False):
    st = _st()

    try:
        return st.container(border=border)
    except TypeError:
        return st.container()


def _to_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}

    if isinstance(value, dict):
        return dict(value)

    if is_dataclass(value):
        return asdict(value)

    if hasattr(value, "data") and isinstance(value.data, dict):
        return dict(value.data)

    try:
        return dict(value)
    except Exception:
        return {}


def _load_allowed_values() -> dict[str, list[Any]]:
    allowed = dict(FALLBACK_ALLOWED_VALUES)

    try:
        from koa_mediatheque import constants

        constant_map = {
            "filearea": "STORAGE_FILEAREA_VALUES",
            "media_type": "MEDIA_TYPE_VALUES",
            "library_scope": "LIBRARY_SCOPE_VALUES",
            "uckk_relevance": "UCKK_RELEVANCE_VALUES",
            "target_system": "TARGET_SYSTEM_VALUES",
            "target_export_allowed": "TARGET_EXPORT_ALLOWED_VALUES",
            "public_state": "PUBLIC_STATE_VALUES",
            "visibility": "VISIBILITY_VALUES",
            "access_level": "ACCESS_LEVEL_VALUES",
            "ownership_scope": "OWNERSHIP_SCOPE_VALUES",
            "source_type": "SOURCE_TYPE_VALUES",
            "source_ownership": "SOURCE_OWNERSHIP_VALUES",
            "rights_status": "RIGHTS_STATUS_VALUES",
            "restriction_state": "RESTRICTION_STATE_VALUES",
            "redaction_required": "BOOLEAN_INT_VALUES",
            "status": "MEDIA_STATUS_VALUES",
            "provenance": "PROVENANCE_VALUES",
            "ai_validation_state": "LOCAL_AI_VALIDATION_VALUES",
            "canonical_validation_state": "CANONICAL_VALIDATION_VALUES",
            "human_review_required": "BOOLEAN_INT_VALUES",
            "audience_suitability": "AUDIENCE_SUITABILITY_VALUES",
            "export_to_uckk": "EXPORT_DECISION_VALUES",
            "export_to_public": "EXPORT_DECISION_VALUES",
        }

        for field_name, constant_name in constant_map.items():
            if hasattr(constants, constant_name):
                raw_value = getattr(constants, constant_name)

                if isinstance(raw_value, str):
                    values = [item.strip() for item in raw_value.split(",") if item.strip()]
                else:
                    values = list(raw_value)

                if values:
                    allowed[field_name] = values
    except Exception:
        pass

    try:
        from koa_mediatheque.validation import allowed_values as validation_allowed_values

        for field_name in list(allowed):
            constant_name = f"{field_name.upper()}_VALUES"
            if hasattr(validation_allowed_values, constant_name):
                values = list(getattr(validation_allowed_values, constant_name))
                if values:
                    allowed[field_name] = values
    except Exception:
        pass

    return allowed


def _normalize_for_compare(value: Any) -> Any:
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    return value


def _coerce_int(value: Any) -> int | None:
    if value is None or value == "":
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_float(value: Any) -> float | None:
    if value is None or value == "":
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _json_text_to_semicolon(value: Any) -> str:
    if value is None or value == "":
        return ""

    if isinstance(value, list):
        return "; ".join(str(item) for item in value)

    if not isinstance(value, str):
        return str(value)

    text = value.strip()

    if not text:
        return ""

    try:
        decoded = json.loads(text)
    except json.JSONDecodeError:
        return text

    if isinstance(decoded, list):
        rendered_items: list[str] = []
        for item in decoded:
            if isinstance(item, str):
                rendered_items.append(item)
            else:
                rendered_items.append(json.dumps(item, ensure_ascii=False, sort_keys=True))
        return "; ".join(rendered_items)

    return text


def _semicolon_to_json_text(value: str) -> str:
    text = str(value or "").strip()

    if not text:
        return "[]"

    if text.startswith("["):
        try:
            decoded = json.loads(text)
            if isinstance(decoded, list):
                return json.dumps(decoded, ensure_ascii=False, sort_keys=True)
        except json.JSONDecodeError:
            pass

    items = [item.strip() for item in text.split(";") if item.strip()]
    return json.dumps(items, ensure_ascii=False, sort_keys=True)


def _field_value(row: dict[str, Any], field_name: str) -> Any:
    return row.get(field_name)


def _render_readonly_field(row: dict[str, Any], field_name: str) -> None:
    st = _st()

    value = _field_value(row, field_name)

    if value is None:
        value = ""

    st.text_input(
        field_name,
        value=str(value),
        disabled=True,
        key=f"koa_row_readonly_{field_name}",
    )


def _render_select_field(
    row: dict[str, Any],
    field_name: str,
    allowed_values: list[Any],
) -> Any:
    st = _st()

    current_value = _field_value(row, field_name)

    normalized_options = list(allowed_values)
    if current_value not in normalized_options and current_value not in (None, ""):
        normalized_options = [current_value, *normalized_options]

    if current_value in normalized_options:
        index = normalized_options.index(current_value)
    elif str(current_value) in [str(item) for item in normalized_options]:
        index = [str(item) for item in normalized_options].index(str(current_value))
    else:
        index = 0

    return st.selectbox(
        field_name,
        options=normalized_options,
        index=index,
        format_func=lambda value: str(value),
        key=f"koa_row_edit_{field_name}",
    )


def _render_text_field(row: dict[str, Any], field_name: str) -> str:
    st = _st()

    value = _field_value(row, field_name)
    rendered_value = "" if value is None else str(value)

    if field_name in TEXTAREA_FIELDS:
        if field_name.endswith("_json"):
            rendered_value = _json_text_to_semicolon(rendered_value)

            return st.text_area(
                field_name,
                value=rendered_value,
                height=120,
                key=f"koa_row_edit_{field_name}",
                help="Valeurs séparées par des points-virgules. Sauvegardé en JSON texte.",
            )

        return st.text_area(
            field_name,
            value=rendered_value,
            height=140,
            key=f"koa_row_edit_{field_name}",
        )

    return st.text_input(
        field_name,
        value=rendered_value,
        key=f"koa_row_edit_{field_name}",
    )


def _render_number_field(row: dict[str, Any], field_name: str) -> Any:
    st = _st()

    value = _field_value(row, field_name)

    if field_name in INTEGER_FIELDS:
        int_value = _coerce_int(value)
        return st.number_input(
            field_name,
            value=int_value if int_value is not None else 0,
            step=1,
            key=f"koa_row_edit_{field_name}",
        )

    float_value = _coerce_float(value)
    return st.number_input(
        field_name,
        value=float_value if float_value is not None else 0.0,
        step=0.01,
        key=f"koa_row_edit_{field_name}",
    )


def _render_field(
    row: dict[str, Any],
    field_name: str,
    allowed_values: dict[str, list[Any]],
) -> Any:
    if field_name in PROTECTED_FIELDS:
        _render_readonly_field(row, field_name)
        return _field_value(row, field_name)

    if field_name in allowed_values:
        return _render_select_field(row, field_name, allowed_values[field_name])

    if field_name in INTEGER_FIELDS or field_name in FLOAT_FIELDS:
        return _render_number_field(row, field_name)

    return _render_text_field(row, field_name)


def _normalize_new_value(field_name: str, value: Any) -> Any:
    if field_name in INTEGER_FIELDS:
        return _coerce_int(value)

    if field_name in FLOAT_FIELDS:
        return _coerce_float(value)

    if field_name.endswith("_json"):
        return _semicolon_to_json_text(str(value or ""))

    if isinstance(value, str):
        return value.strip()

    return value


def _build_updates(row: dict[str, Any], edited_values: dict[str, Any]) -> dict[str, Any]:
    updates: dict[str, Any] = {}

    for field_name, edited_value in edited_values.items():
        if field_name in PROTECTED_FIELDS:
            continue

        new_value = _normalize_new_value(field_name, edited_value)
        old_value = row.get(field_name)

        if _normalize_for_compare(new_value) != _normalize_for_compare(old_value):
            updates[field_name] = new_value

    return updates


def _get_connection_from_session() -> Any:
    st = _st()

    db_path = st.session_state.get(SS_DB_PATH)

    if not db_path:
        return None

    try:
        from koa_mediatheque.db import get_db_connection

        return get_db_connection(Path(str(db_path)).expanduser())
    except Exception as exc:
        st.error(f"Connexion SQLite impossible : {exc}")
        return None


def _render_updates_preview(updates: dict[str, Any]) -> None:
    st = _st()

    if not updates:
        st.info("Aucune modification détectée.")
        return

    st.write(f"{len(updates)} modification(s) détectée(s).")

    with st.expander("Prévisualiser les modifications", expanded=False):
        st.json(updates)


def _store_selection_from_row(row: dict[str, Any]) -> None:
    st = _st()

    if row.get("version_uuid"):
        st.session_state[SS_SELECTED_VERSION_UUID] = row.get("version_uuid")

    if row.get("media_uuid"):
        st.session_state[SS_SELECTED_MEDIA_UUID] = row.get("media_uuid")

    if row.get("storage_path") or row.get("original_path"):
        raw_path = row.get("storage_path") or row.get("original_path")
        st.session_state[SS_SELECTED_FILE_PATH] = str(resolve_content_path(str(raw_path)))


def render_row_editor(row: dict[str, Any]) -> dict[str, Any]:
    st = _st()

    row_data = _to_dict(row)

    if not row_data:
        st.info("Aucune ligne sélectionnée.")
        return {}

    _store_selection_from_row(row_data)

    allowed_values = _load_allowed_values()
    edited_values: dict[str, Any] = {}

    with _safe_container(border=True):
        title = row_data.get("title") or row_data.get("filename") or "Ligne sélectionnée"
        st.subheader(str(title))

        col_id, col_media, col_version = st.columns(3)

        with col_id:
            _render_readonly_field(row_data, "id")
        with col_media:
            _render_readonly_field(row_data, "media_uuid")
        with col_version:
            _render_readonly_field(row_data, "version_uuid")

        with st.expander("Faits fichier protégés", expanded=False):
            protected_display_fields = [
                "original_path",
                "storage_path",
                "filename",
                "extension",
                "mimetype",
                "filesize",
                "sha256",
                "created_at",
                "updated_at",
            ]

            for field_name in protected_display_fields:
                if field_name in row_data:
                    _render_readonly_field(row_data, field_name)

        for group_name, fields in FIELD_GROUPS.items():
            with st.expander(group_name, expanded=group_name == "Description"):
                for field_name in fields:
                    if field_name not in row_data and field_name not in FALLBACK_ALLOWED_VALUES:
                        continue

                    edited_values[field_name] = _render_field(
                        row_data,
                        field_name,
                        allowed_values,
                    )

        unknown_editable_fields = [
            field_name
            for field_name in row_data
            if field_name not in PROTECTED_FIELDS
            and all(field_name not in fields for fields in FIELD_GROUPS.values())
        ]

        if unknown_editable_fields:
            with st.expander("Autres champs", expanded=False):
                for field_name in unknown_editable_fields:
                    edited_values[field_name] = _render_field(
                        row_data,
                        field_name,
                        allowed_values,
                    )

    updates = _build_updates(row_data, edited_values)
    _render_updates_preview(updates)

    return updates


def render_row_save_button(row: dict[str, Any], updates: dict[str, Any]) -> None:
    st = _st()

    row_data = _to_dict(row)

    if not row_data:
        st.info("Aucune ligne à sauvegarder.")
        return

    version_uuid = row_data.get("version_uuid")

    if not version_uuid:
        st.error("Sauvegarde impossible : `version_uuid` manquant.")
        return

    if not updates:
        st.button("Sauvegarder", disabled=True, use_container_width=True)
        return

    col_save, col_reset = st.columns([2, 1])

    with col_save:
        if st.button("Sauvegarder", type="primary", use_container_width=True):
            connection = _get_connection_from_session()

            if connection is None:
                st.error("Sauvegarde impossible : connexion SQLite indisponible.")
                return

            try:
                from koa_mediatheque.repositories.library_rows_repository import (
                    update_library_row_by_version_uuid,
                )

                result = update_library_row_by_version_uuid(
                    connection,
                    str(version_uuid),
                    updates,
                    actor="local_user",
                )

                try:
                    connection.commit()
                except Exception:
                    pass

                st.session_state[SS_LAST_OPERATION_RESULT] = result

                success = bool(getattr(result, "success", False))
                result_text = str(getattr(result, "result", ""))

                if success:
                    st.success(result_text or "Ligne sauvegardée.")
                    st.rerun()
                else:
                    st.error(result_text or "Sauvegarde échouée.")

            except Exception as exc:
                st.error(f"Sauvegarde échouée : {exc}")
            finally:
                try:
                    connection.close()
                except Exception:
                    pass

    with col_reset:
        if st.button("Annuler", use_container_width=True):
            st.rerun()

