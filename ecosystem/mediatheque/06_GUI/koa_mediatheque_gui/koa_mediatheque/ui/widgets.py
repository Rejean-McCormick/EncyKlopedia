# 06_GUI/koa_mediatheque_gui/koa_mediatheque/ui/widgets.py
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from html import escape
from pathlib import Path
from typing import Any


def _st():
    import streamlit as st

    return st


def _to_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}

    if isinstance(value, dict):
        return value

    if is_dataclass(value):
        return asdict(value)

    data: dict[str, Any] = {}

    for key in (
        "success",
        "operation",
        "result",
        "entity_type",
        "entity_uuid",
        "media_uuid",
        "version_uuid",
        "path",
        "data",
        "warnings",
        "errors",
        "is_valid",
        "is_blocked",
        "normalized_data",
    ):
        if hasattr(value, key):
            data[key] = getattr(value, key)

    if not data:
        data["message"] = str(value)

    return data


def _message_to_dict(message: Any) -> dict[str, Any]:
    if message is None:
        return {}

    if isinstance(message, dict):
        return message

    if is_dataclass(message):
        return asdict(message)

    return {
        "code": getattr(message, "code", ""),
        "severity": getattr(message, "severity", ""),
        "message": getattr(message, "message", str(message)),
        "field": getattr(message, "field", None),
        "row_number": getattr(message, "row_number", None),
        "details": getattr(message, "details", {}),
    }


def _render_single_message(message: Any, *, default_severity: str = "info") -> None:
    st = _st()

    data = _message_to_dict(message)

    text = str(data.get("message") or data.get("code") or message)
    code = str(data.get("code") or "")
    severity = str(data.get("severity") or default_severity).lower()
    field = data.get("field")
    row_number = data.get("row_number")
    details = data.get("details") or {}

    suffix_parts: list[str] = []

    if code:
        suffix_parts.append(f"`{code}`")
    if field:
        suffix_parts.append(f"champ `{field}`")
    if row_number is not None:
        suffix_parts.append(f"ligne `{row_number}`")

    suffix = f" — {' · '.join(suffix_parts)}" if suffix_parts else ""
    rendered_text = f"{text}{suffix}"

    if severity in {"error", "blocking"}:
        st.error(rendered_text)
    elif severity == "warning":
        st.warning(rendered_text)
    elif severity == "success":
        st.success(rendered_text)
    else:
        st.info(rendered_text)

    if details:
        with st.expander("Détails", expanded=False):
            st.json(details)


def _render_message_list(messages: Any, *, default_severity: str) -> None:
    if not messages:
        return

    if not isinstance(messages, list):
        messages = [messages]

    for message in messages:
        _render_single_message(message, default_severity=default_severity)


def render_path_input(label: str, key: str, default: str = "") -> str:
    st = _st()

    st.session_state.setdefault(key, default)

    value = st.text_input(label, key=key)
    cleaned_value = str(value or "").strip()

    if cleaned_value:
        path = Path(cleaned_value).expanduser()

        if path.exists():
            if path.is_dir():
                st.caption("Dossier trouvé.")
            else:
                st.caption("Fichier trouvé.")
        else:
            st.caption("Chemin non trouvé ou à créer.")

    return cleaned_value


def render_copy_button(label: str, text: str, key: str) -> None:
    st = _st()

    copied_text = text or ""

    if hasattr(st, "copy_button"):
        st.copy_button(
            label,
            copied_text,
            key=key,
            use_container_width=True,
        )
        return

    # Fallback compact pour anciennes versions Streamlit.
    # Ne pas utiliser st.text_area ici : ça crée une grosse zone de texte
    # entre les champs principaux de ChatGPT Intake.
    import streamlit.components.v1 as components

    safe_key = "".join(
        character if character.isalnum() or character == "_" else "_"
        for character in str(key)
    )
    button_id = f"copy_button_{safe_key}"
    status_id = f"{button_id}_status"

    components.html(
        f"""
        <button
            id="{escape(button_id)}"
            type="button"
            style="
                width:100%;
                padding:0.55rem 0.75rem;
                border:1px solid rgba(49, 51, 63, 0.2);
                border-radius:0.5rem;
                background:white;
                cursor:pointer;
                font-size:0.95rem;
                line-height:1.4;
            "
        >
            {escape(label)}
        </button>

        <div
            id="{escape(status_id)}"
            style="
                min-height:1.2rem;
                margin-top:0.25rem;
                font-size:0.8rem;
                opacity:0.75;
            "
        ></div>

        <script>
        const textToCopy = {json.dumps(copied_text, ensure_ascii=False)};
        const button = document.getElementById({json.dumps(button_id)});
        const status = document.getElementById({json.dumps(status_id)});

        function fallbackCopy(text) {{
            const textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.setAttribute("readonly", "");
            textArea.style.position = "fixed";
            textArea.style.left = "-9999px";
            textArea.style.top = "-9999px";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();

            let copied = false;
            try {{
                copied = document.execCommand("copy");
            }} finally {{
                document.body.removeChild(textArea);
            }}

            return copied;
        }}

        button.addEventListener("click", async () => {{
            try {{
                if (navigator.clipboard && window.isSecureContext) {{
                    await navigator.clipboard.writeText(textToCopy);
                    status.textContent = "Copié.";
                    return;
                }}

                if (fallbackCopy(textToCopy)) {{
                    status.textContent = "Copié.";
                    return;
                }}

                status.textContent = "Copie impossible automatiquement.";
            }} catch (err) {{
                if (fallbackCopy(textToCopy)) {{
                    status.textContent = "Copié.";
                }} else {{
                    status.textContent = "Copie impossible automatiquement.";
                }}
            }}
        }});
        </script>
        """,
        height=76,
    )


def render_result_messages(result: Any) -> None:
    st = _st()

    if result is None:
        return

    data = _to_dict(result)

    warnings = data.get("warnings") or []
    errors = data.get("errors") or []

    if "success" in data:
        success = bool(data.get("success"))
        operation = str(data.get("operation") or "operation")
        result_text = str(data.get("result") or "")

        if success:
            st.success(result_text or f"{operation} terminée.")
        else:
            st.error(result_text or f"{operation} échouée.")

    elif "is_valid" in data or "is_blocked" in data:
        is_valid = bool(data.get("is_valid"))
        is_blocked = bool(data.get("is_blocked"))

        if is_blocked:
            st.error("Validation bloquée.")
        elif is_valid:
            st.success("Validation réussie.")
        else:
            st.warning("Validation incomplète ou invalide.")

    elif data.get("message"):
        st.info(str(data["message"]))

    _render_message_list(warnings, default_severity="warning")
    _render_message_list(errors, default_severity="error")

    payload = data.get("data")
    normalized_data = data.get("normalized_data")

    if payload:
        with st.expander("Données", expanded=False):
            st.json(payload)

    if normalized_data:
        with st.expander("Données normalisées", expanded=False):
            st.json(normalized_data)