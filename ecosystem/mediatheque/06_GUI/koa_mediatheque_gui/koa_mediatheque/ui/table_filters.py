# 06_GUI/koa_mediatheque_gui/koa_mediatheque/ui/table_filters.py
from __future__ import annotations

import json
from typing import Any


SS_CURRENT_FILTERS = "koa_current_filters"


FALLBACK_MEDIA_STATUS_VALUES = [
    "draft",
    "submitted",
    "active",
    "restricted",
    "superseded",
    "archived",
    "deleted_soft",
]

FALLBACK_MEDIA_TYPE_VALUES = [
    "document",
    "pdf",
    "image",
    "audio",
    "video",
    "transcript",
    "spreadsheet",
    "presentation",
    "source_package",
    "external_reference",
    "other",
]

FALLBACK_VISIBILITY_VALUES = [
    "private",
    "user",
    "group",
    "course",
    "cohort",
    "program",
    "institution",
    "public",
    "restricted",
    "restricted_integrity",
    "restricted_cultural",
]

FALLBACK_PUBLIC_STATE_VALUES = [
    "public",
    "non_public",
    "private",
    "restricted",
    "confidential",
    "unknown",
]

FALLBACK_UCKK_RELEVANCE_VALUES = [
    "uckk_core",
    "uckk_related",
    "uckk_reference",
    "not_uckk",
    "unknown",
]

FALLBACK_CANONICAL_VALIDATION_VALUES = [
    "unverified",
    "human_reviewed",
    "verified",
    "contested",
    "invalidated",
    "archived",
]

FALLBACK_LOCAL_AI_VALIDATION_VALUES = [
    "ai_validated",
    "ai_classified_needs_review",
    "ai_uncertain",
    "ai_rejected",
]

FALLBACK_EXPORT_DECISION_VALUES = [
    "yes",
    "no",
    "maybe",
    "review_required",
]


def _st():
    import streamlit as st

    return st


def _load_constant_list(name: str, fallback: list[str]) -> list[str]:
    try:
        from koa_mediatheque import constants

        value = getattr(constants, name, fallback)
    except Exception:
        value = fallback

    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]

    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]

    return fallback


def _safe_columns(df: Any) -> list[str]:
    try:
        return [str(column) for column in list(df.columns)]
    except Exception:
        return []


def _has_column(df: Any, column: str) -> bool:
    return column in _safe_columns(df)


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, (list, tuple, set)):
        return "; ".join(str(item) for item in value)

    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    return str(value)


def _filter_in_values(df: Any, column: str, values: list[str]) -> Any:
    if not values or not _has_column(df, column):
        return df

    try:
        return df[df[column].fillna("").astype(str).isin(values)]
    except Exception:
        return df


def _filter_boolean_int(df: Any, column: str, value: str) -> Any:
    if value == "all" or not _has_column(df, column):
        return df

    expected = 1 if value == "yes" else 0

    try:
        numeric = df[column].fillna(0).astype(int)
        return df[numeric == expected]
    except Exception:
        try:
            text = df[column].fillna("").astype(str).str.lower()
            yes_values = {"1", "true", "yes", "oui"}
            no_values = {"0", "false", "no", "non", ""}

            if expected == 1:
                return df[text.isin(yes_values)]
            return df[text.isin(no_values)]
        except Exception:
            return df


def _filter_contains_text(df: Any, query: str, columns: list[str]) -> Any:
    if not query:
        return df

    available_columns = [column for column in columns if _has_column(df, column)]

    if not available_columns:
        return df

    query_parts = [part.strip().lower() for part in query.split() if part.strip()]

    if not query_parts:
        return df

    try:
        mask = None

        for column in available_columns:
            column_text = df[column].fillna("").map(_normalize_text).str.lower()

            column_mask = column_text.apply(
                lambda value: all(query_part in value for query_part in query_parts)
            )

            mask = column_mask if mask is None else (mask | column_mask)

        if mask is None:
            return df

        return df[mask]
    except Exception:
        return df


def _filter_date_range(
    df: Any,
    column: str,
    date_from: Any,
    date_to: Any,
) -> Any:
    if not _has_column(df, column):
        return df

    if not date_from and not date_to:
        return df

    try:
        import pandas as pd

        values = pd.to_datetime(df[column], errors="coerce", utc=True)

        filtered = df

        if date_from:
            start = pd.to_datetime(str(date_from), errors="coerce", utc=True)
            if not pd.isna(start):
                filtered = filtered[values >= start]

        if date_to:
            end = pd.to_datetime(str(date_to), errors="coerce", utc=True)
            if not pd.isna(end):
                end = end + pd.Timedelta(days=1)
                filtered = filtered[values < end]

        return filtered
    except Exception:
        return df


def render_library_filters() -> dict[str, Any]:
    st = _st()

    st.session_state.setdefault(SS_CURRENT_FILTERS, {})

    media_status_values = _load_constant_list(
        "MEDIA_STATUS_VALUES",
        FALLBACK_MEDIA_STATUS_VALUES,
    )
    media_type_values = _load_constant_list(
        "MEDIA_TYPE_VALUES",
        FALLBACK_MEDIA_TYPE_VALUES,
    )
    visibility_values = _load_constant_list(
        "VISIBILITY_VALUES",
        FALLBACK_VISIBILITY_VALUES,
    )
    public_state_values = _load_constant_list(
        "PUBLIC_STATE_VALUES",
        FALLBACK_PUBLIC_STATE_VALUES,
    )
    uckk_relevance_values = _load_constant_list(
        "UCKK_RELEVANCE_VALUES",
        FALLBACK_UCKK_RELEVANCE_VALUES,
    )
    canonical_validation_values = _load_constant_list(
        "CANONICAL_VALIDATION_VALUES",
        FALLBACK_CANONICAL_VALIDATION_VALUES,
    )
    local_ai_validation_values = _load_constant_list(
        "LOCAL_AI_VALIDATION_VALUES",
        FALLBACK_LOCAL_AI_VALIDATION_VALUES,
    )
    export_decision_values = _load_constant_list(
        "EXPORT_DECISION_VALUES",
        FALLBACK_EXPORT_DECISION_VALUES,
    )

    with st.expander("Filtres", expanded=True):
        query = st.text_input(
            "Recherche",
            key="koa_filter_query",
            placeholder="Titre, description, fichier, UUID, tags...",
        )

        col_left, col_right = st.columns(2)

        with col_left:
            status = st.multiselect(
                "Statut",
                options=media_status_values,
                key="koa_filter_status",
            )
            media_type = st.multiselect(
                "Type média",
                options=media_type_values,
                key="koa_filter_media_type",
            )
            visibility = st.multiselect(
                "Visibilité",
                options=visibility_values,
                key="koa_filter_visibility",
            )
            public_state = st.multiselect(
                "État public",
                options=public_state_values,
                key="koa_filter_public_state",
            )
            uckk_relevance = st.multiselect(
                "Pertinence UCKK",
                options=uckk_relevance_values,
                key="koa_filter_uckk_relevance",
            )

        with col_right:
            canonical_validation_state = st.multiselect(
                "Validation canonique",
                options=canonical_validation_values,
                key="koa_filter_canonical_validation_state",
            )
            ai_validation_state = st.multiselect(
                "Validation IA locale",
                options=local_ai_validation_values,
                key="koa_filter_ai_validation_state",
            )
            export_to_uckk = st.multiselect(
                "Export UCKK",
                options=export_decision_values,
                key="koa_filter_export_to_uckk",
            )
            export_to_public = st.multiselect(
                "Export public",
                options=export_decision_values,
                key="koa_filter_export_to_public",
            )
            human_review_required = st.selectbox(
                "Revue humaine requise",
                options=[
                    ("all", "Tous"),
                    ("yes", "Oui"),
                    ("no", "Non"),
                ],
                format_func=lambda option: option[1],
                key="koa_filter_human_review_required",
            )[0]

        col_dates_left, col_dates_right, col_reset = st.columns([1, 1, 1])

        with col_dates_left:
            updated_from = st.date_input(
                "Mis à jour depuis",
                value=None,
                key="koa_filter_updated_from",
            )

        with col_dates_right:
            updated_to = st.date_input(
                "Mis à jour jusqu'à",
                value=None,
                key="koa_filter_updated_to",
            )

        with col_reset:
            st.write("")
            st.write("")
            if st.button("Réinitialiser les filtres", use_container_width=True):
                for key in [
                    "koa_filter_query",
                    "koa_filter_status",
                    "koa_filter_media_type",
                    "koa_filter_visibility",
                    "koa_filter_public_state",
                    "koa_filter_uckk_relevance",
                    "koa_filter_canonical_validation_state",
                    "koa_filter_ai_validation_state",
                    "koa_filter_export_to_uckk",
                    "koa_filter_export_to_public",
                    "koa_filter_human_review_required",
                    "koa_filter_updated_from",
                    "koa_filter_updated_to",
                ]:
                    st.session_state.pop(key, None)

                st.session_state[SS_CURRENT_FILTERS] = {}
                st.rerun()

    filters: dict[str, Any] = {
        "query": query.strip(),
        "status": status,
        "media_type": media_type,
        "visibility": visibility,
        "public_state": public_state,
        "uckk_relevance": uckk_relevance,
        "canonical_validation_state": canonical_validation_state,
        "ai_validation_state": ai_validation_state,
        "export_to_uckk": export_to_uckk,
        "export_to_public": export_to_public,
        "human_review_required": human_review_required,
        "updated_from": updated_from,
        "updated_to": updated_to,
    }

    st.session_state[SS_CURRENT_FILTERS] = filters
    return filters


def apply_dataframe_filters(df: Any, filters: dict[str, Any]) -> Any:
    if df is None:
        return df

    if not filters:
        return df

    filtered = df

    filtered = _filter_contains_text(
        filtered,
        str(filters.get("query") or "").strip(),
        [
            "title",
            "subtitle",
            "description",
            "summary",
            "filename",
            "original_path",
            "storage_path",
            "media_uuid",
            "version_uuid",
            "sha256",
            "collections_json",
            "tags_json",
            "relations_json",
            "content_flags_json",
            "notes",
        ],
    )

    filtered = _filter_in_values(
        filtered,
        "status",
        [str(value) for value in filters.get("status") or []],
    )
    filtered = _filter_in_values(
        filtered,
        "media_type",
        [str(value) for value in filters.get("media_type") or []],
    )
    filtered = _filter_in_values(
        filtered,
        "visibility",
        [str(value) for value in filters.get("visibility") or []],
    )
    filtered = _filter_in_values(
        filtered,
        "public_state",
        [str(value) for value in filters.get("public_state") or []],
    )
    filtered = _filter_in_values(
        filtered,
        "uckk_relevance",
        [str(value) for value in filters.get("uckk_relevance") or []],
    )
    filtered = _filter_in_values(
        filtered,
        "canonical_validation_state",
        [str(value) for value in filters.get("canonical_validation_state") or []],
    )
    filtered = _filter_in_values(
        filtered,
        "ai_validation_state",
        [str(value) for value in filters.get("ai_validation_state") or []],
    )
    filtered = _filter_in_values(
        filtered,
        "export_to_uckk",
        [str(value) for value in filters.get("export_to_uckk") or []],
    )
    filtered = _filter_in_values(
        filtered,
        "export_to_public",
        [str(value) for value in filters.get("export_to_public") or []],
    )

    filtered = _filter_boolean_int(
        filtered,
        "human_review_required",
        str(filters.get("human_review_required") or "all"),
    )

    filtered = _filter_date_range(
        filtered,
        "updated_at",
        filters.get("updated_from"),
        filters.get("updated_to"),
    )

    return filtered