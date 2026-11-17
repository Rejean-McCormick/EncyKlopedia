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
from koa_mediatheque.models import FileFacts, KoaMessage, OperationResult
from koa_mediatheque.repositories.library_rows_repository import (
    get_library_row_by_version_uuid,
    get_library_rows_by_sha256,
    list_library_rows,
)
from koa_mediatheque.services.file_facts import get_file_facts, is_external_reference_path
from koa_mediatheque.ui.file_preview import render_file_actions, render_file_preview
from koa_mediatheque.ui.layout import (
    configure_page,
    render_operation_result,
    render_sidebar_settings,
)
from koa_mediatheque.ui.widgets import render_result_messages


PAGE_TITLE = "File Preview"

SS_DB_PATH = "koa_db_path"
SS_SELECTED_VERSION_UUID = "koa_selected_version_uuid"
SS_SELECTED_MEDIA_UUID = "koa_selected_media_uuid"
SS_SELECTED_FILE_PATH = "koa_selected_file_path"
SS_LAST_OPERATION_RESULT = "koa_last_operation_result"


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
    version_uuid: str | None = None,
) -> OperationResult:
    return OperationResult(
        success=False,
        operation=operation,
        result=result,
        version_uuid=version_uuid,
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


def _load_library_rows(db_path: Path) -> list[dict[str, Any]]:
    try:
        with get_db_connection(db_path) as connection:
            return list_library_rows(connection)
    except Exception:
        return []


def _load_selected_row(db_path: Path, version_uuid: str | None) -> dict[str, Any] | None:
    if not version_uuid:
        return None

    try:
        with get_db_connection(db_path) as connection:
            return get_library_row_by_version_uuid(connection, version_uuid)
    except Exception:
        return None


def _build_row_label(row: dict[str, Any]) -> str:
    title = str(row.get("title") or "(sans titre)")
    filename = str(row.get("filename") or "")
    version_uuid = str(row.get("version_uuid") or "")

    if filename:
        return f"{title} — {filename} — {version_uuid}"

    return f"{title} — {version_uuid}"


def _resolve_path_from_row(row: dict[str, Any] | None) -> str | None:
    if not row:
        return None

    path_value = row.get("storage_path") or row.get("original_path")
    if not path_value:
        return None

    return str(path_value)


def _render_row_selector(db_path: Path) -> dict[str, Any] | None:
    rows = _load_library_rows(db_path)

    if not rows:
        st.caption("Aucune ligne disponible dans `library_rows`.")
        return None

    options: dict[str, str] = {
        _build_row_label(row): str(row["version_uuid"])
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
        "Sélectionner une ligne",
        labels,
        index=default_index,
    )

    selected_version_uuid = options[selected_label]
    st.session_state[SS_SELECTED_VERSION_UUID] = selected_version_uuid

    row = _load_selected_row(db_path, selected_version_uuid)

    if row:
        st.session_state[SS_SELECTED_MEDIA_UUID] = row.get("media_uuid")
        selected_path = _resolve_path_from_row(row)
        if selected_path:
            st.session_state[SS_SELECTED_FILE_PATH] = selected_path

    return row


def _render_manual_path_input() -> str | None:
    current_path = str(st.session_state.get(SS_SELECTED_FILE_PATH) or "")

    manual_path = st.text_input(
        "Chemin manuel",
        value=current_path,
        placeholder="Coller un chemin local à prévisualiser",
    ).strip()

    if manual_path:
        st.session_state[SS_SELECTED_FILE_PATH] = manual_path
        return manual_path

    return None


def _safe_get_file_facts(path: Path) -> tuple[FileFacts | None, OperationResult | None]:
    if is_external_reference_path(str(path)):
        return None, OperationResult(
            success=True,
            operation="FilePreview",
            result="external_reference",
            path=str(path),
            warnings=[
                KoaMessage(
                    code="WARN_EXTERNAL_REFERENCE",
                    severity="warning",
                    message="Le chemin semble être une référence externe. Aucun fait technique local n’est recalculé.",
                )
            ],
            errors=[],
        )

    if not path.exists():
        return None, _make_error_result(
            operation="FilePreview",
            result="file_not_found",
            code="ERR_FILE_NOT_FOUND",
            message=f"Fichier introuvable : {path}",
            path=str(path),
        )

    if not path.is_file():
        return None, _make_error_result(
            operation="FilePreview",
            result="not_a_file",
            code="ERR_FILE_NOT_FOUND",
            message=f"Le chemin ne pointe pas vers un fichier : {path}",
            path=str(path),
        )

    try:
        return get_file_facts(path), None
    except Exception as exc:
        return None, _make_error_result(
            operation="FilePreview",
            result="file_facts_failed",
            code="ERR_FILE_FACTS",
            message=str(exc),
            path=str(path),
        )


def _render_file_facts(facts: FileFacts | None) -> None:
    st.markdown("#### Faits techniques locaux")

    if facts is None:
        st.caption("Aucun fait technique local disponible.")
        return

    data = {
        "original_path": facts.original_path,
        "filename": facts.filename,
        "extension": facts.extension,
        "mimetype": facts.mimetype,
        "filesize": facts.filesize,
        "sha256": facts.sha256,
    }

    st.dataframe(
        pd.DataFrame(
            [{"champ": key, "valeur": value} for key, value in data.items()]
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_catalog_row(row: dict[str, Any] | None) -> None:
    st.markdown("#### Ligne catalogue liée")

    if row is None:
        st.caption("Aucune ligne `library_rows` liée à cette prévisualisation.")
        return

    col1, col2, col3 = st.columns(3)

    col1.caption("version_uuid")
    col1.code(str(row.get("version_uuid") or ""), language=None)

    col2.caption("media_uuid")
    col2.code(str(row.get("media_uuid") or ""), language=None)

    col3.caption("status")
    col3.code(str(row.get("status") or ""), language=None)

    fields = [
        "title",
        "filename",
        "media_type",
        "filearea",
        "public_state",
        "visibility",
        "access_level",
        "rights_status",
        "restriction_state",
        "audience_suitability",
        "canonical_validation_state",
        "human_review_required",
        "review_queue",
        "review_reason",
        "storage_path",
        "original_path",
    ]

    data = {
        field: row.get(field)
        for field in fields
        if field in row
    }

    st.dataframe(
        pd.DataFrame(
            [{"champ": key, "valeur": value} for key, value in data.items()]
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_duplicate_panel(db_path: Path | None, facts: FileFacts | None) -> None:
    st.markdown("#### Doublons exacts")

    if db_path is None or facts is None or not facts.sha256:
        st.caption("Aucun hash disponible pour la recherche de doublons.")
        return

    try:
        with get_db_connection(db_path) as connection:
            duplicates = get_library_rows_by_sha256(connection, facts.sha256)
    except Exception as exc:
        render_result_messages(
            _make_error_result(
                operation="FilePreviewDuplicates",
                result="duplicate_lookup_failed",
                code="ERR_DUPLICATE_LOOKUP",
                message=str(exc),
            )
        )
        return

    if not duplicates:
        st.caption("Aucune ligne existante avec le même `sha256`.")
        return

    df = pd.DataFrame(duplicates)

    columns = [
        "title",
        "filename",
        "version_uuid",
        "media_uuid",
        "status",
        "storage_path",
        "original_path",
    ]
    visible_columns = [column for column in columns if column in df.columns]

    st.warning(f"{len(duplicates)} ligne(s) avec le même `sha256`.")
    st.dataframe(
        df[visible_columns],
        use_container_width=True,
        hide_index=True,
    )


def _render_preview(path_value: str | None) -> None:
    st.markdown("#### Prévisualisation")

    if not path_value:
        st.caption("Aucun fichier sélectionné.")
        return

    path = Path(path_value).expanduser()
    st.code(str(path), language=None)

    render_file_actions(path)
    render_file_preview(path)


def render_page() -> None:
    configure_page()

    st.title("File Preview")
    st.caption("Prévisualisation locale des fichiers liés à `library_rows`")

    settings = _safe_get_settings()
    db_path = _get_db_path(settings)

    last_result = st.session_state.get(SS_LAST_OPERATION_RESULT)
    render_operation_result(last_result)

    tab_catalog, tab_manual = st.tabs(["Depuis la table", "Chemin manuel"])

    selected_row: dict[str, Any] | None = None
    selected_path: str | None = None

    with tab_catalog:
        if db_path is None:
            st.warning("Chemin SQLite non configuré.")
        elif not db_path.exists():
            render_result_messages(
                _make_error_result(
                    operation="FilePreview",
                    result="db_not_found",
                    code="ERR_DB_NOT_FOUND",
                    message=f"Base SQLite introuvable : {db_path}",
                    path=str(db_path),
                )
            )
        else:
            st.caption(f"Base active : `{db_path}`")
            selected_row = _render_row_selector(db_path)
            selected_path = _resolve_path_from_row(selected_row)

    with tab_manual:
        manual_path = _render_manual_path_input()
        if manual_path:
            selected_path = manual_path
            selected_row = None

    if selected_path:
        st.session_state[SS_SELECTED_FILE_PATH] = selected_path

    st.divider()

    path_obj = Path(selected_path).expanduser() if selected_path else None
    facts: FileFacts | None = None

    if path_obj is not None:
        facts, facts_result = _safe_get_file_facts(path_obj)
        if facts_result is not None:
            render_result_messages(facts_result)

    left, right = st.columns([1, 1])

    with left:
        _render_catalog_row(selected_row)
        _render_file_facts(facts)

    with right:
        _render_preview(selected_path)

    st.divider()

    _render_duplicate_panel(db_path, facts)


if __name__ == "__main__":
    render_page()