"""
Service layer for Médiathèque kOA.

This package contains local application services for file facts, storage,
duplicates, audit logging, backups, repairs, and operating-system file actions.

Public service handles are defined in the project internal contract. Do not
rename exported functions without updating that contract.
"""

from koa_mediatheque.services.audit_service import write_audit_log
from koa_mediatheque.services.backup_service import backup_database
from koa_mediatheque.services.duplicate_service import (
    build_duplicate_warnings,
    find_exact_duplicates_by_sha256,
)
from koa_mediatheque.services.file_facts import (
    calculate_sha256,
    detect_mimetype,
    get_file_facts,
    is_external_reference_path,
)

from koa_mediatheque.services.kristal_media_bridge_service import (
    build_artifact_ref,
    build_export_manifest,
    export_kristal_media_bundle,
    get_kristal_relations,
    is_kristal_linked,
    link_media_to_kristal,
    make_kristal_relation,
    resolve_koa_media_locator,
)

from koa_mediatheque.services.os_open_service import (
    open_file,
    open_folder,
    reveal_in_folder,
)
from koa_mediatheque.services.repair_service import (
    recalculate_file_facts_for_row,
    repair_protected_fields,
)
from koa_mediatheque.services.storage_service import (
    build_canonical_storage_filename,
    copy_into_storage,
    resolve_storage_dir,
)

__all__ = [
    "backup_database",
    "build_canonical_storage_filename",
    "build_duplicate_warnings",
    "calculate_sha256",
    "copy_into_storage",
    "detect_mimetype",
    "find_exact_duplicates_by_sha256",
    "get_file_facts",
    "is_external_reference_path",
    "open_file",
    "open_folder",
    "recalculate_file_facts_for_row",
    "repair_protected_fields",
    "resolve_storage_dir",
    "reveal_in_folder",
    "build_artifact_ref",
    "build_export_manifest",
    "export_kristal_media_bundle",
    "get_kristal_relations",
    "is_kristal_linked",
    "link_media_to_kristal",
    "make_kristal_relation",
    "resolve_koa_media_locator",
    "write_audit_log",
]