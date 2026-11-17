"""
Path helpers for Médiathèque kOA.

This module centralizes canonical path construction and validation.

It performs no filesystem writes on import. Directory creation is only done by
explicit helper functions such as ensure_project_directories().
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from koa_mediatheque.constants import (
    APP_DB_FILENAME,
    DEFAULT_FILEAREA,
    EXPORT_SUBDIRS,
    IMPORT_SUBDIRS,
    KOA_BACKUPS_DIR,
    KOA_DB_DIR,
    KOA_DOCS_DIR,
    KOA_EXPORTS_DIR,
    KOA_GUI_DIR,
    KOA_IMPORTS_DIR,
    KOA_LOGS_DIR,
    KOA_ROOT,
    KOA_STORAGE_DIR,
    KOA_TOOLS_DIR,
    SCHEMA_VERSIONS_DIR,
    STORAGE_FILEAREAS,
)


@dataclass(frozen=True)
class KoaPaths:
    """Resolved canonical paths for a Médiathèque kOA project root."""

    root: Path
    db_dir: Path
    db_path: Path
    schema_dir: Path
    storage_dir: Path
    imports_dir: Path
    exports_dir: Path
    tools_dir: Path
    gui_dir: Path
    backups_dir: Path
    logs_dir: Path
    docs_dir: Path

    def required_directories(self) -> tuple[Path, ...]:
        """Return directories required for normal local app operation."""
        return (
            self.root,
            self.db_dir,
            self.schema_dir,
            self.storage_dir,
            self.imports_dir,
            self.exports_dir,
            self.tools_dir,
            self.gui_dir,
            self.backups_dir,
            self.logs_dir,
            self.docs_dir,
        )

    def storage_filearea_path(self, filearea: str = DEFAULT_FILEAREA) -> Path:
        """Return a resolved path inside 02_STORAGE for a canonical filearea."""
        return resolve_storage_filearea_path(self.storage_dir, filearea)

    def import_subdir_path(self, subdir: str) -> Path:
        """Return a resolved path inside 03_IMPORTS for a canonical subdir."""
        return resolve_import_subdir_path(self.imports_dir, subdir)

    def export_subdir_path(self, subdir: str) -> Path:
        """Return a resolved path inside 04_EXPORTS for a canonical subdir."""
        return resolve_export_subdir_path(self.exports_dir, subdir)


def normalize_path(path_value: str | Path) -> Path:
    """Return an expanded, resolved Path."""
    return Path(path_value).expanduser().resolve()


def resolve_project_root(root_path: str | Path | None = None) -> Path:
    """
    Resolve the KOA_MEDIATHEQUE project root.

    If root_path is supplied, it is used directly.

    If root_path is omitted and the current working directory is already inside
    a KOA_MEDIATHEQUE tree, the ancestor named KOA_MEDIATHEQUE is returned.

    Otherwise, a KOA_MEDIATHEQUE child of the current working directory is
    returned.
    """
    if root_path is not None:
        return normalize_path(root_path)

    current = Path(os.getcwd()).expanduser().resolve()

    if current.name == KOA_ROOT:
        return current

    for parent in current.parents:
        if parent.name == KOA_ROOT:
            return parent

    return current / KOA_ROOT


def find_project_root(start_path: str | Path | None = None) -> Path | None:
    """
    Find an existing KOA_MEDIATHEQUE ancestor.

    Returns None when no ancestor named KOA_MEDIATHEQUE exists.
    """
    start = normalize_path(start_path or os.getcwd())

    if start.name == KOA_ROOT:
        return start

    for parent in start.parents:
        if parent.name == KOA_ROOT:
            return parent

    return None



def resolve_content_root(root_path: str | Path | None = None) -> Path:
    """Resolve the adjacent runtime content root."""
    env = os.environ.get("KOA_CONTENT_ROOT")
    if env:
        return normalize_path(env)
    app_root = resolve_project_root(root_path)
    return (app_root.parent / "content").resolve()

def build_koa_paths(root_path: str | Path | None = None) -> KoaPaths:
    """Build the full canonical path set for a project root."""
    root = resolve_project_root(root_path)
    content = resolve_content_root(root)

    return KoaPaths(
        root=root,
        db_dir=content / KOA_DB_DIR,
        db_path=content / KOA_DB_DIR / APP_DB_FILENAME,
        schema_dir=root / "schemas" / "sqlite",
        storage_dir=content / KOA_STORAGE_DIR,
        imports_dir=content / KOA_IMPORTS_DIR,
        exports_dir=content / KOA_EXPORTS_DIR,
        tools_dir=root / KOA_TOOLS_DIR,
        gui_dir=root / KOA_GUI_DIR,
        backups_dir=content / KOA_BACKUPS_DIR,
        logs_dir=content / KOA_LOGS_DIR,
        docs_dir=root / KOA_DOCS_DIR,
    )


def resolve_from_root(
    root_path: str | Path | None,
    *parts: str | Path,
) -> Path:
    """Resolve a path under the project root."""
    root = resolve_project_root(root_path)
    return root.joinpath(*map(str, parts)).resolve()


def resolve_db_dir(root_path: str | Path | None = None) -> Path:
    """Return the canonical 01_DB path."""
    return resolve_content_root(root_path) / KOA_DB_DIR


def resolve_db_path(root_path: str | Path | None = None) -> Path:
    """Return the canonical SQLite database path."""
    return resolve_content_root(root_path) / KOA_DB_DIR / APP_DB_FILENAME


def resolve_schema_dir(root_path: str | Path | None = None) -> Path:
    """Return the canonical schema_versions directory path."""
    return resolve_project_root(root_path) / "schemas" / "sqlite"


def resolve_storage_root(root_path: str | Path | None = None) -> Path:
    """Return the canonical 02_STORAGE path."""
    return resolve_content_root(root_path) / KOA_STORAGE_DIR


def resolve_imports_root(root_path: str | Path | None = None) -> Path:
    """Return the canonical 03_IMPORTS path."""
    return resolve_content_root(root_path) / KOA_IMPORTS_DIR


def resolve_exports_root(root_path: str | Path | None = None) -> Path:
    """Return the canonical 04_EXPORTS path."""
    return resolve_content_root(root_path) / KOA_EXPORTS_DIR


def resolve_tools_root(root_path: str | Path | None = None) -> Path:
    """Return the canonical 05_TOOLS path."""
    return resolve_from_root(root_path, KOA_TOOLS_DIR)


def resolve_gui_root(root_path: str | Path | None = None) -> Path:
    """Return the canonical 06_GUI path."""
    return resolve_from_root(root_path, KOA_GUI_DIR)


def resolve_backups_root(root_path: str | Path | None = None) -> Path:
    """Return the canonical 07_BACKUPS path."""
    return resolve_content_root(root_path) / KOA_BACKUPS_DIR


def resolve_logs_root(root_path: str | Path | None = None) -> Path:
    """Return the canonical 08_LOGS path."""
    return resolve_content_root(root_path) / KOA_LOGS_DIR


def resolve_docs_root(root_path: str | Path | None = None) -> Path:
    """Return the canonical docs path."""
    return resolve_from_root(root_path, KOA_DOCS_DIR)


def resolve_storage_filearea_path(
    storage_root: str | Path,
    filearea: str = DEFAULT_FILEAREA,
) -> Path:
    """Return a canonical storage filearea path."""
    validate_storage_filearea(filearea)
    return normalize_path(storage_root) / filearea


def resolve_import_subdir_path(
    imports_root: str | Path,
    subdir: str,
) -> Path:
    """Return a canonical import subdirectory path."""
    validate_import_subdir(subdir)
    return normalize_path(imports_root) / subdir


def resolve_export_subdir_path(
    exports_root: str | Path,
    subdir: str,
) -> Path:
    """Return a canonical export subdirectory path."""
    validate_export_subdir(subdir)
    return normalize_path(exports_root) / subdir


def validate_storage_filearea(filearea: str) -> None:
    """Raise ValueError if filearea is not a canonical storage filearea."""
    if filearea not in STORAGE_FILEAREAS:
        allowed = ", ".join(STORAGE_FILEAREAS)
        raise ValueError(f"Invalid storage filearea: {filearea!r}. Allowed: {allowed}")


def validate_import_subdir(subdir: str) -> None:
    """Raise ValueError if subdir is not a canonical imports subdirectory."""
    if subdir not in IMPORT_SUBDIRS:
        allowed = ", ".join(IMPORT_SUBDIRS)
        raise ValueError(f"Invalid import subdir: {subdir!r}. Allowed: {allowed}")


def validate_export_subdir(subdir: str) -> None:
    """Raise ValueError if subdir is not a canonical exports subdirectory."""
    if subdir not in EXPORT_SUBDIRS:
        allowed = ", ".join(EXPORT_SUBDIRS)
        raise ValueError(f"Invalid export subdir: {subdir!r}. Allowed: {allowed}")


def iter_storage_filearea_paths(storage_root: str | Path) -> tuple[Path, ...]:
    """Return all canonical storage filearea paths."""
    root = normalize_path(storage_root)
    return tuple(root / filearea for filearea in STORAGE_FILEAREAS)


def iter_import_subdir_paths(imports_root: str | Path) -> tuple[Path, ...]:
    """Return all canonical import subdirectory paths."""
    root = normalize_path(imports_root)
    return tuple(root / subdir for subdir in IMPORT_SUBDIRS)


def iter_export_subdir_paths(exports_root: str | Path) -> tuple[Path, ...]:
    """Return all canonical export subdirectory paths."""
    root = normalize_path(exports_root)
    return tuple(root / subdir for subdir in EXPORT_SUBDIRS)


def iter_project_directories(root_path: str | Path | None = None) -> tuple[Path, ...]:
    """Return all canonical project directories that should exist."""
    paths = build_koa_paths(root_path)

    return (
        *paths.required_directories(),
        *iter_storage_filearea_paths(paths.storage_dir),
        *iter_import_subdir_paths(paths.imports_dir),
        *iter_export_subdir_paths(paths.exports_dir),
    )


def ensure_directory(path: str | Path) -> Path:
    """Create one directory if missing and return its resolved path."""
    resolved = normalize_path(path)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def ensure_project_directories(root_path: str | Path | None = None) -> KoaPaths:
    """Create all canonical project directories and return resolved paths."""
    paths = build_koa_paths(root_path)

    for directory in iter_project_directories(paths.root):
        directory.mkdir(parents=True, exist_ok=True)

    return paths


def path_exists(path: str | Path) -> bool:
    """Return whether a path exists."""
    return normalize_path(path).exists()


def is_file(path: str | Path) -> bool:
    """Return whether a path exists and is a file."""
    return normalize_path(path).is_file()


def is_dir(path: str | Path) -> bool:
    """Return whether a path exists and is a directory."""
    return normalize_path(path).is_dir()


def require_existing_file(path: str | Path) -> Path:
    """Return resolved path or raise FileNotFoundError if not an existing file."""
    resolved = normalize_path(path)

    if not resolved.is_file():
        raise FileNotFoundError(f"File not found: {resolved}")

    return resolved


def require_existing_dir(path: str | Path) -> Path:
    """Return resolved path or raise FileNotFoundError if not an existing directory."""
    resolved = normalize_path(path)

    if not resolved.is_dir():
        raise FileNotFoundError(f"Directory not found: {resolved}")

    return resolved


def is_path_inside(path: str | Path, parent: str | Path) -> bool:
    """Return whether path is inside parent after resolution."""
    resolved_path = normalize_path(path)
    resolved_parent = normalize_path(parent)

    try:
        resolved_path.relative_to(resolved_parent)
        return True
    except ValueError:
        return False


def relative_to_root(
    path: str | Path,
    root_path: str | Path | None = None,
) -> Path:
    """Return path relative to project root, or raise ValueError if outside."""
    root = resolve_project_root(root_path)
    resolved_path = normalize_path(path)

    try:
        return resolved_path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Path is outside project root: {resolved_path}") from exc


def safe_relative_to(
    path: str | Path,
    parent: str | Path,
) -> Path | None:
    """Return path relative to parent, or None if outside parent."""
    resolved_path = normalize_path(path)
    resolved_parent = normalize_path(parent)

    try:
        return resolved_path.relative_to(resolved_parent)
    except ValueError:
        return None


def coerce_project_path(
    value: str | Path,
    *,
    root_path: str | Path | None = None,
) -> Path:
    """
    Resolve a user-supplied path.

    Absolute paths remain absolute. Relative paths are resolved from the project
    root.
    """
    path = Path(value).expanduser()

    if path.is_absolute():
        return path.resolve()

    return resolve_project_root(root_path).joinpath(path).resolve()


def validate_project_path_is_inside_root(
    path: str | Path,
    *,
    root_path: str | Path | None = None,
) -> Path:
    """Return resolved path if it is inside the project root."""
    root = resolve_project_root(root_path)
    resolved = coerce_project_path(path, root_path=root)

    if not is_path_inside(resolved, root):
        raise ValueError(f"Path is outside project root: {resolved}")

    return resolved


def validate_paths_are_inside_root(
    paths: Iterable[str | Path],
    *,
    root_path: str | Path | None = None,
) -> tuple[Path, ...]:
    """Validate multiple paths are inside the project root."""
    return tuple(
        validate_project_path_is_inside_root(path, root_path=root_path)
        for path in paths
    )


__all__ = [
    "KoaPaths",
    "build_koa_paths",
    "coerce_project_path",
    "ensure_directory",
    "ensure_project_directories",
    "find_project_root",
    "is_dir",
    "is_file",
    "is_path_inside",
    "iter_export_subdir_paths",
    "iter_import_subdir_paths",
    "iter_project_directories",
    "iter_storage_filearea_paths",
    "normalize_path",
    "path_exists",
    "relative_to_root",
    "require_existing_dir",
    "require_existing_file",
    "resolve_backups_root",
    "resolve_content_root",
    "resolve_db_dir",
    "resolve_db_path",
    "resolve_docs_root",
    "resolve_export_subdir_path",
    "resolve_exports_root",
    "resolve_from_root",
    "resolve_gui_root",
    "resolve_import_subdir_path",
    "resolve_imports_root",
    "resolve_logs_root",
    "resolve_project_root",
    "resolve_schema_dir",
    "resolve_storage_filearea_path",
    "resolve_storage_root",
    "resolve_tools_root",
    "safe_relative_to",
    "validate_export_subdir",
    "validate_import_subdir",
    "validate_paths_are_inside_root",
    "validate_project_path_is_inside_root",
    "validate_storage_filearea",
]