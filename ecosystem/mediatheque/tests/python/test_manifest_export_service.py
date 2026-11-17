# tests/python/test_manifest_export_service.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from koa_mediatheque.services import manifest_export_service as svc


def test_build_manifest_dict_includes_required_manifest_sections() -> None:
    rows = [_sample_row()]

    manifest = svc.build_manifest_dict(
        rows,
        export_uuid="export-uuid-001",
        export_type="koa_manifest",
        actor="tester",
        reason="unit test",
    )

    assert manifest["app_name"] == "Médiathèque kOA"
    assert manifest["app_component"] == "koa_mediatheque"
    assert manifest["manifest_filename"] == "manifest.json"
    assert manifest["export_uuid"] == "export-uuid-001"
    assert manifest["export_type"] == "koa_manifest"
    assert manifest["export_actor"] == "tester"
    assert manifest["export_reason"] == "unit test"
    assert manifest["row_count"] == 1

    assert manifest["media_uuids"] == ["media-uuid-001"]
    assert manifest["version_uuids"] == ["version-uuid-001"]
    assert manifest["file_hashes"] == ["abc123"]
    assert manifest["mime_types"] == ["application/pdf"]

    assert manifest["collections"] == ["collection_a", "collection_b"]
    assert manifest["tags"] == ["tag_a", "tag_b"]
    assert manifest["relations"] == ["references:media-uuid-002"]
    assert manifest["content_flags"] == ["requires_context"]

    row = manifest["rows"][0]
    assert row["media_uuid"] == "media-uuid-001"
    assert row["version_uuid"] == "version-uuid-001"
    assert row["file"]["sha256"] == "abc123"
    assert row["classification"]["target_system"] == "uckkarchive"
    assert row["access"]["visibility"] == "private"
    assert row["source_and_rights"]["rights_status"] == "owned"
    assert row["restriction_and_sensitivity"]["audience_suitability"] == "general"
    assert row["validation"]["canonical_validation_state"] == "unverified"
    assert row["export_policy"]["export_to_uckk"] == "yes"


def test_export_manifest_writes_manifest_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [_sample_row()]
    audit_calls: list[dict[str, Any]] = []

    monkeypatch.setattr(svc, "list_library_rows", lambda connection, filters=None: rows)
    monkeypatch.setattr(svc, "utc_now_iso", lambda: "2026-06-15T12:00:00Z")

    def fake_write_audit_log(connection, **kwargs):
        audit_calls.append(kwargs)
        return None

    monkeypatch.setattr(svc, "write_audit_log", fake_write_audit_log)

    result = svc.export_manifest(
        object(),
        tmp_path,
        export_type="koa_manifest",
        filters={"status": "active"},
        actor="tester",
        reason="test export",
    )

    assert result.errors == []
    assert result.export_type == "koa_manifest"
    assert result.row_count == 1
    assert result.manifest_path == str(tmp_path / "manifest.json")

    manifest_path = Path(result.manifest_path)
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["export_timestamp"] == "2026-06-15T12:00:00Z"
    assert manifest["filters"] == {"status": "active"}
    assert manifest["source_row_count"] == 1
    assert manifest["excluded_row_count"] == 0
    assert manifest["rows"][0]["version_uuid"] == "version-uuid-001"

    assert len(audit_calls) == 1
    assert audit_calls[0]["action"] == "manifest_exported"
    assert audit_calls[0]["entity_type"] == "manifest_export"
    assert audit_calls[0]["actor"] == "tester"


def test_export_manifest_rejects_invalid_export_type(tmp_path: Path) -> None:
    result = svc.export_manifest(
        object(),
        tmp_path,
        export_type="bad_export_type",
    )

    assert result.row_count == 0
    assert result.export_type == "bad_export_type"
    assert result.errors
    assert result.errors[0].code == "ERR_INVALID_EXPORT_TYPE"
    assert result.errors[0].severity == "blocking"
    assert not Path(result.manifest_path).exists()


def test_export_manifest_blocks_public_review_package_when_policy_blocks_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        _sample_row(
            version_uuid="version-uuid-blocked-public",
            export_to_public="no",
            public_state="private",
            visibility="private",
        )
    ]

    monkeypatch.setattr(svc, "list_library_rows", lambda connection, filters=None: rows)
    monkeypatch.setattr(svc, "is_public_export_blocked", lambda row: True)

    result = svc.export_manifest(
        object(),
        tmp_path,
        export_type="public_review_package",
    )

    assert result.row_count == 0
    assert result.errors
    assert result.errors[0].code == "ERR_MANIFEST_EXPORT_BLOCKED"
    assert "version-uuid-blocked-public" in result.errors[0].details["blocked_version_uuids"]
    assert not Path(result.manifest_path).exists()


def test_export_manifest_blocks_uckkarchive_candidate_when_policy_blocks_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        _sample_row(
            version_uuid="version-uuid-blocked-uckk",
            export_to_uckk="no",
            target_system="none",
            target_export_allowed=0,
        )
    ]

    monkeypatch.setattr(svc, "list_library_rows", lambda connection, filters=None: rows)
    monkeypatch.setattr(svc, "is_uckk_export_blocked", lambda row: True)

    result = svc.export_manifest(
        object(),
        tmp_path,
        export_type="uckkarchive_candidate",
    )

    assert result.row_count == 0
    assert result.errors
    assert result.errors[0].code == "ERR_MANIFEST_EXPORT_BLOCKED"
    assert "version-uuid-blocked-uckk" in result.errors[0].details["blocked_version_uuids"]
    assert not Path(result.manifest_path).exists()


def test_export_manifest_allows_koa_manifest_without_export_policy_filtering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        _sample_row(
            version_uuid="version-uuid-private",
            export_to_uckk="no",
            export_to_public="no",
            public_state="private",
            visibility="private",
            human_review_required=1,
        )
    ]

    monkeypatch.setattr(svc, "list_library_rows", lambda connection, filters=None: rows)

    result = svc.export_manifest(
        object(),
        tmp_path,
        export_type="koa_manifest",
    )

    assert result.errors == []
    assert result.row_count == 1

    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
    assert manifest["rows"][0]["version_uuid"] == "version-uuid-private"
    assert manifest["restricted_flags"]["human_review_required_count"] == 1


def test_build_manifest_dict_summarizes_restricted_flags() -> None:
    rows = [
        _sample_row(
            version_uuid="version-uuid-restricted",
            restriction_state="privacy",
            visibility="restricted",
            access_level="confidential",
            redaction_required=1,
            human_review_required=1,
        ),
        _sample_row(
            media_uuid="media-uuid-002",
            version_uuid="version-uuid-open",
            sha256="def456",
            restriction_state="none",
            visibility="public",
            access_level="public",
            redaction_required=0,
            human_review_required=0,
        ),
    ]

    manifest = svc.build_manifest_dict(
        rows,
        export_uuid="export-uuid-002",
        export_type="koa_manifest",
        actor="tester",
        reason="restricted summary test",
    )

    restricted_flags = manifest["restricted_flags"]

    assert restricted_flags["restricted_count"] == 1
    assert restricted_flags["redaction_required_count"] == 1
    assert restricted_flags["human_review_required_count"] == 1
    assert restricted_flags["restriction_states"] == ["privacy"]
    assert restricted_flags["restricted_version_uuids"] == ["version-uuid-restricted"]


def test_build_manifest_dict_tolerates_semicolon_json_fields() -> None:
    rows = [
        _sample_row(
            collections_json="collection_a; collection_b",
            tags_json="tag_a; tag_b",
            relations_json="references:media-uuid-002",
            content_flags_json="requires_context; copyright_uncertain",
        )
    ]

    manifest = svc.build_manifest_dict(
        rows,
        export_uuid="export-uuid-003",
        export_type="koa_manifest",
        actor="tester",
        reason="semicolon parsing test",
    )

    assert manifest["collections"] == ["collection_a", "collection_b"]
    assert manifest["tags"] == ["tag_a", "tag_b"]
    assert manifest["relations"] == ["references:media-uuid-002"]
    assert manifest["content_flags"] == ["copyright_uncertain", "requires_context"]

    row = manifest["rows"][0]
    assert row["collections"] == ["collection_a", "collection_b"]
    assert row["tags"] == ["tag_a", "tag_b"]
    assert row["relations"] == ["references:media-uuid-002"]
    assert row["restriction_and_sensitivity"]["content_flags"] == [
        "requires_context",
        "copyright_uncertain",
    ]


def _sample_row(**overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": 1,
        "media_uuid": "media-uuid-001",
        "version_uuid": "version-uuid-001",
        "title": "Document test",
        "subtitle": "Sous-titre test",
        "description": "Description test",
        "summary": "Résumé test",
        "original_path": "/tmp/original.pdf",
        "storage_path": "/tmp/storage/media_original/version-uuid-001.pdf",
        "filename": "original.pdf",
        "extension": ".pdf",
        "mimetype": "application/pdf",
        "filesize": 1234,
        "sha256": "abc123",
        "filearea": "media_original",
        "media_type": "pdf",
        "language": "fr",
        "library_scope": "koa",
        "uckk_relevance": "uckk_related",
        "target_system": "uckkarchive",
        "target_export_allowed": 1,
        "public_state": "non_public",
        "visibility": "private",
        "access_level": "private",
        "ownership_scope": "uckk_owned",
        "source_type": "produced_by_uckk",
        "source_ownership": "uckk_created",
        "rights_status": "owned",
        "rights_note": "Droits test.",
        "restriction_state": "none",
        "restriction_reason": None,
        "redaction_required": 0,
        "status": "active",
        "provenance": "ai_assisted",
        "ai_validation_state": "ai_classified_needs_review",
        "ai_confidence": 0.8,
        "canonical_validation_state": "unverified",
        "human_review_required": 0,
        "review_queue": None,
        "review_reason": None,
        "collections_json": json.dumps(["collection_a", "collection_b"], ensure_ascii=False),
        "tags_json": json.dumps(["tag_a", "tag_b"], ensure_ascii=False),
        "relations_json": json.dumps(["references:media-uuid-002"], ensure_ascii=False),
        "content_flags_json": json.dumps(["requires_context"], ensure_ascii=False),
        "audience_suitability": "general",
        "export_to_uckk": "yes",
        "export_to_public": "no",
        "export_policy_note": "Export UCKK seulement après revue.",
        "import_batch": "batch-001",
        "notes": "Note test.",
        "created_at": "2026-06-15T10:00:00Z",
        "updated_at": "2026-06-15T11:00:00Z",
    }

    row.update(overrides)
    return row