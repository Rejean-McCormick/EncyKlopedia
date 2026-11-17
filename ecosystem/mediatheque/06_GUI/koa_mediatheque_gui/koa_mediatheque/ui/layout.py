# 06_GUI/koa_mediatheque_gui/koa_mediatheque/ui/layout.py
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from koa_mediatheque.workspace import get_workspace_paths


APP_PUBLIC_NAME = "Médiathèque kOA"
APP_SHORT_NAME = "kOA"
APP_TECHNICAL_NAME = "koa-mediatheque"
APP_COMPONENT = "koa_mediatheque"
APP_DB_FILENAME = "koa_mediatheque.sqlite"

SS_DB_PATH = "koa_db_path"
SS_STORAGE_ROOT = "koa_storage_root"
SS_IMPORTS_ROOT = "koa_imports_root"
SS_EXPORTS_ROOT = "koa_exports_root"
SS_BACKUP_ROOT = "koa_backup_root"
SS_SELECTED_VERSION_UUID = "koa_selected_version_uuid"
SS_SELECTED_MEDIA_UUID = "koa_selected_media_uuid"
SS_SELECTED_FILE_PATH = "koa_selected_file_path"
SS_CURRENT_FILTERS = "koa_current_filters"
SS_CHATGPT_RAW_RESPONSE = "koa_chatgpt_raw_response"
SS_CHATGPT_VALIDATION_RESULT = "koa_chatgpt_validation_result"
SS_CHATGPT_PREVIEW_ROW = "koa_chatgpt_preview_row"
SS_XLSX_IMPORT_PREVIEW = "koa_xlsx_import_preview"
SS_LAST_OPERATION_RESULT = "koa_last_operation_result"

WIDGET_DB_PATH = "koa_sidebar_db_path"
WIDGET_STORAGE_ROOT = "koa_sidebar_storage_root"
WIDGET_IMPORTS_ROOT = "koa_sidebar_imports_root"
WIDGET_EXPORTS_ROOT = "koa_sidebar_exports_root"
WIDGET_BACKUP_ROOT = "koa_sidebar_backup_root"


def _st():
    import streamlit as st

    return st


def _project_root() -> Path:
    return get_workspace_paths().app_root


def _default_paths() -> dict[str, str]:
    paths = get_workspace_paths()
    return {
        SS_DB_PATH: str(paths.db_path),
        SS_STORAGE_ROOT: str(paths.storage_root),
        SS_IMPORTS_ROOT: str(paths.imports_root),
        SS_EXPORTS_ROOT: str(paths.exports_root),
        SS_BACKUP_ROOT: str(paths.backups_root),
    }


def _normalize_path_text(value: Any) -> str:
    return str(value or "").strip()


def _ensure_session_defaults() -> None:
    st = _st()

    defaults: dict[str, Any] = {
        **_default_paths(),
        SS_SELECTED_VERSION_UUID: None,
        SS_SELECTED_MEDIA_UUID: None,
        SS_SELECTED_FILE_PATH: None,
        SS_CURRENT_FILTERS: {},
        SS_CHATGPT_RAW_RESPONSE: "",
        SS_CHATGPT_VALIDATION_RESULT: None,
        SS_CHATGPT_PREVIEW_ROW: None,
        SS_XLSX_IMPORT_PREVIEW: None,
        SS_LAST_OPERATION_RESULT: None,
    }

    for key, value in defaults.items():
        current_value = st.session_state.get(key)

        if current_value is None:
            st.session_state[key] = value
            continue

        if isinstance(current_value, str) and current_value.strip() == "":
            st.session_state[key] = value


def _ensure_sidebar_widget_defaults() -> None:
    st = _st()
    defaults = _default_paths()

    widget_defaults = {
        WIDGET_DB_PATH: st.session_state.get(SS_DB_PATH) or defaults[SS_DB_PATH],
        WIDGET_STORAGE_ROOT: st.session_state.get(SS_STORAGE_ROOT) or defaults[SS_STORAGE_ROOT],
        WIDGET_IMPORTS_ROOT: st.session_state.get(SS_IMPORTS_ROOT) or defaults[SS_IMPORTS_ROOT],
        WIDGET_EXPORTS_ROOT: st.session_state.get(SS_EXPORTS_ROOT) or defaults[SS_EXPORTS_ROOT],
        WIDGET_BACKUP_ROOT: st.session_state.get(SS_BACKUP_ROOT) or defaults[SS_BACKUP_ROOT],
    }

    for key, value in widget_defaults.items():
        current_value = st.session_state.get(key)

        if current_value is None:
            st.session_state[key] = str(value)
            continue

        if isinstance(current_value, str) and current_value.strip() == "":
            st.session_state[key] = str(value)


def _sync_sidebar_paths_to_session() -> None:
    st = _st()

    pairs = {
        SS_DB_PATH: WIDGET_DB_PATH,
        SS_STORAGE_ROOT: WIDGET_STORAGE_ROOT,
        SS_IMPORTS_ROOT: WIDGET_IMPORTS_ROOT,
        SS_EXPORTS_ROOT: WIDGET_EXPORTS_ROOT,
        SS_BACKUP_ROOT: WIDGET_BACKUP_ROOT,
    }

    for session_key, widget_key in pairs.items():
        value = _normalize_path_text(st.session_state.get(widget_key))

        if value:
            st.session_state[session_key] = value


def _to_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}

    if isinstance(value, dict):
        return value

    if is_dataclass(value):
        return asdict(value)

    data: dict[str, Any] = {}
    for key in (
        "success",
        "operation",
        "result",
        "entity_type",
        "entity_uuid",
        "media_uuid",
        "version_uuid",
        "path",
        "data",
        "warnings",
        "errors",
    ):
        if hasattr(value, key):
            data[key] = getattr(value, key)

    return data


def _message_to_dict(message: Any) -> dict[str, Any]:
    if isinstance(message, dict):
        return message

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


def _render_messages(messages: list[Any], *, kind: str) -> None:
    st = _st()

    if not messages:
        return

    for raw_message in messages:
        message = _message_to_dict(raw_message)
        text = str(message.get("message") or message.get("code") or raw_message)
        code = str(message.get("code") or "")
        field = message.get("field")
        row_number = message.get("row_number")

        suffix_parts = []
        if code:
            suffix_parts.append(f"`{code}`")
        if field:
            suffix_parts.append(f"champ `{field}`")
        if row_number is not None:
            suffix_parts.append(f"ligne `{row_number}`")

        suffix = f" — {' · '.join(suffix_parts)}" if suffix_parts else ""

        if kind == "error":
            st.error(f"{text}{suffix}")
        elif kind == "warning":
            st.warning(f"{text}{suffix}")
        else:
            st.info(f"{text}{suffix}")


def configure_page() -> None:
    st = _st()

    st.set_page_config(
        page_title=APP_PUBLIC_NAME,
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "About": (
                f"{APP_PUBLIC_NAME} — {APP_TECHNICAL_NAME}. "
                "Catalogue local SQLite, stockage local, intake ChatGPT et round-trip XLSX."
            )
        },
    )

    _ensure_session_defaults()


def render_sidebar_settings() -> dict[str, Any]:
    st = _st()
    _ensure_session_defaults()
    _ensure_sidebar_widget_defaults()

    with st.sidebar:
        st.title(APP_SHORT_NAME)
        st.caption(APP_TECHNICAL_NAME)

        st.divider()

        st.text_input(
            "Base SQLite",
            key=WIDGET_DB_PATH,
            on_change=_sync_sidebar_paths_to_session,
            help="Chemin vers 01_DB/koa_mediatheque.sqlite.",
        )

        st.text_input(
            "Stockage local",
            key=WIDGET_STORAGE_ROOT,
            on_change=_sync_sidebar_paths_to_session,
            help="Chemin vers 02_STORAGE.",
        )

        st.text_input(
            "Imports",
            key=WIDGET_IMPORTS_ROOT,
            on_change=_sync_sidebar_paths_to_session,
            help="Chemin vers 03_IMPORTS.",
        )

        st.text_input(
            "Exports",
            key=WIDGET_EXPORTS_ROOT,
            on_change=_sync_sidebar_paths_to_session,
            help="Chemin vers 04_EXPORTS.",
        )

        st.text_input(
            "Backups",
            key=WIDGET_BACKUP_ROOT,
            on_change=_sync_sidebar_paths_to_session,
            help="Chemin vers 07_BACKUPS.",
        )

        st.divider()

        selected_version_uuid = st.session_state.get(SS_SELECTED_VERSION_UUID)
        selected_media_uuid = st.session_state.get(SS_SELECTED_MEDIA_UUID)
        selected_file_path = st.session_state.get(SS_SELECTED_FILE_PATH)

        st.caption("Sélection courante")
        st.text_input(
            "version_uuid",
            value=selected_version_uuid or "",
            disabled=True,
        )
        st.text_input(
            "media_uuid",
            value=selected_media_uuid or "",
            disabled=True,
        )
        st.text_input(
            "Fichier",
            value=selected_file_path or "",
            disabled=True,
        )

        st.divider()

        if st.button("Réinitialiser la sélection", use_container_width=True):
            st.session_state[SS_SELECTED_VERSION_UUID] = None
            st.session_state[SS_SELECTED_MEDIA_UUID] = None
            st.session_state[SS_SELECTED_FILE_PATH] = None
            st.rerun()

    db_path = _normalize_path_text(st.session_state.get(WIDGET_DB_PATH))
    storage_root = _normalize_path_text(st.session_state.get(WIDGET_STORAGE_ROOT))
    imports_root = _normalize_path_text(st.session_state.get(WIDGET_IMPORTS_ROOT))
    exports_root = _normalize_path_text(st.session_state.get(WIDGET_EXPORTS_ROOT))
    backup_root = _normalize_path_text(st.session_state.get(WIDGET_BACKUP_ROOT))

    return {
        "db_path": db_path,
        "storage_root": storage_root,
        "imports_root": imports_root,
        "exports_root": exports_root,
        "backup_root": backup_root,
        SS_DB_PATH: db_path,
        SS_STORAGE_ROOT: storage_root,
        SS_IMPORTS_ROOT: imports_root,
        SS_EXPORTS_ROOT: exports_root,
        SS_BACKUP_ROOT: backup_root,
        SS_SELECTED_VERSION_UUID: st.session_state.get(SS_SELECTED_VERSION_UUID),
        SS_SELECTED_MEDIA_UUID: st.session_state.get(SS_SELECTED_MEDIA_UUID),
        SS_SELECTED_FILE_PATH: st.session_state.get(SS_SELECTED_FILE_PATH),
    }


def render_operation_result(result: Any) -> None:
    st = _st()

    if result is None:
        return

    data = _to_dict(result)

    success = bool(data.get("success"))
    operation = str(data.get("operation") or "operation")
    result_text = str(data.get("result") or "")
    entity_type = data.get("entity_type")
    entity_uuid = data.get("entity_uuid")
    media_uuid = data.get("media_uuid")
    version_uuid = data.get("version_uuid")
    path = data.get("path")
    payload = data.get("data") or {}

    warnings = data.get("warnings") or []
    errors = data.get("errors") or []

    with st.container(border=True):
        if success:
            st.success(result_text or f"{operation} terminée.")
        else:
            st.error(result_text or f"{operation} échouée.")

        meta: list[str] = [f"operation `{operation}`"]

        if entity_type:
            meta.append(f"entity_type `{entity_type}`")
        if entity_uuid:
            meta.append(f"entity_uuid `{entity_uuid}`")
        if media_uuid:
            meta.append(f"media_uuid `{media_uuid}`")
        if version_uuid:
            meta.append(f"version_uuid `{version_uuid}`")
        if path:
            meta.append(f"path `{path}`")

        st.caption(" · ".join(meta))

        _render_messages(warnings, kind="warning")
        _render_messages(errors, kind="error")

        if payload:
            with st.expander("Données de résultat", expanded=False):
                st.json(payload)