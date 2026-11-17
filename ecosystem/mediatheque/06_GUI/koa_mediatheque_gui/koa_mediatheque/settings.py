"""
Settings for Médiathèque kOA.

This module defines the local configuration object used by the Streamlit GUI and
service layer. It has no Streamlit dependency and performs no filesystem writes
on import.

Configuration precedence:

1. Built-in canonical defaults from constants.py
2. Optional TOML config file
3. Environment variables
4. Explicit runtime overrides
"""

from __future__ import annotations

import os
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Mapping

from koa_mediatheque.constants import (
    APP_COMPONENT,
    APP_DB_FILENAME,
    APP_PRIMARY_LANGUAGE,
    COPY_MODE_COPY_TO_STORAGE,
    COPY_MODE_VALUES,
    DEFAULT_FILEAREA,
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
)

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    tomllib = None  # type: ignore[assignment]


ENV_KOA_ROOT = "KOA_ROOT"
ENV_KOA_CONTENT_ROOT = "KOA_CONTENT_ROOT"
ENV_KOA_DB_PATH = "KOA_DB_PATH"
ENV_KOA_STORAGE_ROOT = "KOA_STORAGE_ROOT"
ENV_KOA_IMPORTS_ROOT = "KOA_IMPORTS_ROOT"
ENV_KOA_EXPORTS_ROOT = "KOA_EXPORTS_ROOT"
ENV_KOA_BACKUPS_ROOT = "KOA_BACKUPS_ROOT"
ENV_KOA_LOGS_ROOT = "KOA_LOGS_ROOT"
ENV_KOA_CONFIG_PATH = "KOA_CONFIG_PATH"
ENV_KOA_ACTOR = "KOA_ACTOR"
ENV_KOA_COPY_MODE = "KOA_COPY_MODE"
ENV_KOA_ALLOW_HUMAN_VERIFIED_OVERRIDE = "KOA_ALLOW_HUMAN_VERIFIED_OVERRIDE"
ENV_KOA_AUTO_CREATE_DIRECTORIES = "KOA_AUTO_CREATE_DIRECTORIES"


TRUE_ENV_VALUES = {"1", "true", "yes", "y", "oui", "on"}
FALSE_ENV_VALUES = {"0", "false", "no", "n", "non", "off", ""}


@dataclass(frozen=True)
class KoaSettings:
    """Resolved local settings for Médiathèque kOA."""

    root_path: Path
    db_path: Path
    storage_root: Path
    imports_root: Path
    exports_root: Path
    tools_root: Path
    gui_root: Path
    backups_root: Path
    logs_root: Path
    docs_root: Path
    schema_dir: Path

    app_component: str = APP_COMPONENT
    app_language: str = APP_PRIMARY_LANGUAGE
    default_filearea: str = DEFAULT_FILEAREA
    copy_mode: str = COPY_MODE_COPY_TO_STORAGE
    actor: str = "local_user"

    allow_human_verified_override: bool = False
    auto_create_directories: bool = True

    config_path: Path | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return settings as a JSON-serializable dictionary."""
        result: dict[str, Any] = {}

        for key, value in asdict(self).items():
            if isinstance(value, Path):
                result[key] = str(value)
            else:
                result[key] = value

        return result

    def with_overrides(self, **overrides: Any) -> "KoaSettings":
        """Return a new settings object with explicit field overrides."""
        data = self.as_dict()
        data.update(overrides)
        return build_settings_from_mapping(data)

    def required_directories(self) -> tuple[Path, ...]:
        """Return directories that should exist before normal app operation."""
        return (
            self.root_path,
            self.db_path.parent,
            self.storage_root,
            self.imports_root,
            self.exports_root,
            self.tools_root,
            self.gui_root,
            self.backups_root,
            self.logs_root,
            self.docs_root,
            self.schema_dir,
        )


def get_default_root_path(start_path: str | Path | None = None) -> Path:
    """
    Resolve the default project root.

    If the current path is already inside a KOA_MEDIATHEQUE tree, the existing
    ancestor named KOA_MEDIATHEQUE is used. Otherwise, the supplied path/current
    working directory is used directly when it is named KOA_MEDIATHEQUE, or a
    KOA_MEDIATHEQUE child directory is returned.
    """
    base = Path(start_path or os.getcwd()).expanduser().resolve()

    if base.name == KOA_ROOT:
        return base

    for parent in base.parents:
        if parent.name == KOA_ROOT:
            return parent

    return base / KOA_ROOT


def get_default_settings(root_path: str | Path | None = None) -> KoaSettings:
    """Return settings for one app plus its adjacent content workspace."""
    root = get_default_root_path(root_path)
    content_env = os.environ.get(ENV_KOA_CONTENT_ROOT)
    content = Path(content_env).expanduser().resolve() if content_env else (root.parent / "content").resolve()

    return KoaSettings(
        root_path=root,
        db_path=content / KOA_DB_DIR / APP_DB_FILENAME,
        storage_root=content / KOA_STORAGE_DIR,
        imports_root=content / KOA_IMPORTS_DIR,
        exports_root=content / KOA_EXPORTS_DIR,
        tools_root=root / KOA_TOOLS_DIR,
        gui_root=root / KOA_GUI_DIR,
        backups_root=content / KOA_BACKUPS_DIR,
        logs_root=content / KOA_LOGS_DIR,
        docs_root=root / KOA_DOCS_DIR,
        schema_dir=root / "schemas" / "sqlite",
    )


def load_settings(
    config_path: str | Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
    overrides: Mapping[str, Any] | None = None,
) -> KoaSettings:
    """
    Load settings from defaults, optional TOML, environment, and overrides.

    This function does not create directories and does not validate database
    existence. It only resolves configuration values.
    """
    environment = dict(os.environ if env is None else env)

    resolved_config_path = _resolve_config_path(config_path, environment)
    config_data = _load_toml_config(resolved_config_path)

    root_value = (
        _get_nested_value(config_data, "paths", "root_path")
        or environment.get(ENV_KOA_ROOT)
        or None
    )

    settings = get_default_settings(root_value)

    settings = _apply_config_mapping(settings, config_data)
    settings = _apply_environment_overrides(settings, environment)

    if overrides:
        settings = settings.with_overrides(**dict(overrides))

    if resolved_config_path:
        settings = settings.with_overrides(config_path=resolved_config_path)

    validate_settings(settings)
    return settings


def validate_settings(settings: KoaSettings) -> None:
    """Validate settings values that must remain within controlled contracts."""
    if settings.copy_mode not in COPY_MODE_VALUES:
        allowed = ", ".join(COPY_MODE_VALUES)
        raise ValueError(f"Invalid copy_mode: {settings.copy_mode!r}. Allowed: {allowed}")

    if not settings.root_path:
        raise ValueError("root_path is required")

    if not settings.db_path.name:
        raise ValueError("db_path must include a SQLite filename")

    if settings.db_path.suffix.lower() not in {".sqlite", ".db", ".sqlite3"}:
        raise ValueError("db_path must point to a SQLite database file")

    if not settings.actor.strip():
        raise ValueError("actor must not be empty")


def ensure_settings_directories(settings: KoaSettings) -> None:
    """
    Create required directories for normal operation.

    This function is explicit by design. Importing or loading settings must not
    write to disk.
    """
    for directory in settings.required_directories():
        directory.mkdir(parents=True, exist_ok=True)


def build_settings_from_mapping(data: Mapping[str, Any]) -> KoaSettings:
    """Build KoaSettings from a flat mapping of field names to values."""
    return KoaSettings(
        root_path=_to_path(data["root_path"]),
        db_path=_to_path(data["db_path"]),
        storage_root=_to_path(data["storage_root"]),
        imports_root=_to_path(data["imports_root"]),
        exports_root=_to_path(data["exports_root"]),
        tools_root=_to_path(data["tools_root"]),
        gui_root=_to_path(data["gui_root"]),
        backups_root=_to_path(data["backups_root"]),
        logs_root=_to_path(data["logs_root"]),
        docs_root=_to_path(data["docs_root"]),
        schema_dir=_to_path(data["schema_dir"]),
        app_component=str(data.get("app_component", APP_COMPONENT)),
        app_language=str(data.get("app_language", APP_PRIMARY_LANGUAGE)),
        default_filearea=str(data.get("default_filearea", DEFAULT_FILEAREA)),
        copy_mode=str(data.get("copy_mode", COPY_MODE_COPY_TO_STORAGE)),
        actor=str(data.get("actor", "local_user")),
        allow_human_verified_override=_to_bool(
            data.get("allow_human_verified_override", False)
        ),
        auto_create_directories=_to_bool(data.get("auto_create_directories", True)),
        config_path=_to_optional_path(data.get("config_path")),
    )


def _resolve_config_path(
    config_path: str | Path | None,
    environment: Mapping[str, str],
) -> Path | None:
    value = config_path or environment.get(ENV_KOA_CONFIG_PATH)

    if not value:
        return None

    return Path(value).expanduser().resolve()


def _load_toml_config(config_path: Path | None) -> dict[str, Any]:
    if config_path is None:
        return {}

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    if tomllib is None:
        raise RuntimeError(
            "TOML config loading requires Python 3.11+ or a runtime with tomllib."
        )

    with config_path.open("rb") as handle:
        loaded = tomllib.load(handle)

    if not isinstance(loaded, dict):
        raise ValueError(f"Config file did not load as a mapping: {config_path}")

    return loaded


def _apply_config_mapping(
    settings: KoaSettings,
    config_data: Mapping[str, Any],
) -> KoaSettings:
    paths = config_data.get("paths", {})
    app = config_data.get("app", {})
    behavior = config_data.get("behavior", {})

    if not isinstance(paths, Mapping):
        raise ValueError("[paths] config section must be a mapping")
    if not isinstance(app, Mapping):
        raise ValueError("[app] config section must be a mapping")
    if not isinstance(behavior, Mapping):
        raise ValueError("[behavior] config section must be a mapping")

    root_path = _to_path(paths.get("root_path", settings.root_path))

    overrides: dict[str, Any] = {
        "root_path": root_path,
        "db_path": _resolve_config_path_value(
            paths.get("db_path"),
            default=settings.db_path,
            root_path=root_path,
        ),
        "storage_root": _resolve_config_path_value(
            paths.get("storage_root"),
            default=settings.storage_root,
            root_path=root_path,
        ),
        "imports_root": _resolve_config_path_value(
            paths.get("imports_root"),
            default=settings.imports_root,
            root_path=root_path,
        ),
        "exports_root": _resolve_config_path_value(
            paths.get("exports_root"),
            default=settings.exports_root,
            root_path=root_path,
        ),
        "tools_root": _resolve_config_path_value(
            paths.get("tools_root"),
            default=settings.tools_root,
            root_path=root_path,
        ),
        "gui_root": _resolve_config_path_value(
            paths.get("gui_root"),
            default=settings.gui_root,
            root_path=root_path,
        ),
        "backups_root": _resolve_config_path_value(
            paths.get("backups_root"),
            default=settings.backups_root,
            root_path=root_path,
        ),
        "logs_root": _resolve_config_path_value(
            paths.get("logs_root"),
            default=settings.logs_root,
            root_path=root_path,
        ),
        "docs_root": _resolve_config_path_value(
            paths.get("docs_root"),
            default=settings.docs_root,
            root_path=root_path,
        ),
        "schema_dir": _resolve_config_path_value(
            paths.get("schema_dir"),
            default=settings.schema_dir,
            root_path=root_path,
        ),
        "app_language": app.get("language", settings.app_language),
        "actor": app.get("actor", settings.actor),
        "copy_mode": behavior.get("copy_mode", settings.copy_mode),
        "allow_human_verified_override": behavior.get(
            "allow_human_verified_override",
            settings.allow_human_verified_override,
        ),
        "auto_create_directories": behavior.get(
            "auto_create_directories",
            settings.auto_create_directories,
        ),
    }

    return settings.with_overrides(**overrides)


def _apply_environment_overrides(
    settings: KoaSettings,
    environment: Mapping[str, str],
) -> KoaSettings:
    overrides: dict[str, Any] = {}

    if ENV_KOA_ROOT in environment:
        root_path = _to_path(environment[ENV_KOA_ROOT])
        overrides["root_path"] = root_path

    root_for_relative_paths = _to_path(overrides.get("root_path", settings.root_path))

    if ENV_KOA_CONTENT_ROOT in environment:
        content_root = _to_path(environment[ENV_KOA_CONTENT_ROOT])
        overrides.update({
            "db_path": content_root / KOA_DB_DIR / APP_DB_FILENAME,
            "storage_root": content_root / KOA_STORAGE_DIR,
            "imports_root": content_root / KOA_IMPORTS_DIR,
            "exports_root": content_root / KOA_EXPORTS_DIR,
            "backups_root": content_root / KOA_BACKUPS_DIR,
            "logs_root": content_root / KOA_LOGS_DIR,
        })

    env_path_map = {
        ENV_KOA_DB_PATH: "db_path",
        ENV_KOA_STORAGE_ROOT: "storage_root",
        ENV_KOA_IMPORTS_ROOT: "imports_root",
        ENV_KOA_EXPORTS_ROOT: "exports_root",
        ENV_KOA_BACKUPS_ROOT: "backups_root",
        ENV_KOA_LOGS_ROOT: "logs_root",
    }

    for env_key, field_name in env_path_map.items():
        if env_key in environment:
            overrides[field_name] = _resolve_path(
                environment[env_key],
                root_path=_to_path(environment.get(ENV_KOA_CONTENT_ROOT, root_for_relative_paths)),
            )

    if ENV_KOA_ACTOR in environment:
        overrides["actor"] = environment[ENV_KOA_ACTOR]

    if ENV_KOA_COPY_MODE in environment:
        overrides["copy_mode"] = environment[ENV_KOA_COPY_MODE]

    if ENV_KOA_ALLOW_HUMAN_VERIFIED_OVERRIDE in environment:
        overrides["allow_human_verified_override"] = _to_bool(
            environment[ENV_KOA_ALLOW_HUMAN_VERIFIED_OVERRIDE]
        )

    if ENV_KOA_AUTO_CREATE_DIRECTORIES in environment:
        overrides["auto_create_directories"] = _to_bool(
            environment[ENV_KOA_AUTO_CREATE_DIRECTORIES]
        )

    if not overrides:
        return settings

    return settings.with_overrides(**overrides)


def _resolve_config_path_value(
    value: Any,
    *,
    default: Path,
    root_path: Path,
) -> Path:
    if value is None:
        return default

    return _resolve_path(value, root_path=root_path)


def _resolve_path(value: Any, *, root_path: Path) -> Path:
    path = _to_path(value)

    if path.is_absolute():
        return path

    return (root_path / path).resolve()


def _to_path(value: Any) -> Path:
    if isinstance(value, Path):
        return value.expanduser().resolve()

    return Path(str(value)).expanduser().resolve()


def _to_optional_path(value: Any) -> Path | None:
    if value is None or value == "":
        return None

    return _to_path(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return bool(value)

    normalized = str(value).strip().lower()

    if normalized in TRUE_ENV_VALUES:
        return True

    if normalized in FALSE_ENV_VALUES:
        return False

    raise ValueError(f"Cannot parse boolean value: {value!r}")


def _get_nested_value(
    mapping: Mapping[str, Any],
    section: str,
    key: str,
) -> Any | None:
    section_value = mapping.get(section)

    if not isinstance(section_value, Mapping):
        return None

    return section_value.get(key)


__all__ = [
    "ENV_KOA_ACTOR",
    "ENV_KOA_ALLOW_HUMAN_VERIFIED_OVERRIDE",
    "ENV_KOA_AUTO_CREATE_DIRECTORIES",
    "ENV_KOA_BACKUPS_ROOT",
    "ENV_KOA_CONFIG_PATH",
    "ENV_KOA_COPY_MODE",
    "ENV_KOA_DB_PATH",
    "ENV_KOA_EXPORTS_ROOT",
    "ENV_KOA_IMPORTS_ROOT",
    "ENV_KOA_LOGS_ROOT",
    "ENV_KOA_ROOT",
    "ENV_KOA_CONTENT_ROOT",
    "ENV_KOA_STORAGE_ROOT",
    "KoaSettings",
    "build_settings_from_mapping",
    "ensure_settings_directories",
    "get_default_root_path",
    "get_default_settings",
    "load_settings",
    "validate_settings",
]