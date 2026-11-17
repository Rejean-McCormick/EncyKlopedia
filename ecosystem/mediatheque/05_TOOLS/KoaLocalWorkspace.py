#!/usr/bin/env python3
"""Plan/apply the adjacent Médiathèque content workspace."""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path

PROJECT_ROOT=Path(__file__).resolve().parents[1]
GUI_ROOT=PROJECT_ROOT/"06_GUI"/"koa_mediatheque_gui"
if str(GUI_ROOT) not in sys.path: sys.path.insert(0,str(GUI_ROOT))
from koa_mediatheque.db import get_db_connection, initialize_database
from koa_mediatheque.services.local_workspace_service import load_local_workspace_config, plan_local_workspace, apply_local_workspace
from koa_mediatheque.workspace import ensure_content_directories, get_workspace_paths


def main()->int:
    paths=get_workspace_paths(PROJECT_ROOT)
    parser=argparse.ArgumentParser(description="Configure/indexe le contenu local adjacent de Médiathèque kOA.")
    sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("plan"); p.add_argument("--config",default=str(paths.config_path)); p.add_argument("--show-files",action="store_true")
    a=sub.add_parser("apply"); a.add_argument("--config",default=str(paths.config_path)); a.add_argument("--db",default=str(paths.db_path)); a.add_argument("--init-db",action="store_true")
    args=parser.parse_args(); cfg=load_local_workspace_config(args.config)
    if args.command=="plan":
        data=plan_local_workspace(cfg)
        if not args.show_files: data.pop("documents",None)
        print(json.dumps(data,ensure_ascii=False,indent=2)); return 0
    ensure_content_directories(paths)
    db=Path(args.db).expanduser().resolve()
    if args.init_db and not db.exists():
        result=initialize_database(db,paths.schema_dir)
        if not result.success:
            print(json.dumps({"success":False,"result":result.result},ensure_ascii=False)); return 1
    if not db.exists():
        print(json.dumps({"success":False,"error":"database_not_found","db":str(db)},ensure_ascii=False)); return 2
    connection=get_db_connection(db)
    try: data=apply_local_workspace(connection,cfg)
    finally: connection.close()
    print(json.dumps({"success":True,**data},ensure_ascii=False,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
