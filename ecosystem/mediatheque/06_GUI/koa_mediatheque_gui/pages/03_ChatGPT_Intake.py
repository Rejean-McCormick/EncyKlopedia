from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st


APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


from koa_mediatheque.db import get_db_connection
from koa_mediatheque.models import KoaMessage, OperationResult, ValidationResult
from koa_mediatheque.services.chatgpt_intake_service import (
    integrate_chatgpt_intake,
    preview_chatgpt_intake,
)
from koa_mediatheque.services.chatgpt_template_service import build_chatgpt_template
from koa_mediatheque.services.json_validation_service import validate_chatgpt_json
from koa_mediatheque.ui.layout import (
    configure_page,
    render_operation_result,
    render_sidebar_settings,
)
from koa_mediatheque.ui.validation_panel import render_validation_result
from koa_mediatheque.ui.widgets import render_copy_button, render_result_messages


PAGE_TITLE = "ChatGPT Intake"

SS_DB_PATH = "koa_db_path"
SS_STORAGE_ROOT = "koa_storage_root"
SS_IMPORTS_ROOT = "koa_imports_root"
SS_SELECTED_FILE_PATH = "koa_selected_file_path"
SS_CHATGPT_RAW_RESPONSE = "koa_chatgpt_raw_response"
SS_CHATGPT_VALIDATION_RESULT = "koa_chatgpt_validation_result"
SS_CHATGPT_PREVIEW_ROW = "koa_chatgpt_preview_row"
SS_CHATGPT_COPY_MODE = "koa_chatgpt_copy_mode"
SS_LAST_OPERATION_RESULT = "koa_last_operation_result"

COPY_MODES = [
    "reference_only",
    "copy_to_storage",
    "copy_and_rename",
]

DEFAULT_COPY_MODE = "reference_only"


def _safe_get_settings() -> dict[str, Any]:
    settings = render_sidebar_settings()
    if not isinstance(settings, dict):
        return {}
    return settings


def _get_setting_path(
    settings: dict[str, Any],
    *,
    session_key: str,
    setting_keys: list[str],
) -> Path | None:
    value = None

    for key in setting_keys:
        value = settings.get(key)
        if value:
            break

    if not value:
        value = st.session_state.get(session_key)

    if not value:
        return None

    return Path(str(value)).expanduser()


def _make_error_result(
    *,
    operation: str,
    result: str,
    code: str,
    message: str,
    path: str | None = None,
) -> OperationResult:
    return OperationResult(
        success=False,
        operation=operation,
        result=result,
        path=path,
        warnings=[],
        errors=[
            KoaMessage(
                code=code,
                severity="error",
                message=message,
            )
        ],
    )


def _new_import_batch() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    return f"chatgpt_{stamp}"


def _get_file_path_from_state() -> str:
    return str(st.session_state.get(SS_SELECTED_FILE_PATH) or "")


def _set_file_path(path_value: str) -> None:
    st.session_state[SS_SELECTED_FILE_PATH] = path_value.strip()


def _render_file_selector() -> Path | None:
    st.markdown("#### 1. Sélection fichier")

    current_path = _get_file_path_from_state()

    file_path_text = st.text_input(
        "Chemin du fichier local",
        value=current_path,
        placeholder="C:/.../document.pdf ou /home/.../document.pdf",
        help="Le fichier peut être copié dans le stockage local ou seulement référencé selon le mode choisi.",
    ).strip()

    if file_path_text:
        _set_file_path(file_path_text)
        file_path = Path(file_path_text).expanduser()

        if file_path.exists():
            st.success("Fichier trouvé.")
        else:
            st.warning("Le chemin n’existe pas localement. L’intégration sera bloquée sauf référence externe reconnue.")

        return file_path

    st.info("Sélectionner ou coller un chemin de fichier avant de générer le template.")
    return None


def _ensure_default_copy_mode() -> None:
    current_value = st.session_state.get(SS_CHATGPT_COPY_MODE)

    if current_value not in COPY_MODES:
        st.session_state[SS_CHATGPT_COPY_MODE] = DEFAULT_COPY_MODE


def _render_options() -> tuple[str, str, bool]:
    st.markdown("#### Options intake")

    _ensure_default_copy_mode()

    col1, col2 = st.columns(2)

    with col1:
        copy_mode = st.radio(
            "Mode fichier",
            COPY_MODES,
            key=SS_CHATGPT_COPY_MODE,
            help="reference_only ne copie pas le fichier. copy_to_storage copie sans renommer. copy_and_rename copie avec nom canonique.",
        )

    with col2:
        import_batch = st.text_input(
            "import_batch",
            value=st.session_state.get("koa_chatgpt_import_batch") or _new_import_batch(),
            help="Identifiant de lot pour relier les ajouts/imports.",
        ).strip()

    st.session_state["koa_chatgpt_import_batch"] = import_batch

    allow_human_verified_override = st.checkbox(
        "Autoriser override humain pour `canonical_validation_state = verified`",
        value=False,
        help="À utiliser seulement si l’utilisateur humain impose explicitement la validation canonique.",
    )

    return copy_mode, import_batch, allow_human_verified_override


def _render_template_panel(file_path: Path | None) -> None:
    try:
        template_text = build_chatgpt_template(
            selected_file_path=file_path,
            template_path=None,
        )
    except Exception as exc:
        render_result_messages(
            _make_error_result(
                operation="BuildChatGPTTemplate",
                result="template_failed",
                code="ERR_CHATGPT_TEMPLATE",
                message=str(exc),
            )
        )
        return

    render_copy_button(
        "Copier prompt ChatGPT",
        template_text,
        key="copy_chatgpt_prompt",
    )

    with st.expander("Voir le prompt généré", expanded=False):
        st.code(template_text, language="text")


def _render_response_input() -> str:
    st.markdown("#### 3. Coller réponse ChatGPT")

    raw_response = st.text_area(
        "Réponse JSON ChatGPT",
        value=st.session_state.get(SS_CHATGPT_RAW_RESPONSE, ""),
        height=320,
        placeholder="{\n  \"title\": \"...\"\n}",
        help="Coller uniquement le JSON retourné par ChatGPT.",
    )

    st.session_state[SS_CHATGPT_RAW_RESPONSE] = raw_response

    return raw_response


def _run_json_validation(
    raw_response: str,
    *,
    allow_human_verified_override: bool,
) -> ValidationResult | None:
    if not raw_response.strip():
        render_result_messages(
            _make_error_result(
                operation="ValidateChatGPTJson",
                result="empty_response",
                code="ERR_JSON_PARSE",
                message="Aucune réponse JSON à valider.",
            )
        )
        return None

    try:
        validation = validate_chatgpt_json(
            raw_response,
            allow_human_verified_override=allow_human_verified_override,
        )
        st.session_state[SS_CHATGPT_VALIDATION_RESULT] = validation
        return validation
    except Exception as exc:
        result = _make_error_result(
            operation="ValidateChatGPTJson",
            result="validation_failed",
            code="ERR_JSON_VALIDATION",
            message=str(exc),
        )
        render_result_messages(result)
        return None


def _render_validation_actions(
    raw_response: str,
    *,
    allow_human_verified_override: bool,
) -> ValidationResult | None:
    st.markdown("#### 4. Valider JSON")

    validation = st.session_state.get(SS_CHATGPT_VALIDATION_RESULT)

    if st.button("Valider JSON", type="primary", use_container_width=True):
        validation = _run_json_validation(
            raw_response,
            allow_human_verified_override=allow_human_verified_override,
        )

    if validation is not None:
        render_validation_result(validation)

        normalized_data = getattr(validation, "normalized_data", None)
        if normalized_data:
            with st.expander("JSON normalisé", expanded=False):
                st.json(normalized_data)

    return validation


def _run_preview(
    *,
    db_path: Path,
    file_path: Path,
    raw_response: str,
    storage_root: Path,
    import_batch: str,
    copy_mode: str,
    allow_human_verified_override: bool,
) -> OperationResult:
    if not db_path.exists():
        return _make_error_result(
            operation="PreviewChatGPTIntake",
            result="db_not_found",
            code="ERR_DB_NOT_FOUND",
            message=f"Base SQLite introuvable : {db_path}",
            path=str(db_path),
        )

    if not raw_response.strip():
        return _make_error_result(
            operation="PreviewChatGPTIntake",
            result="empty_response",
            code="ERR_JSON_PARSE",
            message="Aucune réponse ChatGPT à prévisualiser.",
        )

    try:
        with get_db_connection(db_path) as connection:
            return preview_chatgpt_intake(
                connection,
                file_path=file_path,
                raw_response=raw_response,
                storage_root=storage_root,
                import_batch=import_batch,
                copy_mode=copy_mode,
                allow_human_verified_override=allow_human_verified_override,
            )
    except Exception as exc:
        return _make_error_result(
            operation="PreviewChatGPTIntake",
            result="preview_failed",
            code="ERR_CHATGPT_PREVIEW",
            message=str(exc),
        )


def _run_integrate(
    *,
    db_path: Path,
    file_path: Path,
    raw_response: str,
    storage_root: Path,
    import_batch: str,
    copy_mode: str,
    allow_human_verified_override: bool,
) -> OperationResult:
    if not db_path.exists():
        return _make_error_result(
            operation="IntegrateChatGPTIntake",
            result="db_not_found",
            code="ERR_DB_NOT_FOUND",
            message=f"Base SQLite introuvable : {db_path}",
            path=str(db_path),
        )

    if not raw_response.strip():
        return _make_error_result(
            operation="IntegrateChatGPTIntake",
            result="empty_response",
            code="ERR_JSON_PARSE",
            message="Aucune réponse ChatGPT à intégrer.",
        )

    try:
        with get_db_connection(db_path) as connection:
            return integrate_chatgpt_intake(
                connection,
                file_path=file_path,
                raw_response=raw_response,
                storage_root=storage_root,
                import_batch=import_batch,
                copy_mode=copy_mode,
                actor="local_user",
                allow_human_verified_override=allow_human_verified_override,
            )
    except Exception as exc:
        return _make_error_result(
            operation="IntegrateChatGPTIntake",
            result="integration_failed",
            code="ERR_CHATGPT_INTEGRATION",
            message=str(exc),
        )



def _render_quick_intake_actions(
    *,
    db_path: Path | None,
    storage_root: Path | None,
    file_path: Path | None,
    raw_response: str,
    import_batch: str,
    copy_mode: str,
    allow_human_verified_override: bool,
) -> None:
    st.markdown("#### Actions")

    missing: list[str] = []
    if db_path is None:
        missing.append("SQLite")
    elif not db_path.exists():
        missing.append("SQLite introuvable")

    if storage_root is None:
        missing.append("stockage")

    if file_path is None:
        missing.append("fichier")

    if not raw_response.strip():
        missing.append("JSON")

    integrate_disabled = bool(missing)

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Valider JSON",
            key="quick_validate_json",
            use_container_width=True,
        ):
            validation = _run_json_validation(
                raw_response,
                allow_human_verified_override=allow_human_verified_override,
            )
            if validation is not None:
                st.session_state[SS_CHATGPT_VALIDATION_RESULT] = validation

    with col2:
        if st.button(
            "Valider et intégrer",
            key="quick_validate_and_integrate",
            type="primary",
            use_container_width=True,
            disabled=integrate_disabled,
        ):
            result = _run_integrate(
                db_path=db_path,
                file_path=file_path,
                raw_response=raw_response,
                storage_root=storage_root,
                import_batch=import_batch,
                copy_mode=copy_mode,
                allow_human_verified_override=allow_human_verified_override,
            )

            st.session_state[SS_LAST_OPERATION_RESULT] = result
            render_result_messages(result)

    if integrate_disabled:
        st.caption("Intégration désactivée : " + ", ".join(missing) + ".")

    validation = st.session_state.get(SS_CHATGPT_VALIDATION_RESULT)
    if validation is not None:
        with st.expander("Résultat de validation", expanded=False):
            render_validation_result(validation)

            normalized_data = getattr(validation, "normalized_data", None)
            if normalized_data:
                with st.expander("JSON normalisé", expanded=False):
                    st.json(normalized_data)


def _render_preview_actions(
    *,
    db_path: Path | None,
    storage_root: Path | None,
    file_path: Path | None,
    raw_response: str,
    import_batch: str,
    copy_mode: str,
    allow_human_verified_override: bool,
) -> None:
    st.markdown("#### Prévisualiser entrée")

    if db_path is None:
        st.warning("Chemin SQLite non configuré.")
        return

    if storage_root is None:
        st.warning("Chemin de stockage non configuré.")
        return

    if file_path is None:
        st.warning("Aucun fichier sélectionné.")
        return

    if st.button(
        "Prévisualiser entrée",
        key="preview_chatgpt_intake",
        use_container_width=True,
    ):
        result = _run_preview(
            db_path=db_path,
            file_path=file_path,
            raw_response=raw_response,
            storage_root=storage_root,
            import_batch=import_batch,
            copy_mode=copy_mode,
            allow_human_verified_override=allow_human_verified_override,
        )

        st.session_state[SS_LAST_OPERATION_RESULT] = result
        st.session_state[SS_CHATGPT_PREVIEW_ROW] = getattr(result, "data", {})
        render_result_messages(result)

    preview_data = st.session_state.get(SS_CHATGPT_PREVIEW_ROW)
    if preview_data:
        with st.expander("Prévisualisation courante", expanded=True):
            st.json(preview_data)


def _build_ps7_fallback_command(
    *,
    db_path: Path | None,
    file_path: Path | None,
    storage_root: Path | None,
    raw_response: str,
    import_batch: str,
    copy_mode: str,
) -> str:
    db = str(db_path or "")
    file = str(file_path or "")
    storage = str(storage_root or "")

    compact_json = raw_response.strip()
    if compact_json:
        try:
            compact_json = json.dumps(json.loads(compact_json), ensure_ascii=False)
        except Exception:
            compact_json = raw_response.strip()

    copy_file = "$true" if copy_mode in {"copy_to_storage", "copy_and_rename"} else "$false"

    return (
        "pwsh -NoProfile -File "
        '"05_TOOLS/Add-KoaLibraryRow.ps1" '
        f'-DbPath "{db}" '
        f'-FilePath "{file}" '
        f"-MetadataJson '{compact_json}' "
        f'-StorageRoot "{storage}" '
        f'-ImportBatch "{import_batch}" '
        '-Mode "InsertNew" '
        f"-CopyFile {copy_file}"
    )


def _render_ps7_fallback(
    *,
    db_path: Path | None,
    file_path: Path | None,
    storage_root: Path | None,
    raw_response: str,
    import_batch: str,
    copy_mode: str,
) -> None:
    st.markdown("#### Fallback PS7")

    command = _build_ps7_fallback_command(
        db_path=db_path,
        file_path=file_path,
        storage_root=storage_root,
        raw_response=raw_response,
        import_batch=import_batch,
        copy_mode=copy_mode,
    )

    render_copy_button(
        "Copier commande PS7 fallback",
        command,
        key="copy_ps7_fallback_command",
    )

    with st.expander("Voir commande", expanded=False):
        st.code(command, language="powershell")


def render_page() -> None:
    configure_page()

    st.title("ChatGPT Intake")
    st.caption("Chemin fichier + prompt + réponse JSON, sans va-et-vient inutile.")

    settings = _safe_get_settings()

    db_path = _get_setting_path(
        settings,
        session_key=SS_DB_PATH,
        setting_keys=["db_path", SS_DB_PATH],
    )
    storage_root = _get_setting_path(
        settings,
        session_key=SS_STORAGE_ROOT,
        setting_keys=["storage_root", SS_STORAGE_ROOT],
    )

    last_result = st.session_state.get(SS_LAST_OPERATION_RESULT)
    render_operation_result(last_result)

    left, right = st.columns([1, 1.25])

    with left:
        file_path = _render_file_selector()
        _render_template_panel(file_path)

        with st.expander("Options intake", expanded=False):
            copy_mode, import_batch, allow_human_verified_override = _render_options()

    with right:
        raw_response = _render_response_input()
        _render_quick_intake_actions(
            db_path=db_path,
            storage_root=storage_root,
            file_path=file_path,
            raw_response=raw_response,
            import_batch=import_batch,
            copy_mode=copy_mode,
            allow_human_verified_override=allow_human_verified_override,
        )

    st.divider()

    with st.expander("Prévisualiser entrée", expanded=False):
        _render_preview_actions(
            db_path=db_path,
            storage_root=storage_root,
            file_path=file_path,
            raw_response=raw_response,
            import_batch=import_batch,
            copy_mode=copy_mode,
            allow_human_verified_override=allow_human_verified_override,
        )

    with st.expander("Fallback PS7", expanded=False):
        _render_ps7_fallback(
            db_path=db_path,
            file_path=file_path,
            storage_root=storage_root,
            raw_response=raw_response,
            import_batch=import_batch,
            copy_mode=copy_mode,
        )



if __name__ == "__main__":
    render_page()