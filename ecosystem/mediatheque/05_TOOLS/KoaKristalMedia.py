#!/usr/bin/env python3
"""CLI for the Médiathèque kOA ↔ Kristal local media bridge."""

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
from koa_mediatheque.services.kristal_media_bridge_service import (  # noqa: E402
    export_kristal_media_bundle,
    link_media_to_kristal,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Link local media to Kristal and export IK-compatible media references."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    link = subparsers.add_parser("link", help="Add a kristal:<kind>:<id> relation to one media version.")
    link.add_argument("--db", required=True, help="Path to koa_mediatheque.sqlite")
    link.add_argument("--version-uuid", required=True)
    link.add_argument("--kind", required=True, help="Relation kind, e.g. state, referent, artifact")
    link.add_argument("--id", required=True, dest="relation_id", help="Kristal identifier")
    link.add_argument("--actor", default="local_user")

    export = subparsers.add_parser(
        "export",
        help="Export all explicitly Kristal-linked media as ArtifactRef + ExportManifest.",
    )
    export.add_argument("--db", required=True, help="Path to koa_mediatheque.sqlite")
    export.add_argument("--output-dir", required=True)
    export.add_argument("--actor", default="local_user")
    export.add_argument("--reason", default="")
    export.add_argument("--producer-instance", default=None)
    export.add_argument("--producer-organization", default=None)

    args = parser.parse_args()
    connection = get_db_connection(args.db)
    try:
        if args.command == "link":
            result = link_media_to_kristal(
                connection,
                args.version_uuid,
                relation_kind=args.kind,
                relation_id=args.relation_id,
                actor=args.actor,
            )
        else:
            result = export_kristal_media_bundle(
                connection,
                args.output_dir,
                actor=args.actor,
                reason=args.reason,
                producer_instance=args.producer_instance,
                producer_organization=args.producer_organization,
            )
    finally:
        connection.close()

    payload = _result_to_json(result)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload.get("success") else 1


def _result_to_json(result: Any) -> dict[str, Any]:
    def message_to_dict(message: Any) -> dict[str, Any]:
        return {
            "code": getattr(message, "code", ""),
            "severity": getattr(message, "severity", ""),
            "message": getattr(message, "message", ""),
            "field": getattr(message, "field", None),
            "row_number": getattr(message, "row_number", None),
            "details": getattr(message, "details", {}) or {},
        }

    return {
        "success": bool(getattr(result, "success", False)),
        "operation": getattr(result, "operation", ""),
        "result": getattr(result, "result", ""),
        "entity_type": getattr(result, "entity_type", None),
        "entity_uuid": getattr(result, "entity_uuid", None),
        "media_uuid": getattr(result, "media_uuid", None),
        "version_uuid": getattr(result, "version_uuid", None),
        "path": getattr(result, "path", None),
        "data": getattr(result, "data", {}) or {},
        "warnings": [message_to_dict(item) for item in getattr(result, "warnings", [])],
        "errors": [message_to_dict(item) for item in getattr(result, "errors", [])],
    }


if __name__ == "__main__":
    raise SystemExit(main())
