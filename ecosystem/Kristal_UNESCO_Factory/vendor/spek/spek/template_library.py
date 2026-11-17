"""Read-only discovery of Spek template families at template_library/<category>.

A category only becomes usable when its explicitly versioned contract is
implemented by a Spek producer. A folder alone is not a template engine.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from .core import ValidationError

CATEGORY_ID = re.compile(r"[a-z][a-z0-9-]{0,49}\Z")
DEFAULT_LIBRARY = Path(__file__).resolve().parents[1] / "template_library"

def list_template_categories(root: Path = DEFAULT_LIBRARY) -> list[dict]:
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValidationError("Missing or unsafe Spek template_library directory")
    result = []
    for folder in sorted(root.iterdir()):
        if folder.is_symlink():
            raise ValidationError("Template category must not be a symlink: " + folder.name)
        if not folder.is_dir():
            continue
        if not CATEGORY_ID.fullmatch(folder.name):
            raise ValidationError("Invalid template category name: " + folder.name)
        metadata = folder / "category.json"
        if metadata.is_symlink() or not metadata.is_file():
            raise ValidationError("Category declaration missing: " + folder.name)
        try:
            desc = json.loads(metadata.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            raise ValidationError("Invalid category declaration: " + folder.name) from exc
        if desc.get("format") != "spek.template-category/1.0" or desc.get("id") != folder.name:
            raise ValidationError("Invalid category identity: " + folder.name)
        status = desc.get("status")
        if status not in {"implemented", "reserved"}:
            raise ValidationError("Unknown category status: " + folder.name)
        if status == "implemented" and folder.name == "wiki":
            profiles = folder / "archetype-profiles.json"
            if profiles.is_symlink() or not profiles.is_file():
                raise ValidationError("Missing Wiki archetype registry")
        result.append({"id": folder.name, "status": status, "description": desc.get("description", "")})
    return result
