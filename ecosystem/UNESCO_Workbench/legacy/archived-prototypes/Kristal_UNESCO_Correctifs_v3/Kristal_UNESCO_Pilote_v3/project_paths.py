# -*- coding: utf-8 -*-
"""Known project paths corroborated by the supplied Windows diagnostic.

These are paths to *existing source/runtime assets*, not a claim that the
UNESCO grammar has been compiled.  No environment mutation or disk scan.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

KRISTAL_ROOT = Path(r'C:\mycode\Kristal')
SEMANTIK_WORKSPACE = Path(r'C:\mycode\SemantiK_Architect')
SEMANTIK_PROJECT = SEMANTIK_WORKSPACE / 'SemantiK_Architect'
ENCYKLOPEDIA_ROOT = Path(r'D:\EncyKlopedia')
KONSTELLATION_PGF_REL = Path('runtime/konstellation-fr-3/grammar.pgf')
GF_ADAPTER_REL = Path('src/semantik_architect/adapters/realization/gf/pgf_runtime.py')


def resolve_semantik_project(path: str | Path) -> Path:
    """Accept either workspace parent or the actual SemantiK project."""
    value = Path(path).expanduser()
    if (value / 'src' / 'semantik_architect').is_dir():
        return value
    nested = value / 'SemantiK_Architect'
    if (nested / 'src' / 'semantik_architect').is_dir():
        return nested
    # Even before the project is mounted, preserve a concrete, non-nested path.
    if value.name.lower() == 'semantik_architect':
        return value if (value / 'runtime').exists() else nested if (nested / 'runtime').exists() else value
    return nested


def default_python() -> str:
    """Prefer Python 3.12 from the Windows diagnostic, then current Python."""
    if os.name == 'nt':
        candidate = Path.home() / 'AppData/Local/Programs/Python/Python312/python.exe'
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def runtime_paths(semantik_project: str | Path) -> dict[str, str]:
    sa = resolve_semantik_project(semantik_project)
    return {
        'semantik_project': str(sa),
        'pgf_fr': str(sa / KONSTELLATION_PGF_REL),
        'pgf_adapter': str(sa / GF_ADAPTER_REL),
        'gf_wordbench': str(sa.parent / 'GF_Wordbench'),
        'runtime_manifest': str(sa / 'runtime/konstellation-fr-3/runtime.manifest.json'),
    }
