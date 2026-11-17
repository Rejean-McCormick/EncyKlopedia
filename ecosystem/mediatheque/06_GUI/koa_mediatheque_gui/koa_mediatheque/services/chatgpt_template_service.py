# 06_GUI/koa_mediatheque_gui/koa_mediatheque/services/chatgpt_template_service.py

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    from koa_mediatheque.constants import (
        APP_PUBLIC_NAME,
        APP_SHORT_NAME,
        APP_TECHNICAL_NAME,
        APP_COMPONENT,
        CHATGPT_JSON_REQUIRED_FIELDS,
        JSON_ARRAY_FIELDS,
        TECHNICAL_PROTECTED_FIELDS,
    )
except ImportError:
    APP_PUBLIC_NAME = "Médiathèque kOA"
    APP_SHORT_NAME = "kOA"
    APP_TECHNICAL_NAME = "koa-mediatheque"
    APP_COMPONENT = "koa_mediatheque"
    CHATGPT_JSON_REQUIRED_FIELDS: list[str] = [
        "title",
        "description",
        "media_type",
        "language",
        "library_scope",
        "uckk_relevance",
        "target_system",
        "public_state",
        "visibility",
        "access_level",
        "ownership_scope",
        "source_type",
        "source_ownership",
        "rights_status",
        "restriction_state",
        "status",
        "provenance",
        "ai_validation_state",
        "canonical_validation_state",
        "human_review_required",
        "audience_suitability",
        "export_to_uckk",
        "export_to_public",
    ]
    JSON_ARRAY_FIELDS: list[str] = [
        "collections",
        "tags",
        "relations",
        "content_flags",
    ]
    TECHNICAL_PROTECTED_FIELDS: list[str] = [
        "sha256",
        "filesize",
        "mimetype",
        "filename",
        "extension",
        "original_path",
        "storage_path",
    ]

try:
    from koa_mediatheque.validation.allowed_values import ALLOWED_VALUES_BY_FIELD
except ImportError:
    ALLOWED_VALUES_BY_FIELD: dict[str, list[Any] | set[Any] | tuple[Any, ...]] = {}


TEMPLATE_VERSION = "koa-chatgpt-template-v1"

_TEMPLATE_VERSION_PATTERN = re.compile(
    r"(?im)^\s*TEMPLATE_VERSION\s*[:=]\s*([A-Za-z0-9_.:-]+)\s*$"
)


def load_chatgpt_template(template_path: str | Path) -> str:
    """
    Load a ChatGPT intake template from disk.

    The template must be UTF-8 text. The caller decides whether to render
    placeholders with build_chatgpt_template().
    """
    path = Path(template_path).expanduser()

    if not path.exists():
        raise FileNotFoundError(f"Template ChatGPT introuvable : {path}")

    if not path.is_file():
        raise ValueError(f"Le chemin du template ChatGPT n'est pas un fichier : {path}")

    return path.read_text(encoding="utf-8")


def build_chatgpt_template(
    *,
    selected_file_path: str | Path | None = None,
    template_path: str | Path | None = None,
) -> str:
    """
    Build the prompt copied by the GUI button "Copier template ChatGPT".

    If template_path is supplied, the file is loaded and placeholders are
    replaced. If no path is supplied, a deterministic built-in template is used.
    """
    template_text = (
        load_chatgpt_template(template_path)
        if template_path is not None
        else _build_default_template()
    )

    selected_path = Path(selected_file_path).expanduser() if selected_file_path else None
    selected_file_name = selected_path.name if selected_path else ""

    replacements = {
        "APP_PUBLIC_NAME": APP_PUBLIC_NAME,
        "APP_SHORT_NAME": APP_SHORT_NAME,
        "APP_TECHNICAL_NAME": APP_TECHNICAL_NAME,
        "APP_COMPONENT": APP_COMPONENT,
        "TEMPLATE_VERSION": TEMPLATE_VERSION,
        "SELECTED_FILE_PATH": str(selected_path) if selected_path else "",
        "SELECTED_FILENAME": selected_file_name,
        "REQUIRED_FIELDS": _format_required_fields(),
        "ALLOWED_VALUES": _format_allowed_values(),
        "JSON_ARRAY_FIELDS": _format_list(JSON_ARRAY_FIELDS),
        "TECHNICAL_PROTECTED_FIELDS": _format_list(TECHNICAL_PROTECTED_FIELDS),
        "JSON_SCHEMA_EXAMPLE": _build_json_schema_example(),
    }

    rendered = _replace_placeholders(template_text, replacements)

    if "{{" in rendered or "}}" in rendered:
        rendered = _append_unresolved_placeholder_warning(rendered)

    return rendered.strip() + "\n"


def get_chatgpt_template_version(template_text: str) -> str:
    """
    Extract the template version from a template text.

    Returns TEMPLATE_VERSION when no explicit version marker is present.
    """
    if not isinstance(template_text, str):
        return TEMPLATE_VERSION

    match = _TEMPLATE_VERSION_PATTERN.search(template_text)
    if not match:
        return TEMPLATE_VERSION

    return match.group(1).strip() or TEMPLATE_VERSION


def _build_default_template() -> str:
    return """# Médiathèque kOA — Template ChatGPT Intake

TEMPLATE_VERSION: {{TEMPLATE_VERSION}}

## App identity

App public name: {{APP_PUBLIC_NAME}}
App short name: {{APP_SHORT_NAME}}
Technical name: {{APP_TECHNICAL_NAME}}
Component: {{APP_COMPONENT}}

## Selected file

Selected file path:
{{SELECTED_FILE_PATH}}

Selected filename:
{{SELECTED_FILENAME}}

## Your task

Analyze the selected file context and propose structured catalog metadata for Médiathèque kOA.

Return JSON only.

Do not wrap the JSON in Markdown.
Do not add commentary before or after the JSON.
Do not invent source, ownership, rights, public status, or export permission.
If uncertain, use controlled uncertainty values and require human review.

## Non-negotiable rules

SQLite is the source of truth.
ChatGPT provides metadata suggestions only.
The app recalculates technical file facts locally.
Do not provide technical file facts.
Do not set canonical_validation_state to verified.
Default canonical_validation_state must be unverified unless a human explicitly instructs otherwise.
Unknown rights require human_review_required = 1.
Unknown source requires human_review_required = 1.
Non-UCKK, non-public, private, third-party, uncertain, and non-exportable records are valid cases.

## Technical fields you must not output

{{TECHNICAL_PROTECTED_FIELDS}}

## Required JSON fields

{{REQUIRED_FIELDS}}

## Multi-value JSON array fields

{{JSON_ARRAY_FIELDS}}

## Allowed controlled values

{{ALLOWED_VALUES}}

## JSON object to return

Use this shape exactly. Keep unknown fields as controlled unknown/review values.

{{JSON_SCHEMA_EXAMPLE}}
"""


def _replace_placeholders(template_text: str, replacements: dict[str, str]) -> str:
    rendered = template_text

    for key, value in replacements.items():
        rendered = rendered.replace("{{" + key + "}}", value)

    return rendered


def _format_required_fields() -> str:
    if not CHATGPT_JSON_REQUIRED_FIELDS:
        return "- Aucun champ requis configuré."

    return "\n".join(f"- {field_name}" for field_name in CHATGPT_JSON_REQUIRED_FIELDS)


def _format_allowed_values() -> str:
    if not ALLOWED_VALUES_BY_FIELD:
        return "- Aucune liste de valeurs contrôlées configurée."

    lines: list[str] = []

    for field_name in sorted(ALLOWED_VALUES_BY_FIELD):
        values = ALLOWED_VALUES_BY_FIELD[field_name]
        normalized_values = _sorted_string_values(values)
        joined_values = ", ".join(normalized_values)
        lines.append(f"- {field_name}: {joined_values}")

    return "\n".join(lines)


def _format_list(values: list[Any] | tuple[Any, ...] | set[Any]) -> str:
    if not values:
        return "- Aucun"

    return "\n".join(f"- {value}" for value in _sorted_string_values(values))


def _build_json_schema_example() -> str:
    lines = [
        "{",
        '  "title": "",',
        '  "subtitle": null,',
        '  "description": "",',
        '  "summary": "",',
        '  "media_type": "document",',
        '  "language": "fr",',
        '  "library_scope": "koa",',
        '  "uckk_relevance": "unknown",',
        '  "target_system": "none",',
        '  "target_export_allowed": 0,',
        '  "public_state": "unknown",',
        '  "visibility": "private",',
        '  "access_level": "private",',
        '  "ownership_scope": "unknown",',
        '  "source_type": "unknown",',
        '  "source_ownership": "unknown_source",',
        '  "rights_status": "unknown",',
        '  "rights_note": null,',
        '  "restriction_state": "unknown",',
        '  "restriction_reason": null,',
        '  "redaction_required": 0,',
        '  "status": "draft",',
        '  "provenance": "ai_assisted",',
        '  "ai_validation_state": "ai_uncertain",',
        '  "ai_confidence": null,',
        '  "canonical_validation_state": "unverified",',
        '  "human_review_required": 1,',
        '  "review_queue": "metadata_review",',
        '  "review_reason": "AI metadata suggestion requires human review.",',
        '  "collections": [],',
        '  "tags": [],',
        '  "relations": [],',
        '  "content_flags": [],',
        '  "audience_suitability": "unknown",',
        '  "export_to_uckk": "review_required",',
        '  "export_to_public": "review_required",',
        '  "export_policy_note": "Do not export until source, rights, public status, and restrictions are reviewed.",',
        '  "import_batch": null,',
        '  "notes": null',
        "}",
    ]

    return "\n".join(lines)


def _sorted_string_values(values: list[Any] | tuple[Any, ...] | set[Any]) -> list[str]:
    return sorted(str(value) for value in values)


def _append_unresolved_placeholder_warning(template_text: str) -> str:
    return (
        template_text.rstrip()
        + "\n\n"
        + "## Internal warning\n\n"
        + "Some template placeholders were not resolved. "
        + "Do not answer this template until the local app template is corrected.\n"
    )