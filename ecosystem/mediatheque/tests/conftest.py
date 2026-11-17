# tests/conftest.py

from __future__ import annotations

import importlib
import json
import shutil
import sqlite3
import subprocess
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TESTS_ROOT = Path(__file__).resolve().parent
FIXTURES_DIR = TESTS_ROOT / "fixtures"

GUI_ROOT = PROJECT_ROOT / "06_GUI" / "koa_mediatheque_gui"
PROJECT_SCHEMA_DIR = PROJECT_ROOT / "schemas" / "sqlite"

APP_PACKAGE_NAME = "koa_mediatheque"

CANONICAL_STORAGE_AREAS = [
    "media_original",
    "media_preview",
    "media_thumbnail",
    "media_derivative",
    "media_caption",
    "media_transcript",
    "media_attachment",
    "content_review_files",
    "external_work_reference_files",
    "cultural_protocol_files",
    "source_files",
    "kristal_source_files",
]

CANONICAL_ROOT_DIRS = [
    "01_DB",
    "02_STORAGE",
    "03_IMPORTS",
    "04_EXPORTS",
    "05_TOOLS",
    "06_GUI",
    "07_BACKUPS",
    "08_LOGS",
    "docs",
]

PROTECTED_XLSX_FIELDS = {
    "media_uuid",
    "version_uuid",
    "filename",
    "original_path",
    "storage_path",
    "sha256",
    "filesize",
    "mimetype",
    "updated_at",
}

SCHEMA_FILENAMES = [
    "001_initial_schema.sql",
    "002_indexes.sql",
    "003_triggers.sql",
    "004_seed_schema_meta.sql",
    "005_kristal_sources.sql",
    "006_kristal_catalog.sql",
    "007_source_authority.sql",
]


def pytest_configure(config: pytest.Config) -> None:
    """Make the application package importable for all contract tests."""
    _prepend_sys_path(GUI_ROOT)
    _prepend_sys_path(PROJECT_ROOT)


def _prepend_sys_path(path: Path) -> None:
    path_text = str(path)
    if path.exists() and path_text not in sys.path:
        sys.path.insert(0, path_text)


def import_app_module(module_name: str):
    """Import a koa_mediatheque module and fail with a useful contract message."""
    full_name = f"{APP_PACKAGE_NAME}.{module_name}"

    try:
        return importlib.import_module(full_name)
    except ModuleNotFoundError:
        pytest.fail(
            f"Missing application module required by tests: {full_name}. "
            f"Expected package root: {GUI_ROOT}",
            pytrace=False,
        )
    except Exception as exc:
        pytest.fail(
            f"Application module {full_name} could not be imported: {exc}",
            pytrace=False,
        )


def import_app_callable(module_name: str, callable_name: str) -> Callable[..., Any]:
    """Import a required public callable from the application package."""
    module = import_app_module(module_name)

    try:
        value = getattr(module, callable_name)
    except AttributeError:
        pytest.fail(
            f"Missing public callable: {APP_PACKAGE_NAME}.{module_name}.{callable_name}",
            pytrace=False,
        )

    if not callable(value):
        pytest.fail(
            f"Public symbol is not callable: {APP_PACKAGE_NAME}.{module_name}.{callable_name}",
            pytrace=False,
        )

    return value


def result_to_dict(result: Any) -> dict[str, Any]:
    """Accept either dataclass-like OperationResult objects or plain dicts."""
    if isinstance(result, dict):
        return result

    data: dict[str, Any] = {}

    for key in (
        "success",
        "operation",
        "result",
        "entity_type",
        "entity_uuid",
        "media_uuid",
        "version_uuid",
        "path",
        "data",
        "warnings",
        "errors",
    ):
        if hasattr(result, key):
            data[key] = getattr(result, key)

    if not data:
        pytest.fail(
            f"Expected OperationResult-like object or dict, got {type(result)!r}",
            pytrace=False,
        )

    data.setdefault("warnings", [])
    data.setdefault("errors", [])
    data.setdefault("data", {})

    return data


def validation_to_dict(result: Any) -> dict[str, Any]:
    """Accept either dataclass-like ValidationResult objects or plain dicts."""
    if isinstance(result, dict):
        return result

    data: dict[str, Any] = {}

    for key in (
        "is_valid",
        "is_blocked",
        "normalized_data",
        "warnings",
        "errors",
    ):
        if hasattr(result, key):
            data[key] = getattr(result, key)

    if not data:
        pytest.fail(
            f"Expected ValidationResult-like object or dict, got {type(result)!r}",
            pytrace=False,
        )

    data.setdefault("normalized_data", {})
    data.setdefault("warnings", [])
    data.setdefault("errors", [])

    return data


def assert_operation_result_shape(result: Any) -> dict[str, Any]:
    """Assert the shared OperationResult contract."""
    data = result_to_dict(result)

    assert "success" in data
    assert "operation" in data
    assert "result" in data
    assert "warnings" in data
    assert "errors" in data
    assert isinstance(data["success"], bool)
    assert isinstance(data["operation"], str)
    assert isinstance(data["result"], str)
    assert isinstance(data["warnings"], list)
    assert isinstance(data["errors"], list)

    return data


def assert_validation_result_shape(result: Any) -> dict[str, Any]:
    """Assert the shared ValidationResult contract."""
    data = validation_to_dict(result)

    assert "is_valid" in data
    assert "is_blocked" in data
    assert "normalized_data" in data
    assert "warnings" in data
    assert "errors" in data
    assert isinstance(data["is_valid"], bool)
    assert isinstance(data["is_blocked"], bool)
    assert isinstance(data["normalized_data"], dict)
    assert isinstance(data["warnings"], list)
    assert isinstance(data["errors"], list)

    return data


def load_json_fixture(filename: str) -> dict[str, Any]:
    path = FIXTURES_DIR / filename

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def copy_project_schema_files(destination: Path) -> Path:
    """
    Copy canonical SQL schema files into a temporary test schema directory.

    The app initializer expects schema files inside the supplied schema_dir.
    The temporary KOA root starts empty, so tests must populate it from the
    real project schema source.
    """
    destination.mkdir(parents=True, exist_ok=True)

    if not PROJECT_SCHEMA_DIR.exists():
        pytest.fail(
            f"Canonical schema directory is missing: {PROJECT_SCHEMA_DIR}",
            pytrace=False,
        )

    missing_files = [
        filename
        for filename in SCHEMA_FILENAMES
        if not (PROJECT_SCHEMA_DIR / filename).exists()
    ]

    if missing_files:
        pytest.fail(
            f"Canonical schema directory is incomplete: {PROJECT_SCHEMA_DIR}; "
            f"missing={missing_files}",
            pytrace=False,
        )

    for old_file in destination.glob("*.sql"):
        old_file.unlink()

    for filename in SCHEMA_FILENAMES:
        shutil.copy2(PROJECT_SCHEMA_DIR / filename, destination / filename)

    return destination


def make_valid_metadata() -> dict[str, Any]:
    return {
        "title": "Document de test kOA",
        "subtitle": "Fixture valide",
        "description": "Métadonnées de test pour l’intégration ChatGPT.",
        "summary": "Fixture valide pour tests de contrat.",
        "media_type": "document",
        "language": "fr",
        "library_scope": "koa",
        "uckk_relevance": "unknown",
        "target_system": "none",
        "target_export_allowed": 0,
        "public_state": "unknown",
        "visibility": "private",
        "access_level": "private",
        "ownership_scope": "unknown",
        "source_type": "unknown",
        "source_ownership": "unknown_source",
        "rights_status": "unknown",
        "rights_note": "Droits inconnus; revue humaine requise.",
        "restriction_state": "none",
        "restriction_reason": "",
        "redaction_required": 0,
        "status": "active",
        "provenance": "ai_assisted",
        "ai_validation_state": "ai_uncertain",
        "ai_confidence": 0.42,
        "canonical_validation_state": "unverified",
        "human_review_required": 1,
        "review_queue": "rights_review",
        "review_reason": "Source ou droits inconnus.",
        "collections": ["tests"],
        "tags": ["fixture", "koa"],
        "relations": [],
        "content_flags": ["copyright_uncertain"],
        "audience_suitability": "unknown",
        "export_to_uckk": "no",
        "export_to_public": "no",
        "export_policy_note": "Ne pas exporter sans revue humaine.",
        "notes": "Fixture contrôlée.",
    }


@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def gui_root() -> Path:
    return GUI_ROOT


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def project_schema_dir() -> Path:
    return PROJECT_SCHEMA_DIR


@pytest.fixture()
def koa_root(tmp_path: Path) -> Path:
    root = tmp_path / "KOA_MEDIATHEQUE"

    for dirname in CANONICAL_ROOT_DIRS:
        (root / dirname).mkdir(parents=True, exist_ok=True)

    for area in CANONICAL_STORAGE_AREAS:
        (root / "02_STORAGE" / area).mkdir(parents=True, exist_ok=True)

    for subdir in (
        "google_drive_raw",
        "google_drive_scanned",
        "ai_generated_docs",
        "pending_review",
    ):
        (root / "03_IMPORTS" / subdir).mkdir(parents=True, exist_ok=True)

    for subdir in (
        "xlsx",
        "manifests",
        "uckkarchive",
        "public_review",
    ):
        (root / "04_EXPORTS" / subdir).mkdir(parents=True, exist_ok=True)

    copy_project_schema_files(root / "01_DB" / "schema_versions")

    return root


@pytest.fixture()
def db_path(koa_root: Path) -> Path:
    return koa_root / "01_DB" / "koa_mediatheque.sqlite"


@pytest.fixture()
def schema_dir(koa_root: Path) -> Path:
    return koa_root / "01_DB" / "schema_versions"


@pytest.fixture()
def storage_root(koa_root: Path) -> Path:
    return koa_root / "02_STORAGE"


@pytest.fixture()
def imports_root(koa_root: Path) -> Path:
    return koa_root / "03_IMPORTS"


@pytest.fixture()
def exports_root(koa_root: Path) -> Path:
    return koa_root / "04_EXPORTS"


@pytest.fixture()
def backup_root(koa_root: Path) -> Path:
    return koa_root / "07_BACKUPS"


@pytest.fixture()
def sample_file_path(koa_root: Path) -> Path:
    path = koa_root / "03_IMPORTS" / "pending_review" / "sample_file.txt"
    fixture_path = FIXTURES_DIR / "sample_file.txt"

    if fixture_path.exists():
        shutil.copy2(fixture_path, path)
    else:
        path.write_text(
            "Médiathèque kOA sample file for hashing, storage and intake tests.\n",
            encoding="utf-8",
        )

    return path


@pytest.fixture()
def sample_metadata_valid() -> dict[str, Any]:
    path = FIXTURES_DIR / "sample_metadata_valid.json"

    if path.exists():
        return load_json_fixture("sample_metadata_valid.json")

    return make_valid_metadata()


@pytest.fixture()
def sample_metadata_invalid_enum(sample_metadata_valid: dict[str, Any]) -> dict[str, Any]:
    data = dict(sample_metadata_valid)
    data["visibility"] = "institutional"
    return data


@pytest.fixture()
def sample_metadata_verified_blocked(
    sample_metadata_valid: dict[str, Any],
) -> dict[str, Any]:
    data = dict(sample_metadata_valid)
    data["canonical_validation_state"] = "verified"
    data["human_review_required"] = 0
    data["review_reason"] = ""
    return data


@pytest.fixture()
def sample_metadata_valid_json(sample_metadata_valid: dict[str, Any]) -> str:
    return json.dumps(sample_metadata_valid, ensure_ascii=False)


@pytest.fixture()
def sample_metadata_invalid_enum_json(
    sample_metadata_invalid_enum: dict[str, Any],
) -> str:
    return json.dumps(sample_metadata_invalid_enum, ensure_ascii=False)


@pytest.fixture()
def sample_metadata_verified_blocked_json(
    sample_metadata_verified_blocked: dict[str, Any],
) -> str:
    return json.dumps(sample_metadata_verified_blocked, ensure_ascii=False)


@pytest.fixture()
def sqlite_connection(db_path: Path) -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture()
def initialized_db(db_path: Path, schema_dir: Path) -> Path:
    initialize_database = import_app_callable("db", "initialize_database")
    result = initialize_database(db_path, schema_dir, overwrite=True)
    data = assert_operation_result_shape(result)

    assert data["success"] is True
    assert db_path.exists()

    return db_path


@pytest.fixture()
def initialized_connection(initialized_db: Path) -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(initialized_db)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture()
def sample_library_row_data(
    sample_file_path: Path,
    sample_metadata_valid: dict[str, Any],
) -> dict[str, Any]:
    return {
        "media_uuid": "11111111-1111-4111-8111-111111111111",
        "version_uuid": "22222222-2222-4222-8222-222222222222",
        "title": sample_metadata_valid["title"],
        "subtitle": sample_metadata_valid["subtitle"],
        "description": sample_metadata_valid["description"],
        "summary": sample_metadata_valid["summary"],
        "original_path": str(sample_file_path),
        "storage_path": "",
        "filename": sample_file_path.name,
        "extension": ".txt",
        "mimetype": "text/plain",
        "filesize": sample_file_path.stat().st_size,
        "sha256": "0" * 64,
        "filearea": "media_original",
        "media_type": "document",
        "language": "fr",
        "library_scope": "koa",
        "uckk_relevance": "unknown",
        "target_system": "none",
        "target_export_allowed": 0,
        "public_state": "unknown",
        "visibility": "private",
        "access_level": "private",
        "ownership_scope": "unknown",
        "source_type": "unknown",
        "source_ownership": "unknown_source",
        "rights_status": "unknown",
        "rights_note": "Droits inconnus; revue humaine requise.",
        "restriction_state": "none",
        "restriction_reason": "",
        "redaction_required": 0,
        "status": "active",
        "provenance": "ai_assisted",
        "ai_validation_state": "ai_uncertain",
        "ai_confidence": 0.42,
        "canonical_validation_state": "unverified",
        "human_review_required": 1,
        "review_queue": "rights_review",
        "review_reason": "Source ou droits inconnus.",
        "collections_json": '["tests"]',
        "tags_json": '["fixture", "koa"]',
        "relations_json": "[]",
        "content_flags_json": '["copyright_uncertain"]',
        "audience_suitability": "unknown",
        "export_to_uckk": "no",
        "export_to_public": "no",
        "export_policy_note": "Ne pas exporter sans revue humaine.",
        "import_batch": "test_batch",
        "notes": "Fixture contrôlée.",
    }


@pytest.fixture()
def inserted_library_row(
    initialized_connection: sqlite3.Connection,
    sample_library_row_data: dict[str, Any],
) -> dict[str, Any]:
    insert_library_row = import_app_callable(
        "repositories.library_rows_repository",
        "insert_library_row",
    )

    result = insert_library_row(initialized_connection, sample_library_row_data)
    data = assert_operation_result_shape(result)

    assert data["success"] is True

    initialized_connection.commit()

    return sample_library_row_data


@pytest.fixture()
def sample_import_xlsx_path(
    tmp_path: Path,
    sample_library_row_data: dict[str, Any],
) -> Path:
    openpyxl = pytest.importorskip("openpyxl")

    path = tmp_path / "sample_import.xlsx"
    workbook = openpyxl.Workbook()

    library = workbook.active
    library.title = "Library"

    headers = [
        "action",
        "version_uuid",
        "media_uuid",
        "title",
        "description",
        "visibility",
        "public_state",
        "rights_status",
        "human_review_required",
        "notes",
    ]
    library.append(headers)

    library.append(
        [
            "update",
            sample_library_row_data["version_uuid"],
            sample_library_row_data["media_uuid"],
            "Titre modifié depuis XLSX",
            "Description modifiée depuis XLSX",
            "private",
            "unknown",
            "unknown",
            1,
            "Import XLSX de test.",
        ]
    )

    lists = workbook.create_sheet("Lists")
    lists.append(["list_name", "value"])
    lists.append(["action", "update"])
    lists.append(["action", "ignore"])
    lists.append(["action", "archive"])
    lists.append(["action", "new"])
    lists.append(["visibility", "private"])
    lists.append(["visibility", "public"])
    lists.append(["public_state", "unknown"])
    lists.append(["rights_status", "unknown"])

    report = workbook.create_sheet("Import_Report")
    report.append(["key", "value"])
    report.append(["fixture", "sample_import"])

    workbook.save(path)

    return path


@pytest.fixture()
def ps7_available() -> bool:
    return bool(shutil.which("pwsh"))


@pytest.fixture()
def ps7_tools_root(project_root: Path) -> Path:
    return project_root / "05_TOOLS"


@pytest.fixture()
def run_ps7(ps7_available: bool) -> Callable[..., subprocess.CompletedProcess[str]]:
    if not ps7_available:
        pytest.skip("PowerShell 7 executable 'pwsh' is not available.")

    def _run_ps7(script_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
        command = [
            "pwsh",
            "-NoLogo",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            *args,
        ]

        return subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
        )

    return _run_ps7


@pytest.fixture()
def parse_ps7_json_stdout() -> Callable[[str], dict[str, Any]]:
    def _parse(stdout: str) -> dict[str, Any]:
        try:
            data = json.loads(stdout.strip())
        except json.JSONDecodeError as exc:
            pytest.fail(
                f"PS7 stdout is not valid JSON: {exc}\nstdout={stdout!r}",
                pytrace=False,
            )

        assert_operation_result_shape(data)

        return data

    return _parse