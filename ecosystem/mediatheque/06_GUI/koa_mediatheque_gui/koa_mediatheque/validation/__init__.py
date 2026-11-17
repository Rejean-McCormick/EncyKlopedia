"""
Validation package for Médiathèque kOA.

This package centralizes controlled values, blocking rules, safe defaults, and
XLSX import/export validation rules.

The package initializer intentionally uses lazy module loading so importing
`koa_mediatheque.validation` has no heavy side effects and does not duplicate
validation contracts.
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Final


_PUBLIC_MODULES: Final[tuple[str, ...]] = (
    "allowed_values",
    "blocking_rules",
    "safety_defaults",
    "xlsx_rules",
)


def __getattr__(name: str) -> ModuleType:
    """Lazily import validation submodules."""
    if name in _PUBLIC_MODULES:
        return import_module(f"{__name__}.{name}")

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Return public validation module names for interactive discovery."""
    return sorted((*globals().keys(), *_PUBLIC_MODULES))


__all__ = [
    "allowed_values",
    "blocking_rules",
    "safety_defaults",
    "xlsx_rules",
]