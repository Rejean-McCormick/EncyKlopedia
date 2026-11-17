from __future__ import annotations

import json
from pathlib import Path

from koa_mediatheque.repositories.library_rows_repository import (
    get_library_row_by_version_uuid,
    insert_library_row,
)
from koa_mediatheque.services import kristal_media_bridge_service as svc


def test_make_and_detect_kristal_relation() -> None:
    relation = svc.make_kristal_relation("State", "state-123")
    assert relation == "kristal:state:state-123"

    row = {"relations_json": json.dumps([relation, "references:media-2"])}
    assert svc.is_kristal_linked(row) is True
    assert svc.get_kristal_relations(row) == [relation]


def test_link_media_to_kristal_updates_existing_library_row(
    initialized_connection,
    sample_library_row_data,
) -> None:
    inserted = insert_library_row(initialized_connection, sample_library_row_data)
    assert inserted.success is True

    result = svc.link_media_to_kristal(
        initialized_connection,
        sample_library_row_data["version_uuid"],
        relation_kind="state",
        relation_id="kristal-state-001",
        actor="tester",
    )

    assert result.success is True
    assert result.result == "linked"
    assert result.data["relation"] == "kristal:state:kristal-state-001"

    row = get_library_row_by_version_uuid(
        initialized_connection,
        sample_library_row_data["version_uuid"],
    )
    assert row is not None
    relations = json.loads(row["relations_json"])
    assert "kristal:state:kristal-state-001" in relations


def test_build_artifact_ref_uses_opaque_locator_and_no_local_path(
    sample_library_row_data,
) -> None:
    row = dict(sample_library_row_data)
    row["storage_path"] = "/private/koa/storage/media_original/example.txt"
    row["relations_json"] = '["kristal:state:kristal-state-001"]'

    artifact_ref = svc.build_artifact_ref(row)

    assert artifact_ref["owner"]["system"] == "koa_mediatheque"
    assert artifact_ref["artifact_type"] == "koa.media"
    assert artifact_ref["artifact_id"].startswith("urn:koa-mediatheque:media:")
    assert artifact_ref["version"] == row["version_uuid"]
    assert artifact_ref["integrity"] == {
        "algorithm": "sha256",
        "digest": row["sha256"],
    }
    assert artifact_ref["locator"]["ref"].startswith("koa-media://version/")
    rendered = json.dumps(artifact_ref, ensure_ascii=False)
    assert row["original_path"] not in rendered
    assert row["storage_path"] not in rendered


def test_build_export_manifest_validates_against_pinned_ik_schema(
    sample_library_row_data,
) -> None:
    row = dict(sample_library_row_data)
    row["relations_json"] = '["kristal:referent:kr-ref-001"]'

    manifest = svc.build_export_manifest(
        [row],
        export_uuid="export-001",
        snapshot_at="2026-10-02T03:00:00Z",
        source_revision="library_rows@test",
    )

    assert manifest["profile"] == svc.BRIDGE_PROFILE
    assert manifest["producer"]["system"] == "koa_mediatheque"
    assert manifest["subjects"][0]["type"] == "media"
    assert manifest["items"][0]["digest"] == f"sha256:{row['sha256']}"
    assert manifest["integrity"]["algorithm"] == "sha256"
    assert manifest["integrity"]["digest"].startswith("sha256:")
    assert len(manifest["integrity"]["digest"]) == len("sha256:") + 64


def test_export_kristal_media_bundle_filters_to_explicit_links(
    initialized_connection,
    sample_library_row_data,
    tmp_path: Path,
) -> None:
    linked = dict(sample_library_row_data)
    linked["relations_json"] = '["kristal:state:kristal-state-001"]'
    assert insert_library_row(initialized_connection, linked).success is True

    unlinked = dict(sample_library_row_data)
    unlinked["media_uuid"] = "33333333-3333-4333-8333-333333333333"
    unlinked["version_uuid"] = "44444444-4444-4444-8444-444444444444"
    unlinked["sha256"] = "1" * 64
    unlinked["relations_json"] = "[]"
    assert insert_library_row(initialized_connection, unlinked).success is True

    result = svc.export_kristal_media_bundle(
        initialized_connection,
        tmp_path,
        actor="tester",
        reason="bridge test",
    )

    assert result.success is True
    assert result.data["row_count"] == 1
    assert result.data["source_row_count"] == 2

    manifest_path = Path(result.data["manifest_path"])
    refs_path = Path(result.data["artifact_refs_path"])
    assert manifest_path.exists()
    assert refs_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    refs = json.loads(refs_path.read_text(encoding="utf-8"))
    assert len(manifest["items"]) == 1
    assert len(refs["artifact_refs"]) == 1
    assert linked["version_uuid"] in refs["artifact_refs"][0]["locator"]["ref"]


def test_export_kristal_media_bundle_fails_closed_without_valid_hash(
    initialized_connection,
    sample_library_row_data,
    tmp_path: Path,
) -> None:
    row = dict(sample_library_row_data)
    row["sha256"] = "not-a-real-hash"
    row["relations_json"] = '["kristal:state:kristal-state-001"]'
    assert insert_library_row(initialized_connection, row).success is True

    result = svc.export_kristal_media_bundle(initialized_connection, tmp_path)

    assert result.success is False
    assert result.result == "invalid_linked_media"
    assert result.errors[0].code == "ERR_KRISTAL_EXPORT_INTEGRITY"
    assert not (tmp_path / svc.EXPORT_MANIFEST_FILENAME).exists()


def test_resolve_koa_media_locator_stays_local(
    initialized_connection,
    sample_library_row_data,
) -> None:
    assert insert_library_row(initialized_connection, sample_library_row_data).success is True
    locator = f"{svc.LOCATOR_PREFIX}{sample_library_row_data['version_uuid']}"

    row = svc.resolve_koa_media_locator(initialized_connection, locator)

    assert row is not None
    assert row["version_uuid"] == sample_library_row_data["version_uuid"]


def test_bridge_jcs_matches_kristal_v6_rfc8785_vector() -> None:
    value = {
        "numbers": [333333333.3333333, 1e30, 4.5, 0.002, 1e-27],
        "string": "€$\x0f\nA'B\"" + "\\\\" + "\"/",
        "literals": [None, True, False],
    }
    canonical = svc._jcs_canonicalize(value)

    import hashlib

    assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == (
        "2d5e01a318d0f0879ab568c4be289c8b1f64ef8921a53c6277d5e069978baacb"
    )


def test_bridge_declares_current_ik_daat_and_kristall_baselines(
    sample_library_row_data,
) -> None:
    row = dict(sample_library_row_data)
    row["relations_json"] = '["kristal:state:kristal-state-001"]'

    manifest = svc.build_export_manifest(
        [row],
        export_uuid="export-baselines",
        snapshot_at="2026-10-03T18:00:00Z",
    )

    provenance = manifest["provenance"]
    assert provenance["interaction_kernel"] == "2.0.0-dev.2"
    assert provenance["interaction_kernel_schema"] == "1.1"
    assert provenance["kristal_portable_contract"] == "kristal_state/6.0"
    assert provenance["kristal_portable_standard"] == "6.0.0"
    assert provenance["kristall_design_baseline"] == "7.0.0-draft.3.2"
    assert provenance["daat"] == {"human_name": "DaaT", "system": "daat"}
