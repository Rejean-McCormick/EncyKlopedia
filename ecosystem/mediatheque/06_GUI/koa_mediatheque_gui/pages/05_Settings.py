from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import streamlit as st
from streamlit.errors import StreamlitAPIException


APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


from koa_mediatheque.db import (
    database_exists,
    get_db_connection,
    get_schema_version,
    initialize_database,
)
from koa_mediatheque.models import KoaMessage, OperationResult
from koa_mediatheque.ui.layout import (
    configure_page,
    render_operation_result,
    render_sidebar_settings,
)
from koa_mediatheque.ui.widgets import render_result_messages


PAGE_TITLE = "Settings"

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

WIDGET_SETTINGS_DB_PATH = "koa_settings_db_path"
WIDGET_SETTINGS_STORAGE_ROOT = "koa_settings_storage_root"
WIDGET_SETTINGS_IMPORTS_ROOT = "koa_settings_imports_root"
WIDGET_SETTINGS_EXPORTS_ROOT = "koa_settings_exports_root"
WIDGET_SETTINGS_BACKUP_ROOT = "koa_settings_backup_root"
WIDGET_SETTINGS_SCHEMA_DIR = "koa_settings_schema_dir"
WIDGET_SETTINGS_OVERWRITE_DB = "koa_settings_overwrite_db"

CANONICAL_DB_PATH = "01_DB/koa_mediatheque.sqlite"
CANONICAL_STORAGE_ROOT = "02_STORAGE"
CANONICAL_IMPORTS_ROOT = "03_IMPORTS"
CANONICAL_EXPORTS_ROOT = "04_EXPORTS"
CANONICAL_BACKUP_ROOT = "07_BACKUPS"
CANONICAL_SCHEMA_DIR = "schemas/sqlite"

STORAGE_AREAS = [
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
]

IMPORT_AREAS = [
    "google_drive_raw",
    "google_drive_scanned",
    "ai_generated_docs",
    "pending_review",
]

EXPORT_AREAS = [
    "xlsx",
    "manifests",
    "uckkarchive",
    "public_review",
]


def _make_result(
    *,
    success: bool,
    operation: str,
    result: str,
    message: str | None = None,
    code: str = "INFO_SETTINGS",
    severity: str = "info",
    path: str | None = None,
) -> OperationResult:
    messages = []
    if message:
        messages.append(
            KoaMessage(
                code=code,
                severity=severity,
                message=message,
            )
        )

    if success:
        return OperationResult(
            success=True,
            operation=operation,
            result=result,
            path=path,
            warnings=messages if severity == "warning" else [],
            errors=[],
        )

    return OperationResult(
        success=False,
        operation=operation,
        result=result,
        path=path,
        warnings=[],
        errors=messages,
    )


def _safe_get_settings() -> dict[str, Any]:
    settings = render_sidebar_settings()
    if not isinstance(settings, dict):
        return {}
    return settings


def _project_root_guess() -> Path:
    return APP_DIR.parents[1]


def _resolve_default_path(relative_path: str) -> str:
    return str((_project_root_guess() / relative_path).resolve())


def _normalize_path_text(path_text: Any) -> str:
    return str(Path(str(path_text or "").strip()).expanduser())


def _get_session_path(key: str, default_relative_path: str) -> str:
    value = st.session_state.get(key)

    if isinstance(value, str) and value.strip():
        return value.strip()

    if value:
        return str(value)

    return _resolve_default_path(default_relative_path)


def _ensure_widget_value(widget_key: str, value: str) -> None:
    current_value = st.session_state.get(widget_key)

    if current_value is None:
        st.session_state[widget_key] = value
        return

    if isinstance(current_value, str) and current_value.strip() == "":
        st.session_state[widget_key] = value


def _ensure_settings_widget_defaults() -> None:
    _ensure_widget_value(
        WIDGET_SETTINGS_DB_PATH,
        _get_session_path(SS_DB_PATH, CANONICAL_DB_PATH),
    )
    _ensure_widget_value(
        WIDGET_SETTINGS_STORAGE_ROOT,
        _get_session_path(SS_STORAGE_ROOT, CANONICAL_STORAGE_ROOT),
    )
    _ensure_widget_value(
        WIDGET_SETTINGS_IMPORTS_ROOT,
        _get_session_path(SS_IMPORTS_ROOT, CANONICAL_IMPORTS_ROOT),
    )
    _ensure_widget_value(
        WIDGET_SETTINGS_EXPORTS_ROOT,
        _get_session_path(SS_EXPORTS_ROOT, CANONICAL_EXPORTS_ROOT),
    )
    _ensure_widget_value(
        WIDGET_SETTINGS_BACKUP_ROOT,
        _get_session_path(SS_BACKUP_ROOT, CANONICAL_BACKUP_ROOT),
    )
    _ensure_widget_value(
        WIDGET_SETTINGS_SCHEMA_DIR,
        _resolve_default_path(CANONICAL_SCHEMA_DIR),
    )


def _path_status(path: Path) -> str:
    if path.exists() and path.is_file():
        return "file"
    if path.exists() and path.is_dir():
        return "dir"
    return "missing"


def _render_path_status(label: str, path: Path, expected: str) -> None:
    status = _path_status(path)

    if status == expected:
        st.success(f"{label} : OK — `{path}`")
    elif status == "missing":
        st.warning(f"{label} : manquant — `{path}`")
    else:
        st.error(f"{label} : type inattendu `{status}` — `{path}`")


def _try_set_session_value(key: str, value: str) -> KoaMessage | None:
    try:
        st.session_state[key] = _normalize_path_text(value)
        return None
    except StreamlitAPIException as exc:
        return KoaMessage(
            code="ERR_STREAMLIT_SESSION_KEY_LOCKED",
            severity="error",
            message=(
                f"Impossible d'enregistrer `{key}` dans la session Streamlit. "
                "Une ancienne instance de widget utilise probablement encore cette clé. "
                "Arrête Streamlit avec Ctrl+C puis relance .\\Start-KoaGui.ps1."
            ),
            details={"exception": str(exc)},
        )


def _save_paths_to_session(
    *,
    db_path: str,
    storage_root: str,
    imports_root: str,
    exports_root: str,
    backup_root: str,
) -> OperationResult:
    errors = [
        message
        for message in [
            _try_set_session_value(SS_DB_PATH, db_path),
            _try_set_session_value(SS_STORAGE_ROOT, storage_root),
            _try_set_session_value(SS_IMPORTS_ROOT, imports_root),
            _try_set_session_value(SS_EXPORTS_ROOT, exports_root),
            _try_set_session_value(SS_BACKUP_ROOT, backup_root),
        ]
        if message is not None
    ]

    if errors:
        return OperationResult(
            success=False,
            operation="Settings",
            result="paths_save_failed",
            warnings=[],
            errors=errors,
        )

    return _make_result(
        success=True,
        operation="Settings",
        result="paths_saved",
        message="Chemins enregistrés dans la session Streamlit.",
    )


def _create_required_directories(
    *,
    db_path: Path,
    storage_root: Path,
    imports_root: Path,
    exports_root: Path,
    backup_root: Path,
) -> OperationResult:
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        storage_root.mkdir(parents=True, exist_ok=True)
        imports_root.mkdir(parents=True, exist_ok=True)
        exports_root.mkdir(parents=True, exist_ok=True)
        backup_root.mkdir(parents=True, exist_ok=True)

        for area in STORAGE_AREAS:
            (storage_root / area).mkdir(parents=True, exist_ok=True)

        for area in IMPORT_AREAS:
            (imports_root / area).mkdir(parents=True, exist_ok=True)

        for area in EXPORT_AREAS:
            (exports_root / area).mkdir(parents=True, exist_ok=True)

        return _make_result(
            success=True,
            operation="Settings",
            result="directories_created",
            message="Dossiers canoniques créés ou déjà présents.",
        )
    except Exception as exc:
        return _make_result(
            success=False,
            operation="Settings",
            result="directory_creation_failed",
            code="ERR_SETTINGS_DIRECTORY_CREATE",
            severity="error",
            message=str(exc),
        )


def _initialize_db(
    *,
    db_path: Path,
    schema_dir: Path,
    overwrite: bool,
) -> OperationResult:
    if not schema_dir.exists():
        return _make_result(
            success=False,
            operation="InitializeDatabase",
            result="schema_dir_not_found",
            code="ERR_SCHEMA_DIR_NOT_FOUND",
            severity="error",
            message=f"Dossier de schéma introuvable : {schema_dir}",
            path=str(schema_dir),
        )

    try:
        return initialize_database(
            db_path,
            schema_dir,
            overwrite=overwrite,
        )
    except Exception as exc:
        return _make_result(
            success=False,
            operation="InitializeDatabase",
            result="initialization_failed",
            code="ERR_DB_SCHEMA",
            severity="error",
            message=str(exc),
            path=str(db_path),
        )


def _read_db_health(db_path: Path) -> dict[str, Any]:
    health: dict[str, Any] = {
        "exists": False,
        "schema_version": None,
        "library_rows_count": None,
        "error": None,
    }

    try:
        health["exists"] = database_exists(db_path)

        if not health["exists"]:
            return health

        with get_db_connection(db_path) as connection:
            health["schema_version"] = get_schema_version(connection)
            cursor = connection.execute("SELECT COUNT(*) AS count FROM library_rows")
            health["library_rows_count"] = cursor.fetchone()[0]

        return health
    except Exception as exc:
        health["error"] = str(exc)
        return health


def _render_path_settings() -> tuple[Path, Path, Path, Path, Path, Path]:
    st.markdown("### Chemins")
    _ensure_settings_widget_defaults()

    db_path_text = st.text_input(
        "KOA_DB_PATH",
        key=WIDGET_SETTINGS_DB_PATH,
    )

    storage_root_text = st.text_input(
        "KOA_STORAGE_DIR",
        key=WIDGET_SETTINGS_STORAGE_ROOT,
    )

    imports_root_text = st.text_input(
        "KOA_IMPORTS_DIR",
        key=WIDGET_SETTINGS_IMPORTS_ROOT,
    )

    exports_root_text = st.text_input(
        "KOA_EXPORTS_DIR",
        key=WIDGET_SETTINGS_EXPORTS_ROOT,
    )

    backup_root_text = st.text_input(
        "KOA_BACKUPS_DIR",
        key=WIDGET_SETTINGS_BACKUP_ROOT,
    )

    schema_dir_text = st.text_input(
        "Schema dir",
        key=WIDGET_SETTINGS_SCHEMA_DIR,
    )

    db_path = Path(_normalize_path_text(db_path_text))
    storage_root = Path(_normalize_path_text(storage_root_text))
    imports_root = Path(_normalize_path_text(imports_root_text))
    exports_root = Path(_normalize_path_text(exports_root_text))
    backup_root = Path(_normalize_path_text(backup_root_text))
    schema_dir = Path(_normalize_path_text(schema_dir_text))

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Enregistrer chemins", type="primary", use_container_width=True):
            result = _save_paths_to_session(
                db_path=str(db_path),
                storage_root=str(storage_root),
                imports_root=str(imports_root),
                exports_root=str(exports_root),
                backup_root=str(backup_root),
            )
            st.session_state[SS_LAST_OPERATION_RESULT] = result
            render_result_messages(result)

    with col2:
        if st.button("Créer dossiers canoniques", use_container_width=True):
            result = _create_required_directories(
                db_path=db_path,
                storage_root=storage_root,
                imports_root=imports_root,
                exports_root=exports_root,
                backup_root=backup_root,
            )
            st.session_state[SS_LAST_OPERATION_RESULT] = result
            render_result_messages(result)

    return db_path, storage_root, imports_root, exports_root, backup_root, schema_dir


def _render_path_checks(
    *,
    db_path: Path,
    storage_root: Path,
    imports_root: Path,
    exports_root: Path,
    backup_root: Path,
    schema_dir: Path,
) -> None:
    st.markdown("### Vérification chemins")

    _render_path_status("Base SQLite", db_path, "file")
    _render_path_status("Stockage", storage_root, "dir")
    _render_path_status("Imports", imports_root, "dir")
    _render_path_status("Exports", exports_root, "dir")
    _render_path_status("Backups", backup_root, "dir")
    _render_path_status("Schémas SQL", schema_dir, "dir")

    with st.expander("Zones de stockage", expanded=False):
        for area in STORAGE_AREAS:
            _render_path_status(area, storage_root / area, "dir")

    with st.expander("Zones imports", expanded=False):
        for area in IMPORT_AREAS:
            _render_path_status(area, imports_root / area, "dir")

    with st.expander("Zones exports", expanded=False):
        for area in EXPORT_AREAS:
            _render_path_status(area, exports_root / area, "dir")


def _render_database_settings(
    *,
    db_path: Path,
    schema_dir: Path,
) -> None:
    st.markdown("### Base SQLite")

    health = _read_db_health(db_path)

    col1, col2, col3 = st.columns(3)
    col1.metric("Existe", "oui" if health["exists"] else "non")
    col2.metric("Schema version", health["schema_version"] or "unknown")
    col3.metric(
        "library_rows",
        health["library_rows_count"] if health["library_rows_count"] is not None else "—",
    )

    if health["error"]:
        st.error(health["error"])

    overwrite = st.checkbox(
        "Overwrite database existante",
        value=False,
        key=WIDGET_SETTINGS_OVERWRITE_DB,
        help="À utiliser seulement pour réinitialiser explicitement une base locale.",
    )

    if st.button("Initialiser base SQLite", type="primary", use_container_width=True):
        result = _initialize_db(
            db_path=db_path,
            schema_dir=schema_dir,
            overwrite=overwrite,
        )
        st.session_state[SS_LAST_OPERATION_RESULT] = result
        render_result_messages(result)


def _render_session_state_tools() -> None:
    st.markdown("### Session Streamlit")

    visible_keys = [
        SS_DB_PATH,
        SS_STORAGE_ROOT,
        SS_IMPORTS_ROOT,
        SS_EXPORTS_ROOT,
        SS_BACKUP_ROOT,
        SS_SELECTED_VERSION_UUID,
        SS_SELECTED_MEDIA_UUID,
        SS_SELECTED_FILE_PATH,
        SS_CURRENT_FILTERS,
    ]

    session_snapshot = {
        key: st.session_state.get(key)
        for key in visible_keys
        if key in st.session_state
    }

    st.json(session_snapshot)

    with st.expander("Nettoyage session", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Effacer sélection", use_container_width=True):
                for key in [
                    SS_SELECTED_VERSION_UUID,
                    SS_SELECTED_MEDIA_UUID,
                    SS_SELECTED_FILE_PATH,
                ]:
                    st.session_state.pop(key, None)

                result = _make_result(
                    success=True,
                    operation="Settings",
                    result="selection_cleared",
                    message="Sélection courante effacée.",
                )
                st.session_state[SS_LAST_OPERATION_RESULT] = result
                render_result_messages(result)
                st.rerun()

        with col2:
            if st.button("Effacer previews", use_container_width=True):
                for key in [
                    SS_CHATGPT_VALIDATION_RESULT,
                    SS_CHATGPT_PREVIEW_ROW,
                    SS_XLSX_IMPORT_PREVIEW,
                ]:
                    st.session_state.pop(key, None)

                result = _make_result(
                    success=True,
                    operation="Settings",
                    result="previews_cleared",
                    message="Prévisualisations effacées.",
                )
                st.session_state[SS_LAST_OPERATION_RESULT] = result
                render_result_messages(result)
                st.rerun()

        with col3:
            if st.button("Effacer dernier résultat", use_container_width=True):
                st.session_state.pop(SS_LAST_OPERATION_RESULT, None)
                st.rerun()


def _render_environment_info() -> None:
    st.markdown("### Environnement")

    info = {
        "python": sys.version.split()[0],
        "cwd": os.getcwd(),
        "app_dir": str(APP_DIR),
        "project_root_guess": str(_project_root_guess()),
        "platform": sys.platform,
    }

    st.json(info)


def render_page() -> None:
    configure_page()

    st.title("Settings")
    st.caption("Configuration locale des chemins, de la base SQLite et de la session")

    _safe_get_settings()

    last_result = st.session_state.get(SS_LAST_OPERATION_RESULT)
    render_operation_result(last_result)

    db_path, storage_root, imports_root, exports_root, backup_root, schema_dir = _render_path_settings()

    st.divider()

    tab_paths, tab_db, tab_session, tab_env = st.tabs(
        ["Chemins", "SQLite", "Session", "Environnement"]
    )

    with tab_paths:
        _render_path_checks(
            db_path=db_path,
            storage_root=storage_root,
            imports_root=imports_root,
            exports_root=exports_root,
            backup_root=backup_root,
            schema_dir=schema_dir,
        )

    with tab_db:
        _render_database_settings(
            db_path=db_path,
            schema_dir=schema_dir,
        )

    with tab_session:
        _render_session_state_tools()

    with tab_env:
        _render_environment_info()


if __name__ == "__main__":
    render_page()
