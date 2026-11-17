"""
Duplicate detection service for Médiathèque kOA.

Duplicate detection is based on locally calculated sha256 values. ChatGPT and
XLSX values must not be trusted as file facts.
"""

from __future__ import annotations

from typing import Any

from koa_mediatheque.errors import WARN_DUPLICATE_SHA256
from koa_mediatheque.models import FileFacts, KoaMessage
from koa_mediatheque.repositories.library_rows_repository import (
    get_library_rows_by_sha256,
)


def find_exact_duplicates_by_sha256(
    connection,
    sha256: str,
) -> list[dict[str, Any]]:
    """
    Return existing library rows with the same sha256.

    Empty or missing sha256 values return an empty list because external
    references and unavailable files cannot be exact-file deduplicated.
    """
    hash_value = str(sha256 or "").strip().lower()

    if not hash_value:
        return []

    return get_library_rows_by_sha256(connection, hash_value)


def build_duplicate_warnings(
    connection,
    file_facts: FileFacts,
) -> list[KoaMessage]:
    """
    Build warnings for exact sha256 duplicates.

    Returns:
        list[KoaMessage]: empty when no duplicate is found.
    """
    if not file_facts.sha256:
        return []

    duplicates = find_exact_duplicates_by_sha256(connection, file_facts.sha256)

    if not duplicates:
        return []

    duplicate_refs = [
        {
            "id": row.get("id"),
            "media_uuid": row.get("media_uuid"),
            "version_uuid": row.get("version_uuid"),
            "title": row.get("title"),
            "filename": row.get("filename"),
            "storage_path": row.get("storage_path"),
            "original_path": row.get("original_path"),
        }
        for row in duplicates
    ]

    return [
        KoaMessage(
            code=WARN_DUPLICATE_SHA256,
            severity="warning",
            message=(
                "An existing library row has the same sha256. "
                "This may be an exact duplicate or another version of the same file."
            ),
            field="sha256",
            details={
                "sha256": file_facts.sha256,
                "duplicate_count": len(duplicates),
                "duplicates": duplicate_refs,
            },
        )
    ]