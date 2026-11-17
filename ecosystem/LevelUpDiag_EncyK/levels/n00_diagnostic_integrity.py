from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
from levelupdiag_core.manifest import load_manifest


def run(cfg, report):
    tool = Path(cfg["_tool_root"])
    if sys.version_info >= (3,10):
        report.add("diagnostics.python.version", "PASS", "diagnostics", f"Python {sys.version.split()[0]} is supported.")
    else:
        report.add("diagnostics.python.version", "CONFIG_ERROR", "diagnostics", f"Python {sys.version.split()[0]} is unsupported.", recommendation="Use Python 3.10 or newer.")
    manifest = load_manifest(tool)
    missing = []
    for meta in manifest["levels"]:
        if importlib.util.find_spec(meta["module"]) is None:
            missing.append(meta["module"])
    if missing:
        report.add("diagnostics.level_modules.available", "CONFIG_ERROR", "diagnostics", "One or more declared level modules are missing.", evidence=missing)
    else:
        report.add("diagnostics.level_modules.available", "PASS", "diagnostics", "All declared level modules are importable.", evidence={"count":len(manifest["levels"])})
    schema_dir = tool / "schemas"
    required = [schema_dir/"report.schema.json", schema_dir/"campaign-summary.schema.json"]
    absent = [str(p.name) for p in required if not p.exists()]
    report.add("diagnostics.schemas.present", "CONFIG_ERROR" if absent else "PASS", "diagnostics",
               "Required schema documents are present." if not absent else "Required schema documents are missing.", evidence=absent or {"count":len(required)})
