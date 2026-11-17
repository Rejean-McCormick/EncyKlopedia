# 06_GUI/koa_mediatheque_gui/koa_mediatheque/ui/file_preview.py
from __future__ import annotations

import base64
import html
import mimetypes
import os
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from koa_mediatheque.workspace import resolve_content_path


SS_SELECTED_FILE_PATH = "koa_selected_file_path"
SS_LAST_OPERATION_RESULT = "koa_last_operation_result"

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".csv",
    ".tsv",
    ".json",
    ".jsonl",
    ".xml",
    ".html",
    ".htm",
    ".css",
    ".js",
    ".ts",
    ".py",
    ".ps1",
    ".psm1",
    ".sql",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".log",
}

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}

AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".ogg",
    ".m4a",
    ".aac",
    ".flac",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".m4v",
}

PDF_EXTENSIONS = {
    ".pdf",
}

MAX_TEXT_PREVIEW_BYTES = 250_000
MAX_EMBEDDED_PDF_BYTES = 10_000_000


def _st():
    import streamlit as st

    return st


def _safe_container(*, border: bool = False):
    st = _st()

    try:
        return st.container(border=border)
    except TypeError:
        return st.container()


def _to_path(path: str | Path | None) -> Path | None:
    if path is None:
        return None

    value = str(path).strip()

    if not value:
        return None

    if _is_url(value):
        return None

    return resolve_content_path(value)


def _is_url(value: str | Path | None) -> bool:
    if value is None:
        return False

    parsed = urlparse(str(value).strip())
    return parsed.scheme in {"http", "https", "ftp"}


def _guess_mimetype(path: Path) -> str | None:
    guessed, _encoding = mimetypes.guess_type(str(path))
    return guessed


def _format_size(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "unknown"

    size = float(size_bytes)
    units = ["B", "KB", "MB", "GB", "TB"]

    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.2f} {unit}"
        size /= 1024

    return f"{size_bytes} B"


def _read_text_preview(path: Path) -> tuple[str, bool, str]:
    raw = path.read_bytes()
    truncated = len(raw) > MAX_TEXT_PREVIEW_BYTES

    if truncated:
        raw = raw[:MAX_TEXT_PREVIEW_BYTES]

    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding), truncated, encoding
        except UnicodeDecodeError:
            continue

    return raw.decode("utf-8", errors="replace"), truncated, "utf-8-replace"


def _render_pdf_embed(path: Path) -> None:
    st = _st()

    filesize = path.stat().st_size

    if filesize > MAX_EMBEDDED_PDF_BYTES:
        st.info(
            "PDF trop volumineux pour l’aperçu intégré. "
            "Utilise les actions fichier pour l’ouvrir localement."
        )
        return

    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    safe_name = html.escape(path.name)

    st.markdown(
        f"""
        <iframe
            title="{safe_name}"
            src="data:application/pdf;base64,{encoded}"
            width="100%"
            height="760"
            style="border: 1px solid #ddd; border-radius: 4px;"
        ></iframe>
        """,
        unsafe_allow_html=True,
    )


def _open_file_fallback(path: Path) -> bool:
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
            return True

        if sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
            return True

        subprocess.Popen(["xdg-open", str(path)])
        return True
    except Exception:
        return False


def _open_folder_fallback(path: Path) -> bool:
    folder = path if path.is_dir() else path.parent
    return _open_file_fallback(folder)


def _reveal_in_folder_fallback(path: Path) -> bool:
    try:
        if sys.platform.startswith("win"):
            subprocess.Popen(["explorer", "/select,", str(path)])
            return True

        if sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(path)])
            return True

        return _open_folder_fallback(path)
    except Exception:
        return False


def _call_os_service(function_name: str, path: Path) -> Any:
    try:
        from koa_mediatheque.services import os_open_service

        function = getattr(os_open_service, function_name)
        return function(path)
    except Exception:
        return None


def _operation_success(result: Any) -> bool | None:
    if result is None:
        return None

    if isinstance(result, dict):
        if "success" in result:
            return bool(result["success"])
        return None

    if hasattr(result, "success"):
        return bool(getattr(result, "success"))

    return None


def _render_path_metadata(path: Path) -> None:
    st = _st()

    try:
        stat = path.stat()
        filesize = stat.st_size
    except OSError:
        filesize = None

    mimetype = _guess_mimetype(path)

    col_name, col_type, col_size = st.columns([2, 1, 1])

    col_name.write(f"**Nom**  \n`{path.name}`")
    col_type.write(f"**MIME**  \n`{mimetype or 'unknown'}`")
    col_size.write(f"**Taille**  \n`{_format_size(filesize)}`")

    st.caption(f"Chemin : `{path}`")


def _render_external_reference(value: str) -> None:
    st = _st()

    st.info("Référence externe.")
    st.link_button("Ouvrir la référence", value, use_container_width=True)
    st.code(value, language="text")


def render_file_preview(path: str | Path | None) -> None:
    st = _st()

    if path is None or str(path).strip() == "":
        st.info("Aucun fichier sélectionné.")
        return

    raw_value = str(path).strip()
    st.session_state[SS_SELECTED_FILE_PATH] = raw_value

    if _is_url(raw_value):
        _render_external_reference(raw_value)
        return

    file_path = _to_path(raw_value)

    if file_path is None:
        st.warning("Chemin de fichier invalide.")
        return

    with _safe_container(border=True):
        st.subheader("Aperçu fichier")
        _render_path_metadata(file_path)

        if not file_path.exists():
            st.error("Fichier introuvable.")
            return

        if file_path.is_dir():
            st.info("Le chemin sélectionné est un dossier.")
            try:
                entries = sorted(file_path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
                preview_entries = entries[:200]
                st.write(f"{len(entries)} élément(s).")
                st.dataframe(
                    [
                        {
                            "name": entry.name,
                            "type": "folder" if entry.is_dir() else "file",
                            "path": str(entry),
                        }
                        for entry in preview_entries
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
            except OSError as exc:
                st.error(f"Impossible de lire le dossier : {exc}")
            return

        extension = file_path.suffix.lower()
        mimetype = _guess_mimetype(file_path) or ""

        try:
            if extension in IMAGE_EXTENSIONS or mimetype.startswith("image/"):
                st.image(str(file_path), use_container_width=True)
                return

            if extension in AUDIO_EXTENSIONS or mimetype.startswith("audio/"):
                st.audio(str(file_path))
                return

            if extension in VIDEO_EXTENSIONS or mimetype.startswith("video/"):
                st.video(str(file_path))
                return

            if extension in PDF_EXTENSIONS or mimetype == "application/pdf":
                _render_pdf_embed(file_path)
                return

            if extension in TEXT_EXTENSIONS or mimetype.startswith("text/"):
                text, truncated, encoding = _read_text_preview(file_path)

                st.caption(f"Encodage aperçu : `{encoding}`")

                if truncated:
                    st.warning(
                        f"Aperçu limité aux {MAX_TEXT_PREVIEW_BYTES:,} premiers octets."
                    )

                language = extension.removeprefix(".") or "text"
                if language == "markdown":
                    language = "md"

                st.code(text, language=language)
                return

            st.info("Aucun aperçu direct disponible pour ce type de fichier.")
        except Exception as exc:
            st.error(f"Impossible de générer l’aperçu : {exc}")


def render_file_actions(path: str | Path | None) -> None:
    st = _st()

    if path is None or str(path).strip() == "":
        st.info("Aucun fichier sélectionné.")
        return

    raw_value = str(path).strip()

    if _is_url(raw_value):
        st.link_button("Ouvrir la référence externe", raw_value, use_container_width=True)

        if st.button("Copier la référence dans la sélection", use_container_width=True):
            st.session_state[SS_SELECTED_FILE_PATH] = raw_value
            st.success("Référence sélectionnée.")

        return

    file_path = _to_path(raw_value)

    if file_path is None:
        st.warning("Chemin de fichier invalide.")
        return

    with _safe_container(border=True):
        st.subheader("Actions fichier")

        if not file_path.exists():
            st.error("Fichier introuvable.")
            return

        st.session_state[SS_SELECTED_FILE_PATH] = str(file_path)

        col_open, col_folder, col_reveal, col_download = st.columns(4)

        with col_open:
            if st.button("Ouvrir fichier", use_container_width=True, disabled=file_path.is_dir()):
                result = _call_os_service("open_file", file_path)

                if _operation_success(result) is None:
                    ok = _open_file_fallback(file_path)
                    st.success("Ouverture demandée.") if ok else st.error("Ouverture impossible.")
                elif _operation_success(result):
                    st.success("Ouverture demandée.")
                else:
                    st.error("Ouverture impossible.")

                st.session_state[SS_LAST_OPERATION_RESULT] = result

        with col_folder:
            if st.button("Ouvrir dossier", use_container_width=True):
                result = _call_os_service("open_folder", file_path)

                if _operation_success(result) is None:
                    ok = _open_folder_fallback(file_path)
                    st.success("Ouverture demandée.") if ok else st.error("Ouverture impossible.")
                elif _operation_success(result):
                    st.success("Ouverture demandée.")
                else:
                    st.error("Ouverture impossible.")

                st.session_state[SS_LAST_OPERATION_RESULT] = result

        with col_reveal:
            if st.button("Révéler", use_container_width=True, disabled=file_path.is_dir()):
                result = _call_os_service("reveal_in_folder", file_path)

                if _operation_success(result) is None:
                    ok = _reveal_in_folder_fallback(file_path)
                    st.success("Révélation demandée.") if ok else st.error("Révélation impossible.")
                elif _operation_success(result):
                    st.success("Révélation demandée.")
                else:
                    st.error("Révélation impossible.")

                st.session_state[SS_LAST_OPERATION_RESULT] = result

        with col_download:
            if file_path.is_file():
                try:
                    st.download_button(
                        "Télécharger",
                        data=file_path.read_bytes(),
                        file_name=file_path.name,
                        mime=_guess_mimetype(file_path) or "application/octet-stream",
                        use_container_width=True,
                    )
                except OSError as exc:
                    st.error(f"Téléchargement impossible : {exc}")
            else:
                st.button("Télécharger", disabled=True, use_container_width=True)