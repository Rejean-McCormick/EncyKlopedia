# 06_GUI/koa_mediatheque_gui/app.py
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

from koa_mediatheque.workspace import get_workspace_paths


APP_PUBLIC_NAME = "Médiathèque kOA"
APP_SHORT_NAME = "kOA"
APP_TECHNICAL_NAME = "koa-mediatheque"
APP_COMPONENT = "koa_mediatheque"

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


def _gui_root() -> Path:
    return Path(__file__).resolve().parent


def _koa_root() -> Path:
    return _gui_root().parents[1]


def _ensure_import_path() -> None:
    gui_root = str(_gui_root())
    if gui_root not in sys.path:
        sys.path.insert(0, gui_root)


def _safe_import_streamlit():
    try:
        import streamlit as st  # type: ignore

        return st
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Streamlit n'est pas installé. Installe les dépendances avec : "
            "pip install -r 06_GUI/koa_mediatheque_gui/requirements.txt"
        ) from exc


def _safe_import_layout() -> tuple[
    Callable[[], None],
    Callable[[], dict[str, Any]],
    Callable[[Any], None],
    Exception | None,
]:
    try:
        from koa_mediatheque.ui.layout import (
            configure_page,
            render_operation_result,
            render_sidebar_settings,
        )

        return configure_page, render_sidebar_settings, render_operation_result, None
    except Exception as exc:
        st = _safe_import_streamlit()

        def configure_page_fallback() -> None:
            st.set_page_config(
                page_title=APP_PUBLIC_NAME,
                page_icon="📚",
                layout="wide",
                initial_sidebar_state="expanded",
            )

        def render_sidebar_settings_fallback() -> dict[str, Any]:
            with st.sidebar:
                st.header(APP_SHORT_NAME)
                st.caption(APP_TECHNICAL_NAME)

                paths = get_workspace_paths(_koa_root())

                db_path = st.text_input(
                    "Base SQLite",
                    value=str(paths.db_path),
                    key=SS_DB_PATH,
                )
                storage_root = st.text_input(
                    "Stockage",
                    value=str(paths.storage_root),
                    key=SS_STORAGE_ROOT,
                )
                imports_root = st.text_input(
                    "Imports",
                    value=str(paths.imports_root),
                    key=SS_IMPORTS_ROOT,
                )
                exports_root = st.text_input(
                    "Exports",
                    value=str(paths.exports_root),
                    key=SS_EXPORTS_ROOT,
                )
                backup_root = st.text_input(
                    "Backups",
                    value=str(paths.backups_root),
                    key=SS_BACKUP_ROOT,
                )

            return {
                SS_DB_PATH: db_path,
                SS_STORAGE_ROOT: storage_root,
                SS_IMPORTS_ROOT: imports_root,
                SS_EXPORTS_ROOT: exports_root,
                SS_BACKUP_ROOT: backup_root,
            }

        def render_operation_result_fallback(result: Any) -> None:
            if result is None:
                return

            success = bool(getattr(result, "success", False))
            result_text = str(getattr(result, "result", ""))

            if success:
                st.success(result_text or "Opération terminée.")
            else:
                st.error(result_text or "Opération échouée.")

        return (
            configure_page_fallback,
            render_sidebar_settings_fallback,
            render_operation_result_fallback,
            exc,
        )


def _initialize_session_state() -> None:
    st = _safe_import_streamlit()
    paths = get_workspace_paths(_koa_root())

    defaults: dict[str, Any] = {
        SS_DB_PATH: str(paths.db_path),
        SS_STORAGE_ROOT: str(paths.storage_root),
        SS_IMPORTS_ROOT: str(paths.imports_root),
        SS_EXPORTS_ROOT: str(paths.exports_root),
        SS_BACKUP_ROOT: str(paths.backups_root),
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
        st.session_state.setdefault(key, value)


def _render_home(settings: dict[str, Any]) -> None:
    st = _safe_import_streamlit()

    st.title(APP_PUBLIC_NAME)
    st.caption("Engine Médiathèque + instance de données sélectionnée.")

    col_db, col_storage, col_imports, col_exports = st.columns(4)

    col_db.metric("DB", "SQLite")
    col_storage.metric("Stockage", "local")
    col_imports.metric("Imports", "ChatGPT / XLSX")
    col_exports.metric("Exports", "XLSX / manifest")

    st.divider()

    st.subheader("État de configuration")

    config_rows = [
        ("Base SQLite", settings.get(SS_DB_PATH) or st.session_state.get(SS_DB_PATH)),
        ("Stockage", settings.get(SS_STORAGE_ROOT) or st.session_state.get(SS_STORAGE_ROOT)),
        ("Imports", settings.get(SS_IMPORTS_ROOT) or st.session_state.get(SS_IMPORTS_ROOT)),
        ("Exports", settings.get(SS_EXPORTS_ROOT) or st.session_state.get(SS_EXPORTS_ROOT)),
        ("Backups", settings.get(SS_BACKUP_ROOT) or st.session_state.get(SS_BACKUP_ROOT)),
    ]

    for label, value in config_rows:
        path = Path(str(value)).expanduser() if value else None
        exists = path.exists() if path else False

        status = "OK" if exists else "À créer / vérifier"
        st.write(f"**{label}** — `{value}` — {status}")

    st.divider()

    st.subheader("Pages attendues")

    st.write(
        "Utilise le menu Streamlit pour ouvrir les pages : "
        "`Dashboard`, `Library Table`, `File Preview`, `ChatGPT Intake`, "
        "`XLSX Export/Import`, `Settings`, `Logs`, `Sources`, `Contenu local`."
    )


def _render_alignment_notice(layout_import_error: Exception | None) -> None:
    st = _safe_import_streamlit()

    if layout_import_error is None:
        return

    with st.expander("Module UI partiellement disponible", expanded=False):
        st.warning(
            "Le module `koa_mediatheque.ui.layout` n'est pas encore disponible "
            "ou contient une erreur. `app.py` utilise un fallback minimal."
        )
        st.code(str(layout_import_error), language="text")


def main() -> None:
    _ensure_import_path()

    st = _safe_import_streamlit()

    (
        configure_page,
        render_sidebar_settings,
        render_operation_result,
        layout_import_error,
    ) = _safe_import_layout()

    configure_page()
    _initialize_session_state()

    settings = render_sidebar_settings()

    _render_alignment_notice(layout_import_error)
    _render_home(settings)

    render_operation_result(st.session_state.get(SS_LAST_OPERATION_RESULT))


if __name__ == "__main__":
    main()