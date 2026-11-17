# 06_GUI/koa_mediatheque_gui/koa_mediatheque/ui/__init__.py
from __future__ import annotations

from importlib import import_module
from typing import Any


__all__ = [
    "configure_page",
    "render_sidebar_settings",
    "render_operation_result",
    "render_path_input",
    "render_copy_button",
    "render_result_messages",
    "render_library_filters",
    "apply_dataframe_filters",
    "render_file_preview",
    "render_file_actions",
    "render_row_editor",
    "render_row_save_button",
    "render_validation_result",
    "render_import_preview",
    "render_audit_log",
    "render_chatgpt_intake_log",
    "render_xlsx_import_log",
]


_EXPORT_MAP: dict[str, tuple[str, str]] = {
    "configure_page": ("koa_mediatheque.ui.layout", "configure_page"),
    "render_sidebar_settings": ("koa_mediatheque.ui.layout", "render_sidebar_settings"),
    "render_operation_result": ("koa_mediatheque.ui.layout", "render_operation_result"),
    "render_path_input": ("koa_mediatheque.ui.widgets", "render_path_input"),
    "render_copy_button": ("koa_mediatheque.ui.widgets", "render_copy_button"),
    "render_result_messages": ("koa_mediatheque.ui.widgets", "render_result_messages"),
    "render_library_filters": ("koa_mediatheque.ui.table_filters", "render_library_filters"),
    "apply_dataframe_filters": ("koa_mediatheque.ui.table_filters", "apply_dataframe_filters"),
    "render_file_preview": ("koa_mediatheque.ui.file_preview", "render_file_preview"),
    "render_file_actions": ("koa_mediatheque.ui.file_preview", "render_file_actions"),
    "render_row_editor": ("koa_mediatheque.ui.row_editor", "render_row_editor"),
    "render_row_save_button": ("koa_mediatheque.ui.row_editor", "render_row_save_button"),
    "render_validation_result": ("koa_mediatheque.ui.validation_panel", "render_validation_result"),
    "render_import_preview": ("koa_mediatheque.ui.validation_panel", "render_import_preview"),
    "render_audit_log": ("koa_mediatheque.ui.log_viewer", "render_audit_log"),
    "render_chatgpt_intake_log": ("koa_mediatheque.ui.log_viewer", "render_chatgpt_intake_log"),
    "render_xlsx_import_log": ("koa_mediatheque.ui.log_viewer", "render_xlsx_import_log"),
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORT_MAP:
        raise AttributeError(f"module 'koa_mediatheque.ui' has no attribute {name!r}")

    module_name, attribute_name = _EXPORT_MAP[name]
    module = import_module(module_name)
    value = getattr(module, attribute_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))