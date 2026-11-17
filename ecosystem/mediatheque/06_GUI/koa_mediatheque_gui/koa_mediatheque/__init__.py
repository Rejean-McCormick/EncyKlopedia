"""
Médiathèque kOA package.

This package contains the local SQLite/Streamlit implementation for the
`koa-mediatheque` application.

Public constants, controlled values, paths, validation rules, and settings are
defined in dedicated modules. This package initializer intentionally keeps only
lightweight package metadata so importing `koa_mediatheque` has no side effects.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _distribution_version

_DISTRIBUTION_NAME = "koa-mediatheque"


def _get_package_version() -> str:
    """Return the installed package version, or a local development fallback."""
    try:
        return _distribution_version(_DISTRIBUTION_NAME)
    except PackageNotFoundError:
        return "0.5.1"


__version__ = _get_package_version()

__all__ = [
    "__version__",
]