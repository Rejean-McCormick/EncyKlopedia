"""Spek vNext: deterministic, typed, recursive template composition.

The composition API NEVER selects facts, writes prose, or grants publication.
"""
from .engine import (
    DEFINITIONS_FORMAT, INSTANCE_FORMAT, Library, resolve, dialogue_plan,
    render_html, render_markdown, materialize,
)
__all__ = ['DEFINITIONS_FORMAT', 'INSTANCE_FORMAT', 'Library', 'resolve',
           'dialogue_plan', 'render_html', 'render_markdown', 'materialize']
