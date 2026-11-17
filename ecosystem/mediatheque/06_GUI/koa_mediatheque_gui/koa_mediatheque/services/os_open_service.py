# 06_GUI/koa_mediatheque_gui/koa_mediatheque/services/os_open_service.py

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from koa_mediatheque.errors import ERR_FILE_NOT_FOUND
from koa_mediatheque.models import KoaMessage, OperationResult


ERR_OS_OPEN_FAILED = "ERR_OS_OPEN_FAILED"


def open_file(path: str | Path) -> OperationResult:
    target = _normalize_path(path)

    if not target.is_file():
        return _missing_path_result(
            operation="open_file",
            result="file_not_found",
            path=target,
            message=f"Fichier introuvable : {target}",
        )

    return _open_target(
        target,
        operation="open_file",
        result="opened",
    )


def open_folder(path: str | Path) -> OperationResult:
    target = _normalize_path(path)

    if not target.is_dir():
        return _missing_path_result(
            operation="open_folder",
            result="folder_not_found",
            path=target,
            message=f"Dossier introuvable : {target}",
        )

    return _open_target(
        target,
        operation="open_folder",
        result="opened",
    )


def reveal_in_folder(path: str | Path) -> OperationResult:
    target = _normalize_path(path)

    if not target.exists():
        return _missing_path_result(
            operation="reveal_in_folder",
            result="path_not_found",
            path=target,
            message=f"Chemin introuvable : {target}",
        )

    try:
        _reveal_target(target)

        return _success_result(
            operation="reveal_in_folder",
            result="opened",
            path=target,
        )
    except Exception as exc:
        return _failed_result(
            operation="reveal_in_folder",
            path=target,
            message=str(exc),
        )


def _normalize_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _open_target(
    path: Path,
    *,
    operation: str,
    result: str,
) -> OperationResult:
    try:
        _launch_path(path)

        return _success_result(
            operation=operation,
            result=result,
            path=path,
        )
    except Exception as exc:
        return _failed_result(
            operation=operation,
            path=path,
            message=str(exc),
        )


def _launch_path(path: Path) -> None:
    if sys.platform.startswith("win"):
        os.startfile(str(path))  # type: ignore[attr-defined]
        return

    if sys.platform == "darwin":
        subprocess.Popen(
            ["open", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return

    subprocess.Popen(
        ["xdg-open", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _reveal_target(path: Path) -> None:
    if sys.platform.startswith("win"):
        if path.is_file():
            subprocess.Popen(
                ["explorer", f"/select,{path}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.Popen(
                ["explorer", str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        return

    if sys.platform == "darwin":
        if path.is_file():
            subprocess.Popen(
                ["open", "-R", str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        else:
            subprocess.Popen(
                ["open", str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        return

    folder = path.parent if path.is_file() else path
    subprocess.Popen(
        ["xdg-open", str(folder)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _success_result(
    *,
    operation: str,
    result: str,
    path: Path,
) -> OperationResult:
    return OperationResult(
        success=True,
        operation=operation,
        result=result,
        entity_type="file",
        entity_uuid=None,
        media_uuid=None,
        version_uuid=None,
        path=str(path),
        data={
            "path": str(path),
            "platform": sys.platform,
        },
        warnings=[],
        errors=[],
    )


def _missing_path_result(
    *,
    operation: str,
    result: str,
    path: Path,
    message: str,
) -> OperationResult:
    return OperationResult(
        success=False,
        operation=operation,
        result=result,
        entity_type="file",
        entity_uuid=None,
        media_uuid=None,
        version_uuid=None,
        path=str(path),
        data={
            "path": str(path),
            "platform": sys.platform,
        },
        warnings=[],
        errors=[
            KoaMessage(
                code=ERR_FILE_NOT_FOUND,
                severity="blocking",
                message=message,
                field="path",
            )
        ],
    )


def _failed_result(
    *,
    operation: str,
    path: Path,
    message: str,
) -> OperationResult:
    return OperationResult(
        success=False,
        operation=operation,
        result="open_failed",
        entity_type="file",
        entity_uuid=None,
        media_uuid=None,
        version_uuid=None,
        path=str(path),
        data={
            "path": str(path),
            "platform": sys.platform,
        },
        warnings=[],
        errors=[
            KoaMessage(
                code=ERR_OS_OPEN_FAILED,
                severity="error",
                message=message,
                field="path",
            )
        ],
    )