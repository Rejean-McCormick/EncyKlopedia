from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


from koa_mediatheque.db import get_db_connection
from koa_mediatheque.models import OperationResult
from koa_mediatheque.repositories.audit_log_repository import list_audit_log
from koa_mediatheque.repositories.library_rows_repository import list_library_rows
from koa_mediatheque.ui.layout import (
    configure_page,
    render_operation_result,
    render_sidebar_settings,
)
from koa_mediatheque.ui.widgets import render_result_messages


PAGE_TITLE = "Dashboard"
PAGE_ICON = "📚"


def _safe_get_settings() -> dict[str, Any]:
    settings = render_sidebar_settings()
    if not isinstance(settings, dict):
        return {}
    return settings


def _get_db_path(settings: dict[str, Any]) -> Path | None:
    db_path = (
        settings.get("db_path")
        or settings.get("koa_db_path")
        or st.session_state.get("koa_db_path")
    )

    if not db_path:
        return None

    return Path(str(db_path)).expanduser()


def _load_rows(db_path: Path) -> tuple[list[dict[str, Any]], OperationResult | None]:
    if not db_path.exists():
        return [], OperationResult(
            success=False,
            operation="Dashboard",
            result="db_not_found",
            path=str(db_path),
            errors=[],
            warnings=[],
        )

    try:
        with get_db_connection(db_path) as connection:
            rows = list_library_rows(connection)
        return rows, None
    except Exception as exc:
        return [], OperationResult(
            success=False,
            operation="Dashboard",
            result="load_failed",
            path=str(db_path),
            errors=[
                {
                    "code": "ERR_DASHBOARD_LOAD",
                    "severity": "error",
                    "message": str(exc),
                    "field": None,
                    "row_number": None,
                    "details": {},
                }
            ],
            warnings=[],
        )


def _load_recent_audit(db_path: Path, limit: int = 8) -> list[dict[str, Any]]:
    try:
        with get_db_connection(db_path) as connection:
            return list_audit_log(connection, limit=limit)
    except Exception:
        return []


def _count_true(rows: list[dict[str, Any]], field_name: str) -> int:
    return sum(1 for row in rows if str(row.get(field_name, "")).strip() in {"1", "true", "True"})


def _counter(rows: list[dict[str, Any]], field_name: str) -> Counter[str]:
    values: list[str] = []
    for row in rows:
        value = row.get(field_name)
        if value is None or str(value).strip() == "":
            values.append("unknown")
        else:
            values.append(str(value))
    return Counter(values)


def _render_metric_grid(rows: list[dict[str, Any]]) -> None:
    total_rows = len(rows)
    media_count = len({row.get("media_uuid") for row in rows if row.get("media_uuid")})
    version_count = len({row.get("version_uuid") for row in rows if row.get("version_uuid")})
    review_required = _count_true(rows, "human_review_required")
    export_uckk_yes = sum(1 for row in rows if row.get("export_to_uckk") == "yes")
    export_public_yes = sum(1 for row in rows if row.get("export_to_public") == "yes")

    col1, col2, col3 = st.columns(3)
    col1.metric("Lignes", total_rows)
    col2.metric("Médias", media_count)
    col3.metric("Versions", version_count)

    col4, col5, col6 = st.columns(3)
    col4.metric("À réviser", review_required)
    col5.metric("Export UCKK = yes", export_uckk_yes)
    col6.metric("Export public = yes", export_public_yes)


def _render_distribution(title: str, rows: list[dict[str, Any]], field_name: str) -> None:
    counts = _counter(rows, field_name)

    if not counts:
        st.caption("Aucune donnée.")
        return

    data = (
        pd.DataFrame(
            [{"value": key, "count": value} for key, value in counts.items()]
        )
        .sort_values(["count", "value"], ascending=[False, True])
        .reset_index(drop=True)
    )

    st.markdown(f"#### {title}")
    st.dataframe(data, use_container_width=True, hide_index=True)


def _render_review_queue(rows: list[dict[str, Any]]) -> None:
    review_rows = [
        row
        for row in rows
        if str(row.get("human_review_required", "")).strip() in {"1", "true", "True"}
    ]

    st.markdown("#### Révision humaine requise")

    if not review_rows:
        st.caption("Aucune ligne en attente de révision humaine.")
        return

    columns = [
        "title",
        "version_uuid",
        "public_state",
        "visibility",
        "rights_status",
        "review_queue",
        "review_reason",
    ]

    df = pd.DataFrame(review_rows)
    visible_columns = [column for column in columns if column in df.columns]

    st.dataframe(
        df[visible_columns],
        use_container_width=True,
        hide_index=True,
    )


def _render_recent_rows(rows: list[dict[str, Any]]) -> None:
    st.markdown("#### Dernières lignes")

    if not rows:
        st.caption("Aucune ligne dans `library_rows`.")
        return

    df = pd.DataFrame(rows)

    if "updated_at" in df.columns:
        df = df.sort_values("updated_at", ascending=False)

    columns = [
        "title",
        "media_type",
        "status",
        "uckk_relevance",
        "public_state",
        "canonical_validation_state",
        "updated_at",
    ]
    visible_columns = [column for column in columns if column in df.columns]

    st.dataframe(
        df[visible_columns].head(10),
        use_container_width=True,
        hide_index=True,
    )


def _render_recent_audit(db_path: Path) -> None:
    st.markdown("#### Audit récent")

    audit_rows = _load_recent_audit(db_path)

    if not audit_rows:
        st.caption("Aucun audit récent ou table non disponible.")
        return

    df = pd.DataFrame(audit_rows)

    columns = [
        "created_at",
        "action",
        "entity_type",
        "entity_uuid",
        "actor",
        "note",
    ]
    visible_columns = [column for column in columns if column in df.columns]

    st.dataframe(
        df[visible_columns],
        use_container_width=True,
        hide_index=True,
    )


def _render_quick_actions() -> None:
    st.markdown("#### Actions rapides")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Ouvrir table", use_container_width=True):
            st.switch_page("pages/01_Library_Table.py")

    with col2:
        if st.button("Intake ChatGPT", use_container_width=True):
            st.switch_page("pages/03_ChatGPT_Intake.py")

    with col3:
        if st.button("Export / Import XLSX", use_container_width=True):
            st.switch_page("pages/04_XLSX_Export_Import.py")

    with col4:
        if st.button("Sources", use_container_width=True):
            st.switch_page("pages/07_Sources.py")


def render_page() -> None:
    configure_page()

    st.title("Médiathèque kOA")
    st.caption("Dashboard local — SQLite source de vérité")

    settings = _safe_get_settings()
    db_path = _get_db_path(settings)

    last_result = st.session_state.get("koa_last_operation_result")
    render_operation_result(last_result)

    if db_path is None:
        st.warning("Chemin SQLite non configuré.")
        _render_quick_actions()
        return

    st.caption(f"Base active : `{db_path}`")

    rows, load_result = _load_rows(db_path)
    if load_result is not None:
        render_result_messages(load_result)
        _render_quick_actions()
        return

    _render_metric_grid(rows)

    st.divider()

    _render_quick_actions()

    st.divider()

    left, right = st.columns(2)

    with left:
        _render_distribution("Statuts", rows, "status")
        _render_distribution("Validation canonique", rows, "canonical_validation_state")
        _render_distribution("Pertinence UCKK", rows, "uckk_relevance")

    with right:
        _render_distribution("État public", rows, "public_state")
        _render_distribution("Visibilité", rows, "visibility")
        _render_distribution("Droits", rows, "rights_status")

    st.divider()

    _render_review_queue(rows)

    st.divider()

    _render_recent_rows(rows)

    st.divider()

    _render_recent_audit(db_path)


if __name__ == "__main__":
    render_page()