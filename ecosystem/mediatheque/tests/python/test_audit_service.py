from __future__ import annotations

import json

import pytest

from koa_mediatheque.errors import ERR_INVALID_ENUM
from koa_mediatheque.models import OperationResult
from koa_mediatheque.services import audit_service


def test_write_audit_log_inserts_valid_audit_entry(monkeypatch):
    captured: dict[str, object] = {}

    def fake_insert_audit_log(connection, log_data):
        captured["connection"] = connection
        captured["log_data"] = log_data
        return OperationResult(
            success=True,
            operation="",
            result="audit_log_inserted",
            entity_type=log_data["entity_type"],
            entity_uuid=log_data["entity_uuid"],
            data={"inserted": True},
        )

    monkeypatch.setattr(audit_service, "insert_audit_log", fake_insert_audit_log)
    monkeypatch.setattr(audit_service, "utc_now_iso", lambda: "2026-06-15T12:00:00Z")

    connection = object()

    result = audit_service.write_audit_log(
        connection,
        action="library_row_updated",
        entity_type="version_uuid",
        entity_uuid="version-123",
        before={"title": "Old"},
        after={"title": "New"},
        actor="tester",
        note="Updated title.",
    )

    assert result.success is True
    assert result.operation == "write_audit_log"
    assert result.result == "audit_log_inserted"
    assert result.entity_type == "version_uuid"
    assert result.entity_uuid == "version-123"

    assert captured["connection"] is connection

    log_data = captured["log_data"]
    assert log_data["action"] == "library_row_updated"
    assert log_data["entity_type"] == "version_uuid"
    assert log_data["entity_uuid"] == "version-123"
    assert log_data["actor"] == "tester"
    assert log_data["note"] == "Updated title."
    assert log_data["created_at"] == "2026-06-15T12:00:00Z"
    assert json.loads(log_data["before_json"]) == {"title": "Old"}
    assert json.loads(log_data["after_json"]) == {"title": "New"}


def test_write_audit_log_defaults_blank_actor_to_local_user(monkeypatch):
    captured: dict[str, object] = {}

    def fake_insert_audit_log(connection, log_data):
        captured["log_data"] = log_data
        return OperationResult(
            success=True,
            operation="write_audit_log",
            result="audit_log_inserted",
        )

    monkeypatch.setattr(audit_service, "insert_audit_log", fake_insert_audit_log)
    monkeypatch.setattr(audit_service, "utc_now_iso", lambda: "2026-06-15T12:00:00Z")

    result = audit_service.write_audit_log(
        object(),
        action="backup_created",
        entity_type="backup",
        actor="",
    )

    assert result.success is True
    assert captured["log_data"]["actor"] == "local_user"


def test_write_audit_log_serializes_json_with_unicode_and_sorted_keys(monkeypatch):
    captured: dict[str, object] = {}

    def fake_insert_audit_log(connection, log_data):
        captured["log_data"] = log_data
        return OperationResult(
            success=True,
            operation="write_audit_log",
            result="audit_log_inserted",
        )

    monkeypatch.setattr(audit_service, "insert_audit_log", fake_insert_audit_log)
    monkeypatch.setattr(audit_service, "utc_now_iso", lambda: "2026-06-15T12:00:00Z")

    result = audit_service.write_audit_log(
        object(),
        action="settings_updated",
        entity_type="settings",
        before={"z": "école", "a": "Médiathèque"},
        after={"z": "kOA", "a": "Médiathèque"},
    )

    assert result.success is True
    assert captured["log_data"]["before_json"] == '{"a": "Médiathèque", "z": "école"}'
    assert captured["log_data"]["after_json"] == '{"a": "Médiathèque", "z": "kOA"}'


def test_write_audit_log_allows_none_before_and_after(monkeypatch):
    captured: dict[str, object] = {}

    def fake_insert_audit_log(connection, log_data):
        captured["log_data"] = log_data
        return OperationResult(
            success=True,
            operation="write_audit_log",
            result="audit_log_inserted",
        )

    monkeypatch.setattr(audit_service, "insert_audit_log", fake_insert_audit_log)
    monkeypatch.setattr(audit_service, "utc_now_iso", lambda: "2026-06-15T12:00:00Z")

    result = audit_service.write_audit_log(
        object(),
        action="database_initialized",
        entity_type="database",
    )

    assert result.success is True
    assert captured["log_data"]["before_json"] is None
    assert captured["log_data"]["after_json"] is None


def test_write_audit_log_rejects_invalid_action(monkeypatch):
    called = False

    def fake_insert_audit_log(connection, log_data):
        nonlocal called
        called = True
        raise AssertionError("insert_audit_log should not be called")

    monkeypatch.setattr(audit_service, "insert_audit_log", fake_insert_audit_log)

    result = audit_service.write_audit_log(
        object(),
        action="not_allowed",
        entity_type="database",
    )

    assert result.success is False
    assert result.operation == "write_audit_log"
    assert result.result == "invalid_audit_log"
    assert called is False
    assert len(result.errors) == 1
    assert result.errors[0].code == ERR_INVALID_ENUM
    assert result.errors[0].field == "action"
    assert result.errors[0].severity == "error"


def test_write_audit_log_rejects_invalid_entity_type(monkeypatch):
    called = False

    def fake_insert_audit_log(connection, log_data):
        nonlocal called
        called = True
        raise AssertionError("insert_audit_log should not be called")

    monkeypatch.setattr(audit_service, "insert_audit_log", fake_insert_audit_log)

    result = audit_service.write_audit_log(
        object(),
        action="backup_created",
        entity_type="not_allowed",
    )

    assert result.success is False
    assert result.operation == "write_audit_log"
    assert result.result == "invalid_audit_log"
    assert called is False
    assert len(result.errors) == 1
    assert result.errors[0].code == ERR_INVALID_ENUM
    assert result.errors[0].field == "entity_type"
    assert result.errors[0].severity == "error"


def test_write_audit_log_rejects_invalid_action_and_invalid_entity_type(monkeypatch):
    called = False

    def fake_insert_audit_log(connection, log_data):
        nonlocal called
        called = True
        raise AssertionError("insert_audit_log should not be called")

    monkeypatch.setattr(audit_service, "insert_audit_log", fake_insert_audit_log)

    result = audit_service.write_audit_log(
        object(),
        action="not_allowed",
        entity_type="also_not_allowed",
    )

    assert result.success is False
    assert result.result == "invalid_audit_log"
    assert called is False
    assert len(result.errors) == 2
    assert {error.field for error in result.errors} == {"action", "entity_type"}
    assert {error.code for error in result.errors} == {ERR_INVALID_ENUM}


def test_write_audit_log_returns_repository_operation_result(monkeypatch):
    expected = OperationResult(
        success=True,
        operation="insert_audit_log",
        result="inserted",
        entity_type="database",
        entity_uuid="db-1",
        data={"id": 10},
    )

    def fake_insert_audit_log(connection, log_data):
        return expected

    monkeypatch.setattr(audit_service, "insert_audit_log", fake_insert_audit_log)
    monkeypatch.setattr(audit_service, "utc_now_iso", lambda: "2026-06-15T12:00:00Z")

    result = audit_service.write_audit_log(
        object(),
        action="database_initialized",
        entity_type="database",
        entity_uuid="db-1",
    )

    assert result is expected
    assert result.operation == "insert_audit_log"
    assert result.result == "inserted"


def test_write_audit_log_sets_operation_when_repository_result_has_blank_operation(monkeypatch):
    def fake_insert_audit_log(connection, log_data):
        return OperationResult(
            success=True,
            operation="",
            result="inserted",
        )

    monkeypatch.setattr(audit_service, "insert_audit_log", fake_insert_audit_log)
    monkeypatch.setattr(audit_service, "utc_now_iso", lambda: "2026-06-15T12:00:00Z")

    result = audit_service.write_audit_log(
        object(),
        action="file_scanned",
        entity_type="file",
    )

    assert result.success is True
    assert result.operation == "write_audit_log"
    assert result.result == "inserted"


def test_write_audit_log_handles_repository_exception(monkeypatch):
    def fake_insert_audit_log(connection, log_data):
        raise RuntimeError("database locked")

    monkeypatch.setattr(audit_service, "insert_audit_log", fake_insert_audit_log)
    monkeypatch.setattr(audit_service, "utc_now_iso", lambda: "2026-06-15T12:00:00Z")

    result = audit_service.write_audit_log(
        object(),
        action="backup_created",
        entity_type="backup",
    )

    assert result.success is False
    assert result.operation == "write_audit_log"
    assert result.result == "audit_log_failed"
    assert len(result.errors) == 1
    assert result.errors[0].code == "ERR_AUDIT_LOG_FAILED"
    assert result.errors[0].severity == "error"
    assert "database locked" in result.errors[0].message
    assert result.errors[0].details["exception_type"] == "RuntimeError"


def test_write_audit_log_accepts_non_operation_repository_response(monkeypatch):
    captured: dict[str, object] = {}

    def fake_insert_audit_log(connection, log_data):
        captured["log_data"] = log_data
        return {"id": 123}

    monkeypatch.setattr(audit_service, "insert_audit_log", fake_insert_audit_log)
    monkeypatch.setattr(audit_service, "utc_now_iso", lambda: "2026-06-15T12:00:00Z")

    result = audit_service.write_audit_log(
        object(),
        action="manifest_exported",
        entity_type="manifest_export",
        entity_uuid="export-123",
    )

    assert result.success is True
    assert result.operation == "write_audit_log"
    assert result.result == "audit_log_inserted"
    assert result.entity_type == "manifest_export"
    assert result.entity_uuid == "export-123"
    assert result.data["audit_log"] == captured["log_data"]


@pytest.mark.parametrize(
    ("action", "entity_type"),
    [
        ("database_initialized", "database"),
        ("library_row_inserted", "library_row"),
        ("library_row_updated", "version_uuid"),
        ("library_row_archived", "version_uuid"),
        ("chatgpt_intake_validated", "chatgpt_intake"),
        ("chatgpt_intake_integrated", "chatgpt_intake"),
        ("xlsx_exported", "xlsx_import"),
        ("xlsx_import_previewed", "xlsx_import"),
        ("xlsx_import_applied", "xlsx_import"),
        ("manifest_exported", "manifest_export"),
        ("file_scanned", "file"),
        ("file_copied_to_storage", "file"),
        ("duplicate_detected", "file"),
        ("backup_created", "backup"),
        ("repair_applied", "version_uuid"),
        ("settings_updated", "settings"),
    ],
)
def test_write_audit_log_accepts_all_contract_actions(action, entity_type, monkeypatch):
    def fake_insert_audit_log(connection, log_data):
        return OperationResult(
            success=True,
            operation="write_audit_log",
            result="audit_log_inserted",
        )

    monkeypatch.setattr(audit_service, "insert_audit_log", fake_insert_audit_log)
    monkeypatch.setattr(audit_service, "utc_now_iso", lambda: "2026-06-15T12:00:00Z")

    result = audit_service.write_audit_log(
        object(),
        action=action,
        entity_type=entity_type,
    )

    assert result.success is True