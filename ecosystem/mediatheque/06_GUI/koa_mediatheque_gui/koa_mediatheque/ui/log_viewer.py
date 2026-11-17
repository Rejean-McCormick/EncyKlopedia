# 06_GUI/koa_mediatheque_gui/koa_mediatheque/ui/log_viewer.py
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any


MAX_LOG_ROWS_DEFAULT = 200
MAX_CELL_PREVIEW_CHARS = 240


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

    try:
        return dict(value)
    except Exception:
        return {}


def _rows_to_dicts(rows: Any, columns: list[str] | None = None) -> list[dict[str, Any]]:
    if not rows:
        return []

    output: list[dict[str, Any]] = []

    for row in rows:
        if isinstance(row, dict):
            output.append(dict(row))
            continue

        if is_dataclass(row):
            output.append(asdict(row))
            continue

        try:
            output.append(dict(row))
            continue
        except Exception:
            pass

        if columns:
            try:
                output.append({columns[index]: row[index] for index in range(len(columns))})
                continue
            except Exception:
                pass

        output.append({"value": str(row)})

    return output


def _execute_select(
    connection: Any,
    sql: str,
    params: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, params)
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description or []]
    return _rows_to_dicts(rows, columns)


def _table_exists(connection: Any, table_name: str) -> bool:
    try:
        rows = _execute_select(
            connection,
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        )
        return bool(rows)
    except Exception:
        return False


def _load_logs_from_repository(
    repository_module: str,
    function_name: str,
    connection: Any,
    **kwargs: Any,
) -> list[dict[str, Any]] | None:
    try:
        module = __import__(repository_module, fromlist=[function_name])
        function = getattr(module, function_name)
        rows = function(connection, **kwargs)
        return _rows_to_dicts(rows)
    except Exception:
        return None


def _safe_json_loads(value: Any) -> Any:
    if value is None:
        return None

    if not isinstance(value, str):
        return value

    text = value.strip()

    if not text:
        return ""

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return value


def _truncate_cell(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value)

    if len(text) <= MAX_CELL_PREVIEW_CHARS:
        return value

    return f"{text[:MAX_CELL_PREVIEW_CHARS]}…"


def _prepare_dataframe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []

    for row in rows:
        prepared.append({key: _truncate_cell(value) for key, value in row.items()})

    return prepared


def _render_dataframe(rows: list[dict[str, Any]], *, key: str) -> None:
    st = _st()

    if not rows:
        st.info("Aucun log.")
        return

    prepared_rows = _prepare_dataframe_rows(rows)

    try:
        import pandas as pd

        df = pd.DataFrame(prepared_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception:
        st.dataframe(prepared_rows, use_container_width=True, hide_index=True)


def _render_log_detail(rows: list[dict[str, Any]], *, key: str, title: str) -> None:
    st = _st()

    if not rows:
        return

    options: list[tuple[str, int]] = []

    for index, row in enumerate(rows):
        row_id = row.get("id", index + 1)
        created_at = row.get("created_at", "")
        action = row.get("action") or row.get("validation_status") or row.get("result") or ""
        version_uuid = row.get("version_uuid", "")

        label_parts = [f"#{row_id}"]

        if created_at:
            label_parts.append(str(created_at))
        if action:
            label_parts.append(str(action))
        if version_uuid:
            label_parts.append(str(version_uuid))

        options.append((" · ".join(label_parts), index))

    selected = st.selectbox(
        f"Détail {title}",
        options=options,
        format_func=lambda option: option[0],
        key=f"{key}_detail_select",
    )

    selected_index = selected[1]
    selected_row = rows[selected_index]

    with st.expander("Détail brut", expanded=False):
        rendered: dict[str, Any] = {}

        for field_name, value in selected_row.items():
            if field_name.endswith("_json") or field_name in {
                "before_json",
                "after_json",
                "data_json",
                "validation_errors",
                "parsed_json",
                "filter_json",
                "changes_json",
            }:
                rendered[field_name] = _safe_json_loads(value)
            else:
                rendered[field_name] = value

        st.json(rendered)


def _render_common_controls(key: str) -> tuple[int, str]:
    st = _st()

    col_limit, col_search = st.columns([1, 3])

    with col_limit:
        limit = st.number_input(
            "Limite",
            min_value=10,
            max_value=5000,
            value=MAX_LOG_ROWS_DEFAULT,
            step=50,
            key=f"{key}_limit",
        )

    with col_search:
        query = st.text_input(
            "Filtrer dans les logs affichés",
            key=f"{key}_query",
            placeholder="UUID, action, fichier, erreur...",
        )

    return int(limit), str(query or "").strip().lower()


def _filter_rows(rows: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    if not query:
        return rows

    parts = [part.strip() for part in query.split() if part.strip()]

    if not parts:
        return rows

    filtered: list[dict[str, Any]] = []

    for row in rows:
        text = json.dumps(row, ensure_ascii=False, sort_keys=True, default=str).lower()

        if all(part in text for part in parts):
            filtered.append(row)

    return filtered


def _render_missing_connection() -> None:
    st = _st()
    st.info("Connexion SQLite indisponible.")


def _render_missing_table(table_name: str) -> None:
    st = _st()
    st.warning(f"Table `{table_name}` introuvable.")


def _load_audit_log(connection: Any, limit: int) -> list[dict[str, Any]]:
    repository_rows = _load_logs_from_repository(
        "koa_mediatheque.repositories.audit_log_repository",
        "list_audit_log",
        connection,
        limit=limit,
    )

    if repository_rows is not None:
        return repository_rows

    if not _table_exists(connection, "audit_log"):
        return []

    return _execute_select(
        connection,
        "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?",
        (limit,),
    )


def _load_chatgpt_intake_log(connection: Any, limit: int) -> list[dict[str, Any]]:
    repository_rows = _load_logs_from_repository(
        "koa_mediatheque.repositories.chatgpt_intake_log_repository",
        "list_chatgpt_intake_log",
        connection,
        limit=limit,
    )

    if repository_rows is not None:
        return repository_rows

    if not _table_exists(connection, "chatgpt_intake_log"):
        return []

    return _execute_select(
        connection,
        """
        SELECT
            id,
            version_uuid,
            file_path,
            validation_status,
            validation_errors,
            created_at,
            prompt_template,
            raw_response,
            parsed_json
        FROM chatgpt_intake_log
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )


def _load_xlsx_import_log(
    connection: Any,
    limit: int,
    import_uuid: str | None = None,
) -> list[dict[str, Any]]:
    repository_rows = _load_logs_from_repository(
        "koa_mediatheque.repositories.xlsx_import_log_repository",
        "list_xlsx_import_log",
        connection,
        import_uuid=import_uuid,
    )

    if repository_rows is not None:
        return repository_rows[:limit]

    if not _table_exists(connection, "xlsx_import_log"):
        return []

    if import_uuid:
        return _execute_select(
            connection,
            """
            SELECT *
            FROM xlsx_import_log
            WHERE import_uuid = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (import_uuid, limit),
        )

    return _execute_select(
        connection,
        "SELECT * FROM xlsx_import_log ORDER BY id DESC LIMIT ?",
        (limit,),
    )


def _load_xlsx_import_uuid_options(connection: Any) -> list[str]:
    if not _table_exists(connection, "xlsx_import_log"):
        return []

    try:
        rows = _execute_select(
            connection,
            """
            SELECT DISTINCT import_uuid
            FROM xlsx_import_log
            WHERE import_uuid IS NOT NULL AND import_uuid != ''
            ORDER BY import_uuid DESC
            LIMIT 500
            """,
        )
        return [str(row["import_uuid"]) for row in rows if row.get("import_uuid")]
    except Exception:
        return []


def render_audit_log(connection: Any) -> None:
    st = _st()

    with _safe_container(border=True):
        st.subheader("Audit log")

        if connection is None:
            _render_missing_connection()
            return

        limit, query = _render_common_controls("koa_audit_log")

        if not _table_exists(connection, "audit_log"):
            _render_missing_table("audit_log")
            return

        try:
            rows = _load_audit_log(connection, limit)
        except Exception as exc:
            st.error(f"Lecture audit_log impossible : {exc}")
            return

        rows = _filter_rows(rows, query)

        col_total, col_filtered = st.columns(2)
        col_total.metric("Lignes affichées", len(rows))
        col_filtered.metric("Limite", limit)

        _render_dataframe(rows, key="koa_audit_log")
        _render_log_detail(rows, key="koa_audit_log", title="audit_log")


def render_chatgpt_intake_log(connection: Any) -> None:
    st = _st()

    with _safe_container(border=True):
        st.subheader("ChatGPT intake log")

        if connection is None:
            _render_missing_connection()
            return

        limit, query = _render_common_controls("koa_chatgpt_intake_log")

        if not _table_exists(connection, "chatgpt_intake_log"):
            _render_missing_table("chatgpt_intake_log")
            return

        try:
            rows = _load_chatgpt_intake_log(connection, limit)
        except Exception as exc:
            st.error(f"Lecture chatgpt_intake_log impossible : {exc}")
            return

        rows = _filter_rows(rows, query)

        status_counts: dict[str, int] = {}

        for row in rows:
            status = str(row.get("validation_status") or "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        col_total, col_status = st.columns([1, 3])
        col_total.metric("Lignes affichées", len(rows))

        with col_status:
            if status_counts:
                st.caption(
                    " · ".join(
                        f"{status}: {count}"
                        for status, count in sorted(status_counts.items())
                    )
                )

        _render_dataframe(rows, key="koa_chatgpt_intake_log")
        _render_log_detail(rows, key="koa_chatgpt_intake_log", title="chatgpt_intake_log")


def render_xlsx_import_log(connection: Any) -> None:
    st = _st()

    with _safe_container(border=True):
        st.subheader("XLSX import log")

        if connection is None:
            _render_missing_connection()
            return

        if not _table_exists(connection, "xlsx_import_log"):
            _render_missing_table("xlsx_import_log")
            return

        limit, query = _render_common_controls("koa_xlsx_import_log")

        import_uuid_options = _load_xlsx_import_uuid_options(connection)

        selected_import_uuid = st.selectbox(
            "import_uuid",
            options=[""] + import_uuid_options,
            format_func=lambda value: "Tous" if value == "" else value,
            key="koa_xlsx_import_log_import_uuid",
        )

        try:
            rows = _load_xlsx_import_log(
                connection,
                limit,
                import_uuid=selected_import_uuid or None,
            )
        except Exception as exc:
            st.error(f"Lecture xlsx_import_log impossible : {exc}")
            return

        rows = _filter_rows(rows, query)

        result_counts: dict[str, int] = {}

        for row in rows:
            result = str(
                row.get("result")
                or row.get("status")
                or row.get("action")
                or "unknown"
            )
            result_counts[result] = result_counts.get(result, 0) + 1

        col_total, col_result = st.columns([1, 3])
        col_total.metric("Lignes affichées", len(rows))

        with col_result:
            if result_counts:
                st.caption(
                    " · ".join(
                        f"{result}: {count}"
                        for result, count in sorted(result_counts.items())
                    )
                )

        _render_dataframe(rows, key="koa_xlsx_import_log")
        _render_log_detail(rows, key="koa_xlsx_import_log", title="xlsx_import_log")