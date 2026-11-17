from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from koa_mediatheque.db import get_db_connection
from koa_mediatheque.services.source_catalog_service import (
    get_source_stats,
    list_source_snapshots,
    list_sources,
)
from koa_mediatheque.ui.layout import configure_page, render_sidebar_settings

PAGE_TITLE = "Sources"
PAGE_ICON = "🔗"


def _db_path(settings: dict) -> Path | None:
    raw = settings.get("db_path") or settings.get("koa_db_path") or st.session_state.get("koa_db_path")
    return Path(str(raw)).expanduser() if raw else None


def render_page() -> None:
    configure_page()
    settings = render_sidebar_settings()
    st.title("Sources")
    st.caption(
        "Autorité Médiathèque : Source → Snapshot → Représentation. "
        "Kristal, EncyK et les autres systèmes restent des consommateurs/bindings."
    )

    db_path = _db_path(settings if isinstance(settings, dict) else {})
    if db_path is None or not db_path.exists():
        st.warning("Configure une base Médiathèque kOA existante dans la barre latérale.")
        return

    with get_db_connection(db_path) as connection:
        stats = get_source_stats(connection)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Consommateurs", stats["consumers"])
        c2.metric("Sources", stats["sources"])
        c3.metric("Snapshots", stats["snapshots"])
        c4.metric("Fichiers physiques", stats["physical_files"])

        inventory = list_sources(connection, limit=5000)
        if not inventory:
            st.info("Aucune source n'est encore enregistrée dans le catalogue commun.")
            st.code(
                "python 05_TOOLS/KoaKristalSources.py import-all --db <db> "
                "--storage-root <02_STORAGE> --root <racine-des-Kristals>",
                language="text",
            )
            return

        systems = sorted({str(row["consumer_system"]) for row in inventory})
        instances = sorted({str(row["consumer_instance"]) for row in inventory})
        statuses = sorted({str(row["status"]) for row in inventory})
        col_a, col_b, col_c, col_d = st.columns([2, 2, 2, 4])
        selected_system = col_a.selectbox("Système", ["Tous", *systems])
        selected_instance = col_b.selectbox("Consommateur", ["Tous", *instances])
        selected_status = col_c.selectbox("Statut", ["Tous", *statuses])
        search = col_d.text_input("Recherche", placeholder="titre, éditeur, URL, source_id…")

        rows = list_sources(
            connection,
            consumer_system=None if selected_system == "Tous" else selected_system,
            consumer_instance=None if selected_instance == "Tous" else selected_instance,
            status=None if selected_status == "Tous" else selected_status,
            search=search or None,
            limit=5000,
        )
        df = pd.DataFrame(rows)
        visible = [
            "consumer_system",
            "consumer_instance",
            "external_source_id",
            "title",
            "publisher",
            "source_kind",
            "status",
            "snapshot_count",
            "available_snapshot_count",
            "representation_count",
            "source_uuid",
        ]
        st.dataframe(
            df[[c for c in visible if c in df.columns]],
            use_container_width=True,
            hide_index=True,
        )

        if rows:
            options = {
                f"{row['consumer_system']}:{row['consumer_instance']} · {row['title']} · "
                f"{row['external_source_id']}": row["source_uuid"]
                for row in rows
            }
            selected = st.selectbox("Détail d'une source", list(options))
            source_uuid = options[selected]
            snapshots = list_source_snapshots(connection, source_uuid)
            st.markdown("#### Snapshots")
            if snapshots:
                snap_df = pd.DataFrame(snapshots)
                snap_cols = [
                    "snapshot_id",
                    "retrieved_at",
                    "status",
                    "http_status",
                    "acquisition_method",
                    "representation_count",
                    "final_url",
                    "error",
                ]
                st.dataframe(
                    snap_df[[c for c in snap_cols if c in snap_df.columns]],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.caption("Source déclarée, pas encore téléchargée.")


if __name__ == "__main__":
    render_page()
