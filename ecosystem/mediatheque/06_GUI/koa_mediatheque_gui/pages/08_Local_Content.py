\
from __future__ import annotations
import os, sys
from pathlib import Path

from koa_mediatheque.workspace import get_workspace_paths
import pandas as pd
import streamlit as st
APP_DIR=Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path: sys.path.insert(0,str(APP_DIR))
from koa_mediatheque.db import get_db_connection
from koa_mediatheque.services.local_workspace_service import load_local_workspace_config, plan_local_workspace, apply_local_workspace
from koa_mediatheque.ui.layout import configure_page, render_sidebar_settings

def render_page()->None:
    configure_page(); settings=render_sidebar_settings(); st.title("Contenu local")
    st.caption("Charge des Kristals et documents locaux sans les embarquer dans la distribution. Les documents sont indexés par référence et restent privés par défaut.")
    default=os.environ.get("KOA_PRIVATE_WORKSPACE_CONFIG", str(get_workspace_paths().config_path))
    cfg_path=st.text_input("Configuration privée",value=default)
    try: cfg=load_local_workspace_config(cfg_path); plan=plan_local_workspace(cfg)
    except Exception as exc: st.info(f"Configuration non chargée: {exc}"); return
    c1,c2=st.columns(2); c1.metric("Kristals",plan["kristal_count"]); c2.metric("Documents",plan["document_count"])
    if plan["kristals"]: st.dataframe(pd.DataFrame(plan["kristals"]),use_container_width=True,hide_index=True)
    db_raw=(settings or {}).get("db_path") or (settings or {}).get("koa_db_path") or st.session_state.get("koa_db_path")
    if st.button("Indexer ce workspace",type="primary"):
        db=Path(str(db_raw)).expanduser() if db_raw else None
        if not db or not db.exists(): st.error("Initialise d’abord la base SQLite."); return
        connection=get_db_connection(db)
        try: result=apply_local_workspace(connection,cfg)
        finally: connection.close()
        st.success("Workspace indexé."); st.json(result)
if __name__=="__main__": render_page()
