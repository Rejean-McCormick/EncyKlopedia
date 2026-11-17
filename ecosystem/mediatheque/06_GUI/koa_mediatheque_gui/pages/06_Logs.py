from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


from koa_mediatheque.db import get_db_connection
from koa_mediatheque.models import KoaMessage, OperationResult
from koa_mediatheque.repositories.audit_log_repository import list_audit_log
from koa_mediatheque.repositories.chatgpt_intake_log_repository import (
    list_chatgpt_intake_log,
)
from koa_mediatheque.repositories.xlsx_import_log_repository import (
    list_xlsx_import_log,
)
from koa_mediatheque.ui.layout import (
    configure_page,
    render_operation_result,
    render_sidebar_settings,
)
from koa_mediatheque.ui.log_viewer import (
    render_audit_log,
    render_chatgpt_intake_log,
    render_xlsx_import_log,
)
from koa_mediatheque.ui.widgets import render_result_messages


PAGE_TITLE = "Logs"

SS_DB_PATH = "koa_db_path"
SS_LAST_OPERATION_RESULT = "koa_last_operation_result"

LOG_LIMIT_DEFAULT = 200
LOG_LIMIT_OPTIONS = [50, 100, 200, 500, 1000]


def _safe_get_settings() -> dict[str, Any]:
    settings = render_sidebar_settings()
    if not isinstance(settings, dict):
        return {}
    return settings


def _get_db_path(settings: dict[str, Any]) -> Path | None:
    db_path = (
        settings.get("db_path")
        or settings.get(SS_DB_PATH)
        or st.session_state.get(SS_DB_PATH)
    )

    if not db_path:
        return None

    return Path(str(db_path)).expanduser()


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


def _validate_db_path(db_path: Path | None) -> OperationResult | None:
    if db_path is None:
        return _make_error_result(
            operation="Logs",
            result="db_path_missing",
            code="ERR_DB_NOT_FOUND",
            message="Chemin SQLite non configuré.",
        )

    if not db_path.exists():
        return _make_error_result(
            operation="Logs",
            result="db_not_found",
            code="ERR_DB_NOT_FOUND",
            message=f"Base SQLite introuvable : {db_path}",
            path=str(db_path),
        )

    return None


def _safe_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


def _filter_dataframe(
    df: pd.DataFrame,
    *,
    search_text: str,
    severity_filter: str,
    action_filter: str,
) -> pd.DataFrame:
    if df.empty:
        return df

    filtered = df.copy()

    if search_text:
        object_columns = [
            column for column in filtered.columns if filtered[column].dtype == "object"
        ]

        if object_columns:
            mask = pd.Series(False, index=filtered.index)

            for column in object_columns:
                mask = mask | filtered[column].fillna("").astype(str).str.contains(
                    search_text,
                    case=False,
                    regex=False,
                )

            filtered = filtered[mask]

    if severity_filter != "all" and "severity" in filtered.columns:
        filtered = filtered[filtered["severity"].fillna("").astype(str) == severity_filter]

    if action_filter != "all" and "action" in filtered.columns:
        filtered = filtered[filtered["action"].fillna("").astype(str) == action_filter]

    return filtered.reset_index(drop=True)


def _render_log_dataframe(
    *,
    title: str,
    rows: list[dict[str, Any]],
    default_columns: list[str],
    key_prefix: str,
) -> None:
    st.markdown(f"### {title}")

    df = _safe_dataframe(rows)

    if df.empty:
        st.caption("Aucune entrée.")
        return

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_text = st.text_input(
            "Recherche",
            value="",
            key=f"{key_prefix}_search",
            placeholder="action, UUID, fichier, erreur, note...",
        ).strip()

    with col2:
        if "severity" in df.columns:
            severity_values = sorted(
                {
                    str(value)
                    for value in df["severity"].dropna().unique().tolist()
                    if str(value).strip()
                }
            )
            severity_filter = st.selectbox(
                "severity",
                ["all", *severity_values],
                key=f"{key_prefix}_severity",
            )
        else:
            severity_filter = "all"

    with col3:
        if "action" in df.columns:
            action_values = sorted(
                {
                    str(value)
                    for value in df["action"].dropna().unique().tolist()
                    if str(value).strip()
                }
            )
            action_filter = st.selectbox(
                "action",
                ["all", *action_values],
                key=f"{key_prefix}_action",
            )
        else:
            action_filter = "all"

    filtered_df = _filter_dataframe(
        df,
        search_text=search_text,
        severity_filter=severity_filter,
        action_filter=action_filter,
    )

    metric1, metric2 = st.columns(2)
    metric1.metric("Total", len(df))
    metric2.metric("Affiché", len(filtered_df))

    show_all_columns = st.checkbox(
        "Afficher toutes les colonnes",
        value=False,
        key=f"{key_prefix}_show_all_columns",
    )

    if show_all_columns:
        visible_columns = list(filtered_df.columns)
    else:
        visible_columns = [
            column for column in default_columns if column in filtered_df.columns
        ]

        if not visible_columns:
            visible_columns = list(filtered_df.columns)

    st.dataframe(
        filtered_df[visible_columns],
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("JSON brut", expanded=False):
        st.json(filtered_df.to_dict(orient="records"))


def _load_audit_rows(db_path: Path, limit: int) -> tuple[list[dict[str, Any]], OperationResult | None]:
    try:
        with get_db_connection(db_path) as connection:
            rows = list_audit_log(connection, limit=limit)
        return rows, None
    except Exception as exc:
        return [], _make_error_result(
            operation="LogsAudit",
            result="load_failed",
            code="ERR_AUDIT_LOG_LOAD",
            message=str(exc),
            path=str(db_path),
        )


def _load_chatgpt_rows(db_path: Path, limit: int) -> tuple[list[dict[str, Any]], OperationResult | None]:
    try:
        with get_db_connection(db_path) as connection:
            rows = list_chatgpt_intake_log(connection, limit=limit)
        return rows, None
    except Exception as exc:
        return [], _make_error_result(
            operation="LogsChatGPTIntake",
            result="load_failed",
            code="ERR_CHATGPT_INTAKE_LOG_LOAD",
            message=str(exc),
            path=str(db_path),
        )


def _load_xlsx_rows(db_path: Path) -> tuple[list[dict[str, Any]], OperationResult | None]:
    try:
        with get_db_connection(db_path) as connection:
            rows = list_xlsx_import_log(connection, import_uuid=None)
        return rows, None
    except Exception as exc:
        return [], _make_error_result(
            operation="LogsXlsxImport",
            result="load_failed",
            code="ERR_XLSX_IMPORT_LOG_LOAD",
            message=str(exc),
            path=str(db_path),
        )


def _load_file_scan_rows(db_path: Path, limit: int) -> tuple[list[dict[str, Any]], OperationResult | None]:
    try:
        with get_db_connection(db_path) as connection:
            cursor = connection.execute(
                """
                SELECT *
                FROM file_scan_log
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(row) for row in cursor.fetchall()]
        return rows, None
    except Exception as exc:
        return [], _make_error_result(
            operation="LogsFileScan",
            result="load_failed",
            code="ERR_FILE_SCAN_LOG_LOAD",
            message=str(exc),
            path=str(db_path),
        )


def _render_ui_log_viewers(db_path: Path) -> None:
    st.markdown("### Viewers UI")

    try:
        with get_db_connection(db_path) as connection:
            tab_audit, tab_chatgpt, tab_xlsx = st.tabs(
                ["Audit", "ChatGPT intake", "XLSX import"]
            )

            with tab_audit:
                render_audit_log(connection)

            with tab_chatgpt:
                render_chatgpt_intake_log(connection)

            with tab_xlsx:
                render_xlsx_import_log(connection)

    except Exception as exc:
        render_result_messages(
            _make_error_result(
                operation="LogsUiViewers",
                result="render_failed",
                code="ERR_LOG_VIEWER_RENDER",
                message=str(exc),
                path=str(db_path),
            )
        )


def _render_audit_tab(db_path: Path, limit: int) -> None:
    rows, result = _load_audit_rows(db_path, limit)

    if result is not None:
        render_result_messages(result)
        return

    _render_log_dataframe(
        title="Audit log",
        rows=rows,
        default_columns=[
            "created_at",
            "action",
            "entity_type",
            "entity_uuid",
            "actor",
            "note",
        ],
        key_prefix="audit_log",
    )


def _render_chatgpt_tab(db_path: Path, limit: int) -> None:
    rows, result = _load_chatgpt_rows(db_path, limit)

    if result is not None:
        render_result_messages(result)
        return

    _render_log_dataframe(
        title="ChatGPT intake log",
        rows=rows,
        default_columns=[
            "created_at",
            "version_uuid",
            "file_path",
            "validation_status",
            "validation_errors",
        ],
        key_prefix="chatgpt_intake_log",
    )


def _render_xlsx_tab(db_path: Path, limit: int) -> None:
    rows, result = _load_xlsx_rows(db_path)

    if result is not None:
        render_result_messages(result)
        return

    if len(rows) > limit:
        rows = rows[:limit]

    _render_log_dataframe(
        title="XLSX import log",
        rows=rows,
        default_columns=[
            "created_at",
            "import_uuid",
            "xlsx_path",
            "mode",
            "status",
            "rows_total",
            "rows_updated",
            "rows_new",
            "rows_blocked",
            "errors_json",
        ],
        key_prefix="xlsx_import_log",
    )


def _render_file_scan_tab(db_path: Path, limit: int) -> None:
    rows, result = _load_file_scan_rows(db_path, limit)

    if result is not None:
        render_result_messages(result)
        return

    _render_log_dataframe(
        title="File scan log",
        rows=rows,
        default_columns=[
            "created_at",
            "import_batch",
            "scan_root",
            "file_path",
            "sha256",
            "filesize",
            "mimetype",
            "status",
            "message",
        ],
        key_prefix="file_scan_log",
    )


def _render_health_tab(db_path: Path) -> None:
    st.markdown("### Santé des logs")

    tables = [
        "audit_log",
        "chatgpt_intake_log",
        "xlsx_import_log",
        "file_scan_log",
    ]

    rows: list[dict[str, Any]] = []

    try:
        with get_db_connection(db_path) as connection:
            for table in tables:
                try:
                    cursor = connection.execute(f"SELECT COUNT(*) AS count FROM {table}")
                    count = cursor.fetchone()[0]
                    rows.append(
                        {
                            "table": table,
                            "exists": True,
                            "count": count,
                            "error": "",
                        }
                    )
                except Exception as exc:
                    rows.append(
                        {
                            "table": table,
                            "exists": False,
                            "count": None,
                            "error": str(exc),
                        }
                    )
    except Exception as exc:
        render_result_messages(
            _make_error_result(
                operation="LogsHealth",
                result="health_failed",
                code="ERR_LOG_HEALTH",
                message=str(exc),
                path=str(db_path),
            )
        )
        return

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )


def render_page() -> None:
    configure_page()

    st.title("Logs")
    st.caption("Audit, intake ChatGPT, imports XLSX et scans fichiers")

    settings = _safe_get_settings()
    db_path = _get_db_path(settings)

    last_result = st.session_state.get(SS_LAST_OPERATION_RESULT)
    render_operation_result(last_result)

    validation_error = _validate_db_path(db_path)
    if validation_error is not None:
        render_result_messages(validation_error)
        return

    st.caption(f"Base active : `{db_path}`")

    limit = st.selectbox(
        "Nombre maximal d’entrées",
        LOG_LIMIT_OPTIONS,
        index=LOG_LIMIT_OPTIONS.index(LOG_LIMIT_DEFAULT),
    )

    tab_audit, tab_chatgpt, tab_xlsx, tab_scan, tab_health, tab_ui_viewers = st.tabs(
        [
            "Audit",
            "ChatGPT intake",
            "XLSX import",
            "File scan",
            "Santé",
            "Viewers UI",
        ]
    )

    with tab_audit:
        _render_audit_tab(db_path, limit)

    with tab_chatgpt:
        _render_chatgpt_tab(db_path, limit)

    with tab_xlsx:
        _render_xlsx_tab(db_path, limit)

    with tab_scan:
        _render_file_scan_tab(db_path, limit)

    with tab_health:
        _render_health_tab(db_path)

    with tab_ui_viewers:
        _render_ui_log_viewers(db_path)


if __name__ == "__main__":
    render_page()