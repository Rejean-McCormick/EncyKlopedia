#!/usr/bin/env python3
"""CLI for shared Kristal local-source management in Médiathèque kOA."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GUI_ROOT = PROJECT_ROOT / "06_GUI" / "koa_mediatheque_gui"
if str(GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(GUI_ROOT))

from koa_mediatheque.db import get_db_connection  # noqa: E402
from koa_mediatheque.services.kristal_source_library_service import (  # noqa: E402
    discover_kristal_source_stores,
    discover_source_library_candidates,
    ensure_kristal_source_schema,
    export_kristal_bindings,
    get_kristal_source_stats,
    import_discovered_kristal_stores,
    import_kristal_source_store,
    list_kristal_sources,
    plan_kristal_source_store,
    verify_kristal_source_storage,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Classer, migrer et gérer les sources locales liées aux Kristals dans Médiathèque kOA."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    discover = sub.add_parser("discover", help="Découvrir les librairies de sources Kristal.")
    discover.add_argument("--root", required=True, help="Racine contenant les dossiers Kristal-*")
    discover.add_argument("--include-candidates", action="store_true")

    plan = sub.add_parser("plan", help="Planifier l'import d'un source-store.json sans écrire.")
    plan.add_argument("--store", required=True)
    plan.add_argument("--show-files", action="store_true")

    init = sub.add_parser("init", help="Ajouter les tables de gestion Kristal à une DB existante.")
    init.add_argument("--db", required=True)

    one = sub.add_parser("import-store", help="Importer une librairie Kristal canonique.")
    one.add_argument("--db", required=True)
    one.add_argument("--storage-root", required=True)
    one.add_argument("--store", required=True)

    all_cmd = sub.add_parser("import-all", help="Importer toutes les librairies canoniques découvertes.")
    all_cmd.add_argument("--db", required=True)
    all_cmd.add_argument("--storage-root", required=True)
    all_cmd.add_argument("--root", required=True)

    status = sub.add_parser("status", help="Afficher les statistiques et le catalogue des sources.")
    status.add_argument("--db", required=True)
    status.add_argument("--kristal", default=None)
    status.add_argument("--source-status", default=None)
    status.add_argument("--search", default=None)
    status.add_argument("--limit", type=int, default=200)

    verify = sub.add_parser("verify", help="Vérifier existence et SHA-256 des fichiers partagés.")
    verify.add_argument("--db", required=True)

    export = sub.add_parser("export-bindings", help="Exporter les pointeurs source→Médiathèque par Kristal.")
    export.add_argument("--db", required=True)
    export.add_argument("--output-dir", required=True)
    export.add_argument("--kristal", default=None)

    args = parser.parse_args()

    if args.command == "discover":
        payload: dict[str, Any] = {"stores": discover_kristal_source_stores(args.root)}
        if args.include_candidates:
            payload["candidates"] = discover_source_library_candidates(args.root)
        print(_json(payload))
        return 0

    if args.command == "plan":
        payload = plan_kristal_source_store(args.store)
        if not args.show_files:
            payload = {key: value for key, value in payload.items() if key != "files"}
        print(_json(payload))
        return 0 if payload.get("missing_files", 0) == 0 else 2

    connection = get_db_connection(args.db)
    try:
        if args.command == "init":
            ensure_kristal_source_schema(connection)
            print(_json({"success": True, "stats": get_kristal_source_stats(connection)}))
            return 0

        if args.command == "import-store":
            result = import_kristal_source_store(connection, args.store, args.storage_root)
            print(_json(_result_to_dict(result)))
            return 0 if result.success else 1

        if args.command == "import-all":
            results = import_discovered_kristal_stores(connection, args.root, args.storage_root)
            payload = {
                "success": all(item.success for item in results),
                "results": [_result_to_dict(item) for item in results],
                "stats": get_kristal_source_stats(connection),
            }
            print(_json(payload))
            return 0 if payload["success"] else 1

        if args.command == "status":
            payload = {
                "stats": get_kristal_source_stats(connection),
                "sources": list_kristal_sources(
                    connection,
                    kristal_id=args.kristal,
                    status=args.source_status,
                    search=args.search,
                    limit=args.limit,
                ),
            }
            print(_json(payload))
            return 0

        if args.command == "verify":
            payload = verify_kristal_source_storage(connection)
            print(_json(payload))
            return 0 if payload["ok"] else 1

        if args.command == "export-bindings":
            paths = export_kristal_bindings(
                connection,
                args.output_dir,
                kristal_id=args.kristal,
            )
            print(_json({"success": True, "files": paths}))
            return 0
    finally:
        connection.close()

    return 2


def _result_to_dict(result: Any) -> dict[str, Any]:
    return {
        "success": bool(result.success),
        "operation": result.operation,
        "result": result.result,
        "entity_type": result.entity_type,
        "entity_uuid": result.entity_uuid,
        "path": result.path,
        "data": result.data,
        "warnings": [_message_to_dict(item) for item in result.warnings],
        "errors": [_message_to_dict(item) for item in result.errors],
    }


def _message_to_dict(message: Any) -> dict[str, Any]:
    return {
        "code": getattr(message, "code", ""),
        "severity": getattr(message, "severity", ""),
        "message": getattr(message, "message", ""),
        "details": getattr(message, "details", {}) or {},
    }


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


if __name__ == "__main__":
    raise SystemExit(main())
