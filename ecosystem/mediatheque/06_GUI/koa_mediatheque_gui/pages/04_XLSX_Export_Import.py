from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


from koa_mediatheque.db import get_db_connection
from koa_mediatheque.models import ImportPreview, KoaMessage, OperationResult
from koa_mediatheque.services.xlsx_compare_service import compare_xlsx_to_sqlite
from koa_mediatheque.services.xlsx_export_service import export_library_to_xlsx
from koa_mediatheque.services.xlsx_import_service import apply_xlsx_import, preview_xlsx_import
from koa_mediatheque.ui.layout import (
    configure_page,
    render_operation_result,
    render_sidebar_settings,
)
from koa_mediatheque.ui.validation_panel import render_import_preview
from koa_mediatheque.ui.widgets import render_result_messages


PAGE_TITLE = "XLSX Export Import"

SS_DB_PATH = "koa_db_path"
SS_EXPORTS_ROOT = "koa_exports_root"
SS_IMPORTS_ROOT = "koa_imports_root"
SS_BACKUP_ROOT = "koa_backup_root"
SS_XLSX_IMPORT_PREVIEW = "koa_xlsx_import_preview"
SS_LAST_OPERATION_RESULT = "koa_last_operation_result"

XLSX_IMPORT_MODES = [
    "normal",
    "repair",
    "dry_run",
]


def _safe_get_settings() -> dict[str, Any]:
    settings = render_sidebar_settings()
    if not isinstance(settings, dict):
        return {}
    return settings


def _get_setting_path(
    settings: dict[str, Any],
    *,
    session_key: str,
    setting_keys: list[str],
) -> Path | None:
    value = None

    for key in setting_keys:
        value = settings.get(key)
        if value:
            break

    if not value:
        value = st.session_state.get(session_key)

    if not value:
        return None

    return Path(str(value)).expanduser()


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")


def _make_error_result(
    *,
    operation: str,
    result: str,
    code: str,
    message: str,
    path: str | None = None,
) -> OperationResult:
    return OperationResult(
        success=False,
        operation=operation,
        result=result,
        path=path,
        warnings=[],
        errors=[
            KoaMessage(
                code=code,
                severity="error",
                message=message,
            )
        ],
    )


def _validate_db_path(db_path: Path | None, operation: str) -> OperationResult | None:
    if db_path is None:
        return _make_error_result(
            operation=operation,
            result="db_path_missing",
            code="ERR_DB_NOT_FOUND",
            message="Chemin SQLite non configuré.",
        )

    if not db_path.exists():
        return _make_error_result(
            operation=operation,
            result="db_not_found",
            code="ERR_DB_NOT_FOUND",
            message=f"Base SQLite introuvable : {db_path}",
            path=str(db_path),
        )

    return None


def _default_xlsx_output_path(exports_root: Path | None) -> str:
    root = exports_root or Path("04_EXPORTS") / "xlsx"
    return str(root / f"koa_library_export_{_utc_stamp()}.xlsx")


def _default_import_path(imports_root: Path | None) -> str:
    root = imports_root or Path("03_IMPORTS") / "pending_review"
    return str(root)


def _render_export_filters() -> dict[str, Any]:
    st.markdown("#### Filtres export")

    col1, col2, col3 = st.columns(3)

    with col1:
        status = st.text_input(
            "status",
            value="",
            placeholder="active",
        ).strip()

    with col2:
        uckk_relevance = st.text_input(
            "uckk_relevance",
            value="",
            placeholder="uckk_core",
        ).strip()

    with col3:
        public_state = st.text_input(
            "public_state",
            value="",
            placeholder="non_public",
        ).strip()

    filters: dict[str, Any] = {}

    if status:
        filters["status"] = status

    if uckk_relevance:
        filters["uckk_relevance"] = uckk_relevance

    if public_state:
        filters["public_state"] = public_state

    return filters


def _render_export_tab(
    *,
    db_path: Path | None,
    exports_root: Path | None,
) -> None:
    st.markdown("### Export SQLite → XLSX")
    st.caption("SQLite reste la source de vérité. Le XLSX est une interface de bulk edit.")

    output_path_text = st.text_input(
        "Chemin de sortie XLSX",
        value=_default_xlsx_output_path(exports_root),
        help="Le dossier sera créé si le service d’export le permet.",
    ).strip()

    filters = _render_export_filters()

    col1, col2 = st.columns(2)

    with col1:
        include_lists = st.checkbox(
            "Inclure feuille `Lists`",
            value=True,
        )

    with col2:
        include_import_report = st.checkbox(
            "Inclure feuille `Import_Report`",
            value=True,
        )

    with st.expander("Filtres appliqués", expanded=False):
        st.json(filters)

    if st.button("Exporter XLSX", type="primary", use_container_width=True):
        validation_error = _validate_db_path(db_path, "ExportLibraryXlsx")
        if validation_error is not None:
            st.session_state[SS_LAST_OPERATION_RESULT] = validation_error
            render_result_messages(validation_error)
            return

        if not output_path_text:
            result = _make_error_result(
                operation="ExportLibraryXlsx",
                result="output_path_missing",
                code="ERR_XLSX_OUTPUT_PATH",
                message="Chemin de sortie XLSX manquant.",
            )
            st.session_state[SS_LAST_OPERATION_RESULT] = result
            render_result_messages(result)
            return

        output_path = Path(output_path_text).expanduser()

        try:
            with get_db_connection(db_path) as connection:
                result = export_library_to_xlsx(
                    connection,
                    output_path,
                    filters=filters or None,
                    include_lists=include_lists,
                    include_import_report=include_import_report,
                )

            st.session_state[SS_LAST_OPERATION_RESULT] = result
            render_result_messages(result)

            if output_path.exists():
                with output_path.open("rb") as file:
                    st.download_button(
                        "Télécharger le XLSX exporté",
                        data=file,
                        file_name=output_path.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
        except Exception as exc:
            result = _make_error_result(
                operation="ExportLibraryXlsx",
                result="export_failed",
                code="ERR_XLSX_EXPORT",
                message=str(exc),
                path=str(output_path),
            )
            st.session_state[SS_LAST_OPERATION_RESULT] = result
            render_result_messages(result)


def _save_uploaded_xlsx(uploaded_file: Any, imports_root: Path | None) -> Path:
    root = imports_root or Path("03_IMPORTS") / "pending_review"
    root.mkdir(parents=True, exist_ok=True)

    safe_name = Path(uploaded_file.name).name
    target_path = root / f"{_utc_stamp()}_{safe_name}"

    target_path.write_bytes(uploaded_file.getbuffer())

    return target_path


def _render_xlsx_source_input(imports_root: Path | None) -> Path | None:
    st.markdown("#### Source XLSX")

    source_mode = st.radio(
        "Mode source",
        ["chemin_local", "upload"],
        horizontal=True,
    )

    if source_mode == "chemin_local":
        path_text = st.text_input(
            "Chemin du XLSX à importer/comparer",
            value=_default_import_path(imports_root),
            placeholder="C:/.../koa_library_export.xlsx",
        ).strip()

        if not path_text:
            return None

        return Path(path_text).expanduser()

    uploaded_file = st.file_uploader(
        "Téléverser un fichier XLSX",
        type=["xlsx"],
    )

    if uploaded_file is None:
        return None

    try:
        saved_path = _save_uploaded_xlsx(uploaded_file, imports_root)
        st.success(f"Fichier sauvegardé : {saved_path}")
        return saved_path
    except Exception as exc:
        render_result_messages(
            _make_error_result(
                operation="SaveUploadedXlsx",
                result="save_failed",
                code="ERR_XLSX_UPLOAD_SAVE",
                message=str(exc),
            )
        )
        return None


def _preview_to_dataframe(preview: ImportPreview | None) -> pd.DataFrame:
    if preview is None:
        return pd.DataFrame()

    changes = getattr(preview, "changes", None)
    if not changes:
        return pd.DataFrame()

    return pd.DataFrame(changes)


def _render_preview_details(preview: ImportPreview | None) -> None:
    if preview is None:
        return

    render_import_preview(preview)

    df = _preview_to_dataframe(preview)

    if df.empty:
        st.caption("Aucun changement détaillé à afficher.")
        return

    with st.expander("Changements détaillés", expanded=True):
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )


def _run_preview_import(
    *,
    db_path: Path | None,
    xlsx_path: Path | None,
    mode: str,
) -> ImportPreview | None:
    validation_error = _validate_db_path(db_path, "PreviewXlsxImport")
    if validation_error is not None:
        st.session_state[SS_LAST_OPERATION_RESULT] = validation_error
        render_result_messages(validation_error)
        return None

    if xlsx_path is None:
        render_result_messages(
            _make_error_result(
                operation="PreviewXlsxImport",
                result="xlsx_path_missing",
                code="ERR_XLSX_PATH",
                message="Chemin XLSX manquant.",
            )
        )
        return None

    if not xlsx_path.exists():
        render_result_messages(
            _make_error_result(
                operation="PreviewXlsxImport",
                result="xlsx_not_found",
                code="ERR_FILE_NOT_FOUND",
                message=f"Fichier XLSX introuvable : {xlsx_path}",
                path=str(xlsx_path),
            )
        )
        return None

    try:
        with get_db_connection(db_path) as connection:
            preview = preview_xlsx_import(
                connection,
                xlsx_path,
                mode=mode,
            )

        st.session_state[SS_XLSX_IMPORT_PREVIEW] = preview
        return preview
    except Exception as exc:
        result = _make_error_result(
            operation="PreviewXlsxImport",
            result="preview_failed",
            code="ERR_XLSX_IMPORT_PREVIEW",
            message=str(exc),
            path=str(xlsx_path),
        )
        st.session_state[SS_LAST_OPERATION_RESULT] = result
        render_result_messages(result)
        return None


def _run_compare(
    *,
    db_path: Path | None,
    xlsx_path: Path | None,
) -> ImportPreview | None:
    validation_error = _validate_db_path(db_path, "CompareXlsxToSqlite")
    if validation_error is not None:
        st.session_state[SS_LAST_OPERATION_RESULT] = validation_error
        render_result_messages(validation_error)
        return None

    if xlsx_path is None:
        render_result_messages(
            _make_error_result(
                operation="CompareXlsxToSqlite",
                result="xlsx_path_missing",
                code="ERR_XLSX_PATH",
                message="Chemin XLSX manquant.",
            )
        )
        return None

    if not xlsx_path.exists():
        render_result_messages(
            _make_error_result(
                operation="CompareXlsxToSqlite",
                result="xlsx_not_found",
                code="ERR_FILE_NOT_FOUND",
                message=f"Fichier XLSX introuvable : {xlsx_path}",
                path=str(xlsx_path),
            )
        )
        return None

    try:
        with get_db_connection(db_path) as connection:
            preview = compare_xlsx_to_sqlite(
                connection,
                xlsx_path,
            )

        st.session_state[SS_XLSX_IMPORT_PREVIEW] = preview
        return preview
    except Exception as exc:
        result = _make_error_result(
            operation="CompareXlsxToSqlite",
            result="compare_failed",
            code="ERR_XLSX_COMPARE",
            message=str(exc),
            path=str(xlsx_path),
        )
        st.session_state[SS_LAST_OPERATION_RESULT] = result
        render_result_messages(result)
        return None


def _run_apply_import(
    *,
    db_path: Path | None,
    xlsx_path: Path | None,
    backup_dir: Path | None,
    mode: str,
) -> OperationResult:
    validation_error = _validate_db_path(db_path, "ApplyXlsxImport")
    if validation_error is not None:
        return validation_error

    if xlsx_path is None:
        return _make_error_result(
            operation="ApplyXlsxImport",
            result="xlsx_path_missing",
            code="ERR_XLSX_PATH",
            message="Chemin XLSX manquant.",
        )

    if not xlsx_path.exists():
        return _make_error_result(
            operation="ApplyXlsxImport",
            result="xlsx_not_found",
            code="ERR_FILE_NOT_FOUND",
            message=f"Fichier XLSX introuvable : {xlsx_path}",
            path=str(xlsx_path),
        )

    if backup_dir is None:
        return _make_error_result(
            operation="ApplyXlsxImport",
            result="backup_dir_missing",
            code="ERR_BACKUP_DIR",
            message="Dossier de backup non configuré.",
        )

    try:
        with get_db_connection(db_path) as connection:
            return apply_xlsx_import(
                connection,
                xlsx_path,
                backup_dir=backup_dir,
                actor="local_user",
                mode=mode,
            )
    except Exception as exc:
        return _make_error_result(
            operation="ApplyXlsxImport",
            result="apply_failed",
            code="ERR_XLSX_IMPORT_APPLY",
            message=str(exc),
            path=str(xlsx_path),
        )


def _render_import_tab(
    *,
    db_path: Path | None,
    imports_root: Path | None,
    backup_root: Path | None,
) -> None:
    st.markdown("### Import XLSX → SQLite")
    st.caption(
        "L’import utilise `version_uuid` comme clé. "
        "Les colonnes techniques protégées ne sont pas écrasées en mode normal."
    )

    xlsx_path = _render_xlsx_source_input(imports_root)

    mode = st.radio(
        "Mode import",
        XLSX_IMPORT_MODES,
        index=0,
        horizontal=True,
    )

    backup_dir_text = st.text_input(
        "Dossier backup",
        value=str(backup_root or Path("07_BACKUPS")),
    ).strip()
    backup_dir = Path(backup_dir_text).expanduser() if backup_dir_text else None

    st.warning(
        "La suppression d’une ligne dans XLSX ne supprime pas la ligne SQLite. "
        "Utiliser l’action `archive` pour archiver."
    )

    col1, col2, col3 = st.columns(3)

    preview: ImportPreview | None = st.session_state.get(SS_XLSX_IMPORT_PREVIEW)

    with col1:
        if st.button("Prévisualiser import", use_container_width=True):
            preview = _run_preview_import(
                db_path=db_path,
                xlsx_path=xlsx_path,
                mode=mode,
            )

    with col2:
        if st.button("Comparer XLSX / SQLite", use_container_width=True):
            preview = _run_compare(
                db_path=db_path,
                xlsx_path=xlsx_path,
            )

    with col3:
        confirm_apply = st.checkbox(
            "Confirmer application",
            value=False,
            help="L’application crée un backup et écrit un log d’import.",
        )

    if preview is not None:
        _render_preview_details(preview)

    st.divider()

    if st.button(
        "Appliquer import XLSX",
        type="primary",
        disabled=not confirm_apply,
        use_container_width=True,
    ):
        result = _run_apply_import(
            db_path=db_path,
            xlsx_path=xlsx_path,
            backup_dir=backup_dir,
            mode=mode,
        )

        st.session_state[SS_LAST_OPERATION_RESULT] = result
        render_result_messages(result)


def render_page() -> None:
    configure_page()

    st.title("XLSX Export / Import")
    st.caption("Round-trip contrôlé : SQLite → XLSX → preview → validation → SQLite")

    settings = _safe_get_settings()

    db_path = _get_setting_path(
        settings,
        session_key=SS_DB_PATH,
        setting_keys=["db_path", SS_DB_PATH],
    )
    exports_root = _get_setting_path(
        settings,
        session_key=SS_EXPORTS_ROOT,
        setting_keys=["exports_root", SS_EXPORTS_ROOT],
    )
    imports_root = _get_setting_path(
        settings,
        session_key=SS_IMPORTS_ROOT,
        setting_keys=["imports_root", SS_IMPORTS_ROOT],
    )
    backup_root = _get_setting_path(
        settings,
        session_key=SS_BACKUP_ROOT,
        setting_keys=["backup_root", SS_BACKUP_ROOT],
    )

    last_result = st.session_state.get(SS_LAST_OPERATION_RESULT)
    render_operation_result(last_result)

    if db_path is not None:
        st.caption(f"Base active : `{db_path}`")
    else:
        st.warning("Chemin SQLite non configuré.")

    tab_export, tab_import = st.tabs(["Export XLSX", "Import / Compare XLSX"])

    with tab_export:
        _render_export_tab(
            db_path=db_path,
            exports_root=exports_root,
        )

    with tab_import:
        _render_import_tab(
            db_path=db_path,
            imports_root=imports_root,
            backup_root=backup_root,
        )


if __name__ == "__main__":
    render_page()