from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from koa_mediatheque.db import get_db_connection
from koa_mediatheque.services.kristal_source_library_service import (
    get_kristal_source_stats,
    list_kristal_sources,
    list_source_snapshots,
)
from koa_mediatheque.ui.layout import configure_page, render_sidebar_settings

PAGE_TITLE = "Sources Kristal"
PAGE_ICON = "🔗"


def _db_path(settings: dict) -> Path | None:
    raw = settings.get("db_path") or settings.get("koa_db_path") or st.session_state.get("koa_db_path")
    return Path(str(raw)).expanduser() if raw else None


def render_page() -> None:
    configure_page()
    settings = render_sidebar_settings()
    st.title("Sources locales liées aux Kristals")
    st.caption(
        "Catalogue logique partagé : Kristal → Source → Snapshot → Représentation. "
        "Les fichiers physiques restent dans library_rows et sont dédupliqués par SHA-256."
    )

    db_path = _db_path(settings if isinstance(settings, dict) else {})
    if db_path is None or not db_path.exists():
        st.warning("Configure une base Médiathèque kOA existante dans la barre latérale.")
        return

    with get_db_connection(db_path) as connection:
        stats = get_kristal_source_stats(connection)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Kristals", stats["kristals"])
        c2.metric("Sources", stats["sources"])
        c3.metric("Snapshots", stats["snapshots"])
        c4.metric("Fichiers physiques", stats["physical_files"])

        inventory = list_kristal_sources(connection, limit=5000)
        if not inventory:
            st.info("Aucune source Kristal importée pour le moment.")
            st.code(
                "python 05_TOOLS/KoaKristalSources.py import-all --db <db> "
                "--storage-root <02_STORAGE> --root <racine-des-Kristals>",
                language="text",
            )
            return

        kristals = sorted({str(row["kristal_id"]) for row in inventory})
        statuses = sorted({str(row["status"]) for row in inventory})
        col_a, col_b, col_c = st.columns([2, 2, 4])
        selected_kristal = col_a.selectbox("Kristal", ["Tous", *kristals])
        selected_status = col_b.selectbox("Statut", ["Tous", *statuses])
        search = col_c.text_input("Recherche", placeholder="titre, éditeur, URL, source_id…")

        rows = list_kristal_sources(
            connection,
            kristal_id=None if selected_kristal == "Tous" else selected_kristal,
            status=None if selected_status == "Tous" else selected_status,
            search=search or None,
            limit=5000,
        )
        df = pd.DataFrame(rows)
        visible = [
            "kristal_id", "source_id", "title", "publisher", "source_kind", "status",
            "role", "evidence_class", "authority_class", "category", "priority",
            "snapshot_count", "available_snapshot_count", "representation_count", "source_uuid",
        ]
        st.dataframe(df[[c for c in visible if c in df.columns]], use_container_width=True, hide_index=True)

        if rows:
            options = {
                f"{row['kristal_id']} · {row['title']} · {row['source_id']}": row["source_uuid"]
                for row in rows
            }
            selected = st.selectbox("Détail d'une source", list(options))
            source_uuid = options[selected]
            snapshots = list_source_snapshots(connection, source_uuid)
            st.markdown("#### Snapshots")
            if snapshots:
                snap_df = pd.DataFrame(snapshots)
                snap_cols = [
                    "snapshot_id", "retrieved_at", "status", "http_status", "acquisition_method",
                    "representation_count", "final_url", "error",
                ]
                st.dataframe(snap_df[[c for c in snap_cols if c in snap_df.columns]], use_container_width=True, hide_index=True)
            else:
                st.caption("Source déclarée, pas encore téléchargée.")


if __name__ == "__main__":
    render_page()
