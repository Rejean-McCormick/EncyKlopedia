# 06_GUI/koa_mediatheque_gui/koa_mediatheque/ui/validation_panel.py
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any


MAX_CHANGE_ROWS_RENDERED = 500


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

    data: dict[str, Any] = {}

    for key in (
        "is_valid",
        "is_blocked",
        "normalized_data",
        "warnings",
        "errors",
        "import_uuid",
        "source_path",
        "rows_total",
        "rows_update",
        "rows_new",
        "rows_archive",
        "rows_ignore",
        "rows_blocked",
        "changes",
    ):
        if hasattr(value, key):
            data[key] = getattr(value, key)

    return data


def _message_to_dict(message: Any) -> dict[str, Any]:
    if message is None:
        return {}

    if isinstance(message, dict):
        return dict(message)

    if is_dataclass(message):
        return asdict(message)

    return {
        "code": getattr(message, "code", ""),
        "severity": getattr(message, "severity", ""),
        "message": getattr(message, "message", str(message)),
        "field": getattr(message, "field", None),
        "row_number": getattr(message, "row_number", None),
        "details": getattr(message, "details", {}),
    }


def _normalize_messages(messages: Any) -> list[dict[str, Any]]:
    if not messages:
        return []

    if not isinstance(messages, list):
        messages = [messages]

    return [_message_to_dict(message) for message in messages]


def _render_message(message: dict[str, Any], *, default_severity: str = "info") -> None:
    st = _st()

    code = str(message.get("code") or "")
    severity = str(message.get("severity") or default_severity).lower()
    text = str(message.get("message") or code or "Message")
    field = message.get("field")
    row_number = message.get("row_number")
    details = message.get("details") or {}

    suffix_parts: list[str] = []

    if code:
        suffix_parts.append(f"`{code}`")
    if field:
        suffix_parts.append(f"champ `{field}`")
    if row_number is not None:
        suffix_parts.append(f"ligne `{row_number}`")

    suffix = f" — {' · '.join(suffix_parts)}" if suffix_parts else ""
    rendered_text = f"{text}{suffix}"

    if severity in {"error", "blocking"}:
        st.error(rendered_text)
    elif severity == "warning":
        st.warning(rendered_text)
    elif severity == "success":
        st.success(rendered_text)
    else:
        st.info(rendered_text)

    if details:
        with st.expander("Détails", expanded=False):
            st.json(details)


def _render_messages(
    title: str,
    messages: list[dict[str, Any]],
    *,
    default_severity: str,
) -> None:
    st = _st()

    if not messages:
        return

    with st.expander(f"{title} ({len(messages)})", expanded=default_severity in {"error", "blocking"}):
        for message in messages:
            _render_message(message, default_severity=default_severity)


def _safe_json(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, str):
        text = value.strip()

        if not text:
            return ""

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return value

    return value


def _flatten_change(change: dict[str, Any]) -> dict[str, Any]:
    flattened: dict[str, Any] = {}

    preferred_keys = [
        "row_number",
        "action",
        "status",
        "version_uuid",
        "media_uuid",
        "title",
        "filename",
        "field",
        "old_value",
        "new_value",
        "message",
        "blocked",
    ]

    for key in preferred_keys:
        if key in change:
            flattened[key] = change[key]

    for key, value in change.items():
        if key in flattened:
            continue

        if isinstance(value, (dict, list)):
            flattened[key] = json.dumps(value, ensure_ascii=False, sort_keys=True)
        else:
            flattened[key] = value

    return flattened


def _changes_to_rows(changes: Any) -> list[dict[str, Any]]:
    if not changes:
        return []

    if not isinstance(changes, list):
        changes = [changes]

    rows: list[dict[str, Any]] = []

    for change in changes:
        if isinstance(change, dict):
            rows.append(_flatten_change(change))
        elif is_dataclass(change):
            rows.append(_flatten_change(asdict(change)))
        else:
            rows.append({"change": str(change)})

    return rows


def _render_changes_summary(changes: list[dict[str, Any]]) -> None:
    st = _st()

    if not changes:
        return

    action_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}

    for change in changes:
        action = str(change.get("action") or "unknown")
        status = str(change.get("status") or "unknown")

        action_counts[action] = action_counts.get(action, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1

    col_action, col_status = st.columns(2)

    with col_action:
        st.caption("Actions")
        st.dataframe(
            [{"action": key, "count": value} for key, value in sorted(action_counts.items())],
            use_container_width=True,
            hide_index=True,
        )

    with col_status:
        st.caption("Statuts")
        st.dataframe(
            [{"status": key, "count": value} for key, value in sorted(status_counts.items())],
            use_container_width=True,
            hide_index=True,
        )


def render_validation_result(validation: Any) -> None:
    st = _st()

    if validation is None:
        st.info("Aucun résultat de validation.")
        return

    data = _to_dict(validation)

    is_valid = bool(data.get("is_valid"))
    is_blocked = bool(data.get("is_blocked"))
    normalized_data = data.get("normalized_data") or {}
    warnings = _normalize_messages(data.get("warnings"))
    errors = _normalize_messages(data.get("errors"))

    with _safe_container(border=True):
        st.subheader("Résultat de validation")

        col_status, col_errors, col_warnings = st.columns(3)

        with col_status:
            if is_blocked:
                st.metric("Statut", "Bloqué")
            elif is_valid:
                st.metric("Statut", "Valide")
            else:
                st.metric("Statut", "Invalide")

        with col_errors:
            st.metric("Erreurs", len(errors))

        with col_warnings:
            st.metric("Warnings", len(warnings))

        if is_blocked:
            st.error("Validation bloquée. Intégration interdite.")
        elif is_valid:
            st.success("Validation réussie.")
        else:
            st.warning("Validation non valide ou incomplète.")

        _render_messages("Erreurs", errors, default_severity="error")
        _render_messages("Warnings", warnings, default_severity="warning")

        if normalized_data:
            with st.expander("Données normalisées", expanded=False):
                st.json(_safe_json(normalized_data))


def render_import_preview(preview: Any) -> None:
    st = _st()

    if preview is None:
        st.info("Aucune prévisualisation d’import.")
        return

    data = _to_dict(preview)

    import_uuid = str(data.get("import_uuid") or "")
    source_path = str(data.get("source_path") or "")
    rows_total = int(data.get("rows_total") or 0)
    rows_update = int(data.get("rows_update") or 0)
    rows_new = int(data.get("rows_new") or 0)
    rows_archive = int(data.get("rows_archive") or 0)
    rows_ignore = int(data.get("rows_ignore") or 0)
    rows_blocked = int(data.get("rows_blocked") or 0)

    warnings = _normalize_messages(data.get("warnings"))
    errors = _normalize_messages(data.get("errors"))
    changes = _changes_to_rows(data.get("changes"))

    with _safe_container(border=True):
        st.subheader("Prévisualisation d’import XLSX")

        if rows_blocked > 0 or errors:
            st.error("Import bloqué ou partiellement bloqué.")
        elif rows_total == 0:
            st.warning("Aucune ligne détectée.")
        else:
            st.success("Prévisualisation générée.")

        col_total, col_update, col_new, col_archive, col_ignore, col_blocked = st.columns(6)

        col_total.metric("Total", rows_total)
        col_update.metric("Update", rows_update)
        col_new.metric("New", rows_new)
        col_archive.metric("Archive", rows_archive)
        col_ignore.metric("Ignore", rows_ignore)
        col_blocked.metric("Bloquées", rows_blocked)

        meta_parts = []

        if import_uuid:
            meta_parts.append(f"import_uuid `{import_uuid}`")
        if source_path:
            meta_parts.append(f"source `{source_path}`")

        if meta_parts:
            st.caption(" · ".join(meta_parts))

        _render_messages("Erreurs", errors, default_severity="error")
        _render_messages("Warnings", warnings, default_severity="warning")

        if changes:
            st.divider()
            st.write(f"{len(changes)} changement(s) détecté(s).")

            _render_changes_summary(changes)

            rendered_changes = changes[:MAX_CHANGE_ROWS_RENDERED]

            if len(changes) > MAX_CHANGE_ROWS_RENDERED:
                st.warning(
                    f"Affichage limité aux {MAX_CHANGE_ROWS_RENDERED} premiers changements."
                )

            st.dataframe(
                rendered_changes,
                use_container_width=True,
                hide_index=True,
            )

            with st.expander("Changements bruts", expanded=False):
                st.json(changes)
        else:
            st.info("Aucun changement détecté.")