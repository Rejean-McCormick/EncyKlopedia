"""Resolve the single Médiathèque application and its adjacent content workspace."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath


@dataclass(frozen=True)
class WorkspacePaths:
    app_root: Path
    content_root: Path
    db_path: Path
    storage_root: Path
    imports_root: Path
    exports_root: Path
    backups_root: Path
    logs_root: Path
    kristals_root: Path
    documents_root: Path
    schema_dir: Path
    config_path: Path


def resolve_app_root(start: str | Path | None = None) -> Path:
    env = os.environ.get("KOA_APP_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    current = Path(start or __file__).expanduser().resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "05_TOOLS").is_dir():
            return candidate
    return current


def resolve_content_root(app_root: str | Path | None = None) -> Path:
    env = os.environ.get("KOA_CONTENT_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    app = resolve_app_root(app_root)
    return (app.parent / "content").resolve()


def get_workspace_paths(app_root: str | Path | None = None) -> WorkspacePaths:
    app = resolve_app_root(app_root)
    content = resolve_content_root(app)
    return WorkspacePaths(
        app_root=app,
        content_root=content,
        db_path=content / "01_DB" / "koa_mediatheque.sqlite",
        storage_root=content / "02_STORAGE",
        imports_root=content / "03_IMPORTS",
        exports_root=content / "04_EXPORTS",
        backups_root=content / "07_BACKUPS",
        logs_root=content / "08_LOGS",
        kristals_root=content / "kristals",
        documents_root=content / "documents",
        schema_dir=app / "schemas" / "sqlite",
        config_path=content / "config.toml",
    )



def resolve_content_path(value: str | Path, app_root: str | Path | None = None) -> Path:
    """Resolve DB-stored relative paths against the adjacent content root."""
    text = str(value).strip()
    path = Path(text).expanduser()
    if path.is_absolute() or PureWindowsPath(text).drive:
        return path
    return (resolve_content_root(app_root) / path).resolve()

def ensure_content_directories(paths: WorkspacePaths | None = None) -> WorkspacePaths:
    p = paths or get_workspace_paths()
    for directory in (
        p.content_root,
        p.db_path.parent,
        p.storage_root,
        p.imports_root,
        p.exports_root,
        p.backups_root,
        p.logs_root,
        p.kristals_root,
        p.documents_root,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    return p


__all__ = [
    "WorkspacePaths",
    "ensure_content_directories",
    "get_workspace_paths",
    "resolve_app_root",
    "resolve_content_root",
    "resolve_content_path",
]
