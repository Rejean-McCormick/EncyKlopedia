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
from koa_mediatheque.models import OperationResult
from koa_mediatheque.repositories.library_rows_repository import (
    get_library_row_by_version_uuid,
    list_library_rows,
    soft_delete_library_row,
    update_library_row_by_version_uuid,
)
from koa_mediatheque.ui.file_preview import render_file_actions, render_file_preview
from koa_mediatheque.ui.layout import (
    configure_page,
    render_operation_result,
    render_sidebar_settings,
)
from koa_mediatheque.ui.row_editor import render_row_editor
from koa_mediatheque.ui.table_filters import apply_dataframe_filters, render_library_filters
from koa_mediatheque.ui.widgets import render_result_messages


PAGE_TITLE = "Library Table"

SS_SELECTED_VERSION_UUID = "koa_selected_version_uuid"
SS_SELECTED_MEDIA_UUID = "koa_selected_media_uuid"
SS_SELECTED_FILE_PATH = "koa_selected_file_path"
SS_CURRENT_FILTERS = "koa_current_filters"
SS_LAST_OPERATION_RESULT = "koa_last_operation_result"


DEFAULT_VISIBLE_COLUMNS = [
    "title",
    "filename",
    "media_type",
    "status",
    "uckk_relevance",
    "target_system",
    "public_state",
    "visibility",
    "rights_status",
    "human_review_required",
    "canonical_validation_state",
    "updated_at",
    "version_uuid",
]


PROTECTED_DISPLAY_COLUMNS = [
    "id",
    "media_uuid",
    "version_uuid",
    "sha256",
    "filesize",
    "mimetype",
    "original_path",
    "storage_path",
    "created_at",
    "updated_at",
]


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
            operation="LibraryTable",
            result="db_not_found",
            path=str(db_path),
            warnings=[],
            errors=[
                {
                    "code": "ERR_DB_NOT_FOUND",
                    "severity": "error",
                    "message": f"Base SQLite introuvable : {db_path}",
                    "field": None,
                    "row_number": None,
                    "details": {},
                }
            ],
        )

    try:
        with get_db_connection(db_path) as connection:
            rows = list_library_rows(connection)
        return rows, None
    except Exception as exc:
        return [], OperationResult(
            success=False,
            operation="LibraryTable",
            result="load_failed",
            path=str(db_path),
            warnings=[],
            errors=[
                {
                    "code": "ERR_LIBRARY_TABLE_LOAD",
                    "severity": "error",
                    "message": str(exc),
                    "field": None,
                    "row_number": None,
                    "details": {},
                }
            ],
        )


def _to_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    if "updated_at" in df.columns:
        df = df.sort_values("updated_at", ascending=False, na_position="last")

    return df.reset_index(drop=True)


def _render_table_toolbar(df: pd.DataFrame) -> pd.DataFrame:
    st.markdown("#### Table")

    if df.empty:
        st.info("Aucune ligne dans `library_rows`.")
        return df

    filters = render_library_filters()
    if isinstance(filters, dict):
        st.session_state[SS_CURRENT_FILTERS] = filters
    else:
        filters = st.session_state.get(SS_CURRENT_FILTERS, {})

    filtered_df = apply_dataframe_filters(df, filters)

    search_text = st.text_input(
        "Recherche rapide",
        value="",
        placeholder="Titre, fichier, UUID, tags, notes...",
    ).strip()

    if search_text:
        haystack_columns = [
            column
            for column in filtered_df.columns
            if filtered_df[column].dtype == "object"
        ]
        mask = pd.Series(False, index=filtered_df.index)

        for column in haystack_columns:
            mask = mask | filtered_df[column].fillna("").astype(str).str.contains(
                search_text,
                case=False,
                regex=False,
            )

        filtered_df = filtered_df[mask]

    col1, col2, col3 = st.columns([1, 1, 2])
    col1.metric("Total", len(df))
    col2.metric("Affiché", len(filtered_df))

    with col3:
        show_protected = st.checkbox(
            "Afficher colonnes techniques",
            value=False,
            help="Affiche les champs protégés comme UUID, hash, chemins et tailles.",
        )

    if show_protected:
        visible_columns = list(filtered_df.columns)
    else:
        visible_columns = [
            column for column in DEFAULT_VISIBLE_COLUMNS if column in filtered_df.columns
        ]

    if not visible_columns:
        visible_columns = list(filtered_df.columns)

    st.dataframe(
        filtered_df[visible_columns],
        use_container_width=True,
        hide_index=True,
    )

    return filtered_df


def _build_row_label(row: dict[str, Any]) -> str:
    title = str(row.get("title") or "(sans titre)")
    filename = str(row.get("filename") or "")
    version_uuid = str(row.get("version_uuid") or "")

    if filename:
        return f"{title} — {filename} — {version_uuid}"

    return f"{title} — {version_uuid}"


def _select_row(filtered_df: pd.DataFrame) -> dict[str, Any] | None:
    st.markdown("#### Sélection")

    if filtered_df.empty:
        st.caption("Aucune ligne à sélectionner.")
        return None

    rows = filtered_df.to_dict(orient="records")
    options = {
        _build_row_label(row): row.get("version_uuid")
        for row in rows
        if row.get("version_uuid")
    }

    if not options:
        st.warning("Aucune ligne sélectionnable : `version_uuid` manquant.")
        return None

    current_version_uuid = st.session_state.get(SS_SELECTED_VERSION_UUID)

    labels = list(options.keys())
    default_index = 0

    if current_version_uuid:
        for index, label in enumerate(labels):
            if options[label] == current_version_uuid:
                default_index = index
                break

    selected_label = st.selectbox(
        "Ligne active",
        labels,
        index=default_index,
    )

    selected_version_uuid = options[selected_label]
    st.session_state[SS_SELECTED_VERSION_UUID] = selected_version_uuid

    for row in rows:
        if row.get("version_uuid") == selected_version_uuid:
            st.session_state[SS_SELECTED_MEDIA_UUID] = row.get("media_uuid")

            selected_path = row.get("storage_path") or row.get("original_path")
            if selected_path:
                st.session_state[SS_SELECTED_FILE_PATH] = selected_path

            return row

    return None


def _reload_selected_row(db_path: Path, version_uuid: str) -> dict[str, Any] | None:
    try:
        with get_db_connection(db_path) as connection:
            return get_library_row_by_version_uuid(connection, version_uuid)
    except Exception:
        return None


def _render_selected_summary(row: dict[str, Any]) -> None:
    title = row.get("title") or "(sans titre)"
    st.markdown(f"#### {title}")

    col1, col2, col3 = st.columns(3)
    col1.caption("version_uuid")
    col1.code(str(row.get("version_uuid") or ""), language=None)

    col2.caption("media_uuid")
    col2.code(str(row.get("media_uuid") or ""), language=None)

    col3.caption("sha256")
    col3.code(str(row.get("sha256") or ""), language=None)

    metadata_columns = [
        "media_type",
        "status",
        "library_scope",
        "uckk_relevance",
        "target_system",
        "public_state",
        "visibility",
        "access_level",
        "rights_status",
        "restriction_state",
        "audience_suitability",
        "canonical_validation_state",
        "ai_validation_state",
        "human_review_required",
        "review_queue",
        "review_reason",
    ]

    summary_data = {
        column: row.get(column)
        for column in metadata_columns
        if column in row
    }

    st.dataframe(
        pd.DataFrame(
            [{"champ": key, "valeur": value} for key, value in summary_data.items()]
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_file_panel(row: dict[str, Any]) -> None:
    st.markdown("#### Fichier")

    path_value = row.get("storage_path") or row.get("original_path")

    if not path_value:
        st.caption("Aucun chemin de fichier disponible.")
        return

    path = Path(str(path_value)).expanduser()

    st.code(str(path), language=None)
    render_file_actions(path)
    render_file_preview(path)


def _render_edit_panel(db_path: Path, row: dict[str, Any]) -> None:
    st.markdown("#### Édition metadata")

    version_uuid = row.get("version_uuid")
    if not version_uuid:
        st.warning("Impossible d’éditer : `version_uuid` manquant.")
        return

    updates = render_row_editor(row)

    if not isinstance(updates, dict):
        updates = {}

    if not updates:
        st.caption("Aucune modification détectée.")
        return

    with st.expander("Modifications proposées", expanded=False):
        st.json(updates)

    if st.button("Enregistrer modifications", type="primary", use_container_width=True):
        try:
            with get_db_connection(db_path) as connection:
                result = update_library_row_by_version_uuid(
                    connection,
                    str(version_uuid),
                    updates,
                    actor="local_user",
                )
            st.session_state[SS_LAST_OPERATION_RESULT] = result
            render_result_messages(result)

            if getattr(result, "success", False):
                st.rerun()
        except Exception as exc:
            result = OperationResult(
                success=False,
                operation="LibraryTableUpdate",
                result="update_failed",
                version_uuid=str(version_uuid),
                warnings=[],
                errors=[
                    {
                        "code": "ERR_LIBRARY_ROW_UPDATE",
                        "severity": "error",
                        "message": str(exc),
                        "field": None,
                        "row_number": None,
                        "details": {},
                    }
                ],
            )
            st.session_state[SS_LAST_OPERATION_RESULT] = result
            render_result_messages(result)


def _render_archive_panel(db_path: Path, row: dict[str, Any]) -> None:
    version_uuid = row.get("version_uuid")
    if not version_uuid:
        return

    with st.expander("Archiver / soft delete", expanded=False):
        st.warning(
            "Cette action doit seulement changer le statut local. "
            "Elle ne doit pas supprimer le fichier physique."
        )

        confirm = st.checkbox(
            "Confirmer l’archivage local de cette ligne",
            key=f"confirm_archive_{version_uuid}",
        )

        if st.button(
            "Archiver la ligne",
            disabled=not confirm,
            use_container_width=True,
        ):
            try:
                with get_db_connection(db_path) as connection:
                    result = soft_delete_library_row(
                        connection,
                        str(version_uuid),
                        actor="local_user",
                    )

                st.session_state[SS_LAST_OPERATION_RESULT] = result
                render_result_messages(result)

                if getattr(result, "success", False):
                    st.rerun()
            except Exception as exc:
                result = OperationResult(
                    success=False,
                    operation="LibraryTableArchive",
                    result="archive_failed",
                    version_uuid=str(version_uuid),
                    warnings=[],
                    errors=[
                        {
                            "code": "ERR_LIBRARY_ROW_ARCHIVE",
                            "severity": "error",
                            "message": str(exc),
                            "field": None,
                            "row_number": None,
                            "details": {},
                        }
                    ],
                )
                st.session_state[SS_LAST_OPERATION_RESULT] = result
                render_result_messages(result)


def _render_export_selection_hint(row: dict[str, Any]) -> None:
    with st.expander("Contexte export", expanded=False):
        export_fields = [
            "export_to_uckk",
            "export_to_public",
            "target_export_allowed",
            "target_system",
            "export_policy_note",
        ]

        export_data = {
            field: row.get(field)
            for field in export_fields
            if field in row
        }

        st.json(export_data)


def render_page() -> None:
    configure_page()

    st.title("Library Table")
    st.caption("Inventaire local `library_rows` — SQLite source de vérité")

    settings = _safe_get_settings()
    db_path = _get_db_path(settings)

    last_result = st.session_state.get(SS_LAST_OPERATION_RESULT)
    render_operation_result(last_result)

    if db_path is None:
        st.warning("Chemin SQLite non configuré.")
        return

    st.caption(f"Base active : `{db_path}`")

    rows, load_result = _load_rows(db_path)
    if load_result is not None:
        render_result_messages(load_result)
        return

    df = _to_dataframe(rows)
    filtered_df = _render_table_toolbar(df)

    st.divider()

    selected_row = _select_row(filtered_df)

    if not selected_row:
        return

    selected_version_uuid = selected_row.get("version_uuid")
    if selected_version_uuid:
        refreshed_row = _reload_selected_row(db_path, str(selected_version_uuid))
        if refreshed_row:
            selected_row = refreshed_row

    st.divider()

    tab_summary, tab_file, tab_edit, tab_policy = st.tabs(
        ["Résumé", "Fichier", "Édition", "Politique export"]
    )

    with tab_summary:
        _render_selected_summary(selected_row)

    with tab_file:
        _render_file_panel(selected_row)

    with tab_edit:
        _render_edit_panel(db_path, selected_row)
        _render_archive_panel(db_path, selected_row)

    with tab_policy:
        _render_export_selection_hint(selected_row)


if __name__ == "__main__":
    render_page()