# 05_TOOLS/Add-KoaLibraryRow.ps1
# Médiathèque kOA — Add one controlled library_rows record from file + metadata JSON
# PowerShell 7 only. Emits exactly one JSON result to stdout.
# Uses Python sqlite3 for the database write path.

#requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $DbPath,

    [Parameter(Mandatory)]
    [string] $FilePath,

    [Parameter(Mandatory)]
    [string] $MetadataJson,

    [string] $StorageRoot = "",

    [string] $ImportBatch = "",

    [ValidateSet("InsertNew", "UpdateExisting", "Upsert", "DryRun")]
    [string] $Mode = "InsertNew",

    [switch] $CopyFile,

    [switch] $AllowHumanVerifiedOverride
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$Operation = "Add-KoaLibraryRow"

function New-KoaLocalMessage {
    param(
        [Parameter(Mandatory)]
        [string] $Code,

        [Parameter(Mandatory)]
        [ValidateSet("info", "warning", "error", "blocking")]
        [string] $Severity,

        [Parameter(Mandatory)]
        [string] $Message,

        [string] $Field = $null,

        [Nullable[int]] $RowNumber = $null,

        [hashtable] $Details = @{}
    )

    return [ordered]@{
        code       = $Code
        severity   = $Severity
        message    = $Message
        field      = $Field
        row_number = $RowNumber
        details    = $Details
    }
}

function New-KoaLocalResult {
    param(
        [Parameter(Mandatory)]
        [bool] $Success,

        [Parameter(Mandatory)]
        [string] $Result,

        [string] $EntityType = "library_row",

        [string] $EntityUuid = "",

        [string] $VersionUuid = "",

        [string] $MediaUuid = "",

        [string] $Path = "",

        [hashtable] $Data = @{},

        [object[]] $Warnings = @(),

        [object[]] $Errors = @()
    )

    return [ordered]@{
        success      = $Success
        operation    = $Operation
        result       = $Result
        entity_type  = $EntityType
        entity_uuid  = $EntityUuid
        version_uuid = $VersionUuid
        media_uuid   = $MediaUuid
        path         = $Path
        data         = $Data
        warnings     = @($Warnings)
        errors       = @($Errors)
    }
}

function Write-KoaLocalJsonResult {
    param(
        [Parameter(Mandatory)]
        [object] $Result
    )

    [Console]::Out.WriteLine(($Result | ConvertTo-Json -Depth 100 -Compress:$false))
}

function Get-KoaPythonCommand {
    $candidatePaths = @()

    if (-not [string]::IsNullOrWhiteSpace($env:KOA_TEST_PYTHON)) {
        $candidatePaths += $env:KOA_TEST_PYTHON
    }

    if (-not [string]::IsNullOrWhiteSpace($env:PYTHON)) {
        $candidatePaths += $env:PYTHON
    }

    $repoRoot = Split-Path -Parent $PSScriptRoot

    $candidatePaths += @(
        (Join-Path $repoRoot ".venv/Scripts/python.exe"),
        (Join-Path $repoRoot ".venv/bin/python")
    )

    foreach ($candidatePath in $candidatePaths) {
        if ([string]::IsNullOrWhiteSpace($candidatePath)) {
            continue
        }

        if (Test-Path -LiteralPath $candidatePath -PathType Leaf) {
            return [pscustomobject]@{
                Exe  = $candidatePath
                Args = @()
            }
        }

        $resolved = Get-Command $candidatePath -ErrorAction SilentlyContinue
        if ($resolved) {
            return [pscustomobject]@{
                Exe  = [string] $resolved.Source
                Args = @()
            }
        }
    }

    foreach ($candidate in @("python", "python3")) {
        $resolved = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($resolved) {
            return [pscustomobject]@{
                Exe  = [string] $resolved.Source
                Args = @()
            }
        }
    }

    $py = Get-Command "py" -ErrorAction SilentlyContinue
    if ($py) {
        return [pscustomobject]@{
            Exe  = [string] $py.Source
            Args = @("-3")
        }
    }

    throw "Python was not found. Add-KoaLibraryRow.ps1 requires Python with sqlite3."
}

function Invoke-KoaPythonAddLibraryRow {
    $pythonCommand = Get-KoaPythonCommand
    $pythonExe = [string] $pythonCommand.Exe
    $pythonArgs = @($pythonCommand.Args)

    if ([string]::IsNullOrWhiteSpace($pythonExe)) {
        throw "Python executable path resolved to an empty string."
    }

    if (
        -not (Test-Path -LiteralPath $pythonExe -PathType Leaf) -and
        -not (Get-Command $pythonExe -ErrorAction SilentlyContinue)
    ) {
        throw "Python executable was not found: $pythonExe"
    }

    $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("koa_add_row_" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

    $scriptPath = Join-Path $tempDir "add_library_row.py"
    $metadataPath = Join-Path $tempDir "metadata.json"
    $stderrPath = Join-Path $tempDir "stderr.txt"

    Set-Content -LiteralPath $metadataPath -Value $MetadataJson -Encoding UTF8

    $pythonCode = @'
from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import shutil
import sqlite3
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


OPERATION = "Add-KoaLibraryRow"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def message(code, severity, msg, field=None, row_number=None, details=None):
    return {
        "code": code,
        "severity": severity,
        "message": msg,
        "field": field,
        "row_number": row_number,
        "details": details or {},
    }


def result(
    *,
    success,
    result_text,
    path="",
    entity_uuid="",
    version_uuid="",
    media_uuid="",
    data=None,
    warnings=None,
    errors=None,
):
    return {
        "success": bool(success),
        "operation": OPERATION,
        "result": result_text,
        "entity_type": "library_row",
        "entity_uuid": entity_uuid or "",
        "version_uuid": version_uuid or "",
        "media_uuid": media_uuid or "",
        "path": path or "",
        "data": data or {},
        "warnings": warnings or [],
        "errors": errors or [],
    }


def emit(payload, exit_code):
    print(json.dumps(payload, ensure_ascii=False, sort_keys=False))
    raise SystemExit(exit_code)


def to_int01(value, default=0):
    if value is None:
        return default
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)):
        return 1 if int(value) else 0
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "oui"}:
        return 1
    if text in {"0", "false", "no", "n", "non"}:
        return 0
    return default


def safe_json_array(value):
    if value is None:
        return "[]"
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, tuple):
        return json.dumps(list(value), ensure_ascii=False)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return "[]"
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return json.dumps(parsed, ensure_ascii=False)
        except Exception:
            pass
        return json.dumps([text], ensure_ascii=False)
    return json.dumps([value], ensure_ascii=False)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_facts(file_path_text: str) -> dict:
    path = Path(file_path_text)
    stat = path.stat()
    guessed_mime, _ = mimetypes.guess_type(str(path))
    return {
        "original_path": file_path_text,
        "filename": path.name,
        "extension": path.suffix,
        "filesize": int(stat.st_size),
        "sha256": sha256_file(path),
        "mimetype": guessed_mime or "application/octet-stream",
    }


def safe_filename_part(value: str, fallback="file") -> str:
    text = str(value or "").strip()
    if not text:
        text = fallback
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", text)
    text = text.strip("._-")
    return text or fallback


def db_table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table_name,),
    ).fetchone()
    return row is not None


def db_columns(connection: sqlite3.Connection, table_name: str) -> list[str]:
    cursor = connection.execute(f"PRAGMA table_info({table_name})")
    try:
        return [str(row[1]) for row in cursor.fetchall()]
    finally:
        cursor.close()


def fetch_one_by_version(connection: sqlite3.Connection, version_uuid: str):
    if not version_uuid:
        return None
    connection.row_factory = sqlite3.Row
    cursor = connection.execute(
        "SELECT * FROM library_rows WHERE version_uuid = ? LIMIT 1",
        (version_uuid,),
    )
    try:
        row = cursor.fetchone()
        return dict(row) if row is not None else None
    finally:
        cursor.close()


def fetch_by_sha256(connection: sqlite3.Connection, sha256: str):
    if not sha256:
        return []
    connection.row_factory = sqlite3.Row
    cursor = connection.execute(
        """
        SELECT id, media_uuid, version_uuid, title, filename, original_path, storage_path, status
        FROM library_rows
        WHERE sha256 = ?
        ORDER BY id
        """,
        (sha256,),
    )
    try:
        return [dict(row) for row in cursor.fetchall()]
    finally:
        cursor.close()


CONTROLLED_VALUES = {
    "media_type": {"document", "image", "audio", "video", "archive", "other"},
    "language": {"fr", "en", "und", "unknown"},
    "library_scope": {"koa", "uckk", "mixed", "unknown"},
    "uckk_relevance": {"unknown", "not_uckk", "uckk_reference", "uckk_candidate", "uckk_core"},
    "target_system": {"none", "uckkarchive", "moodle", "website"},
    "public_state": {"unknown", "public", "private", "non_public"},
    "visibility": {"public", "private", "restricted", "unknown"},
    "access_level": {"public", "private", "restricted", "internal", "unknown"},
    "ownership_scope": {"unknown", "koa_owned", "uckk_owned", "third_party", "mixed"},
    "source_type": {"unknown", "produced_by_uckk", "external", "user_submitted", "generated"},
    "source_ownership": {"unknown_source", "uckk_created", "koa_created", "third_party", "mixed"},
    "rights_status": {"unknown", "owned", "third_party", "fair_use_reference", "public_domain", "licensed"},
    "restriction_state": {"none", "possible", "restricted"},
    "status": {"active", "archived", "pending_review", "deleted"},
    "provenance": {"ai_assisted", "human_created", "imported", "mixed"},
    "ai_validation_state": {"ai_uncertain", "ai_validated", "ai_rejected"},
    "canonical_validation_state": {"unverified", "human_reviewed", "verified"},
    "audience_suitability": {"unknown", "general", "restricted"},
    "export_to_uckk": {"yes", "no"},
    "export_to_public": {"yes", "no"},
}


DEFAULTS = {
    "title": "Untitled",
    "subtitle": "",
    "description": "",
    "summary": "",
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
    "rights_note": "",
    "restriction_state": "none",
    "restriction_reason": "",
    "redaction_required": 0,
    "status": "active",
    "provenance": "ai_assisted",
    "ai_validation_state": "ai_uncertain",
    "ai_confidence": None,
    "canonical_validation_state": "unverified",
    "human_review_required": 1,
    "review_queue": "",
    "review_reason": "",
    "audience_suitability": "unknown",
    "export_to_uckk": "no",
    "export_to_public": "no",
    "export_policy_note": "",
    "notes": "",
}


def validate_metadata(metadata: dict, allow_human_verified_override: bool):
    warnings = []
    errors = []

    if not isinstance(metadata, dict):
        errors.append(message("ERR_METADATA_JSON_OBJECT_REQUIRED", "blocking", "MetadataJson must be a JSON object.", "MetadataJson"))
        return warnings, errors

    title = str(metadata.get("title") or "").strip()
    if not title:
        errors.append(message("ERR_REQUIRED_FIELD", "blocking", "Metadata field title is required.", "title"))

    for key, allowed in CONTROLLED_VALUES.items():
        if key not in metadata or metadata.get(key) is None or str(metadata.get(key)).strip() == "":
            continue
        value = str(metadata.get(key)).strip()
        if value not in allowed:
            errors.append(
                message(
                    "ERR_INVALID_CONTROLLED_VALUE",
                    "blocking",
                    f"Invalid value for {key}: {value}",
                    key,
                    details={"allowed": sorted(allowed), "value": value},
                )
            )

    canonical = str(metadata.get("canonical_validation_state") or "").strip()
    if canonical == "verified" and not allow_human_verified_override:
        errors.append(
            message(
                "ERR_HUMAN_VERIFIED_BLOCKED",
                "blocking",
                "canonical_validation_state=verified requires explicit human override.",
                "canonical_validation_state",
            )
        )

    return warnings, errors


def build_row_data(
    metadata: dict,
    facts: dict,
    storage_path: str,
    import_batch: str,
    media_uuid: str | None = None,
    version_uuid: str | None = None,
):
    media_uuid = str(media_uuid or metadata.get("media_uuid") or "").strip() or str(uuid4())
    version_uuid = str(version_uuid or metadata.get("version_uuid") or "").strip() or str(uuid4())

    row = {
        "media_uuid": media_uuid,
        "version_uuid": version_uuid,
        "title": str(metadata.get("title") or DEFAULTS["title"]),
        "subtitle": str(metadata.get("subtitle") or DEFAULTS["subtitle"]),
        "description": str(metadata.get("description") or DEFAULTS["description"]),
        "summary": str(metadata.get("summary") or DEFAULTS["summary"]),
        "original_path": facts["original_path"],
        "storage_path": storage_path or "",
        "filename": facts["filename"],
        "extension": facts["extension"],
        "mimetype": facts["mimetype"],
        "filesize": facts["filesize"],
        "sha256": facts["sha256"],
        "filearea": str(metadata.get("filearea") or DEFAULTS["filearea"]),
        "media_type": str(metadata.get("media_type") or DEFAULTS["media_type"]),
        "language": str(metadata.get("language") or DEFAULTS["language"]),
        "library_scope": str(metadata.get("library_scope") or DEFAULTS["library_scope"]),
        "uckk_relevance": str(metadata.get("uckk_relevance") or DEFAULTS["uckk_relevance"]),
        "target_system": str(metadata.get("target_system") or DEFAULTS["target_system"]),
        "target_export_allowed": to_int01(metadata.get("target_export_allowed"), DEFAULTS["target_export_allowed"]),
        "public_state": str(metadata.get("public_state") or DEFAULTS["public_state"]),
        "visibility": str(metadata.get("visibility") or DEFAULTS["visibility"]),
        "access_level": str(metadata.get("access_level") or DEFAULTS["access_level"]),
        "ownership_scope": str(metadata.get("ownership_scope") or DEFAULTS["ownership_scope"]),
        "source_type": str(metadata.get("source_type") or DEFAULTS["source_type"]),
        "source_ownership": str(metadata.get("source_ownership") or DEFAULTS["source_ownership"]),
        "rights_status": str(metadata.get("rights_status") or DEFAULTS["rights_status"]),
        "rights_note": str(metadata.get("rights_note") or DEFAULTS["rights_note"]),
        "restriction_state": str(metadata.get("restriction_state") or DEFAULTS["restriction_state"]),
        "restriction_reason": str(metadata.get("restriction_reason") or DEFAULTS["restriction_reason"]),
        "redaction_required": to_int01(metadata.get("redaction_required"), DEFAULTS["redaction_required"]),
        "status": str(metadata.get("status") or DEFAULTS["status"]),
        "provenance": str(metadata.get("provenance") or DEFAULTS["provenance"]),
        "ai_validation_state": str(metadata.get("ai_validation_state") or DEFAULTS["ai_validation_state"]),
        "ai_confidence": metadata.get("ai_confidence", DEFAULTS["ai_confidence"]),
        "canonical_validation_state": str(metadata.get("canonical_validation_state") or DEFAULTS["canonical_validation_state"]),
        "human_review_required": to_int01(metadata.get("human_review_required"), DEFAULTS["human_review_required"]),
        "review_queue": str(metadata.get("review_queue") or DEFAULTS["review_queue"]),
        "review_reason": str(metadata.get("review_reason") or DEFAULTS["review_reason"]),
        "collections_json": safe_json_array(metadata.get("collections")),
        "tags_json": safe_json_array(metadata.get("tags")),
        "relations_json": safe_json_array(metadata.get("relations")),
        "content_flags_json": safe_json_array(metadata.get("content_flags")),
        "audience_suitability": str(metadata.get("audience_suitability") or DEFAULTS["audience_suitability"]),
        "export_to_uckk": str(metadata.get("export_to_uckk") or DEFAULTS["export_to_uckk"]),
        "export_to_public": str(metadata.get("export_to_public") or DEFAULTS["export_to_public"]),
        "export_policy_note": str(metadata.get("export_policy_note") or DEFAULTS["export_policy_note"]),
        "import_batch": import_batch,
        "notes": str(metadata.get("notes") or DEFAULTS["notes"]),
    }

    return row


def insert_row(connection: sqlite3.Connection, row_data: dict):
    columns = db_columns(connection, "library_rows")
    insert_data = {key: value for key, value in row_data.items() if key in columns}
    names = list(insert_data.keys())
    sql = f"INSERT INTO library_rows ({', '.join(names)}) VALUES ({', '.join('?' for _ in names)})"
    connection.execute(sql, [insert_data[name] for name in names])


def update_row(connection: sqlite3.Connection, row_data: dict, version_uuid: str):
    columns = db_columns(connection, "library_rows")
    update_data = {
        key: value
        for key, value in row_data.items()
        if key in columns and key not in {"media_uuid", "version_uuid", "created_at"}
    }

    if "updated_at" in columns:
        update_data["updated_at"] = now_iso()

    names = list(update_data.keys())
    sql = f"UPDATE library_rows SET {', '.join(name + ' = ?' for name in names)} WHERE version_uuid = ?"
    connection.execute(sql, [update_data[name] for name in names] + [version_uuid])


def insert_intake_log(connection: sqlite3.Connection, version_uuid: str, file_path: str, raw_response: str, parsed, status: str, validation_errors):
    if not db_table_exists(connection, "chatgpt_intake_log"):
        return

    connection.execute(
        """
        INSERT INTO chatgpt_intake_log(
            version_uuid,
            file_path,
            prompt_template,
            raw_response,
            parsed_json,
            validation_status,
            validation_errors,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            version_uuid or "",
            file_path or "",
            "",
            raw_response or "",
            json.dumps(parsed or {}, ensure_ascii=False, sort_keys=True),
            status,
            json.dumps(validation_errors or [], ensure_ascii=False, sort_keys=True),
            now_iso(),
        ),
    )


def insert_audit_log(connection: sqlite3.Connection, action: str, entity_uuid: str, before, after, note: str):
    if not db_table_exists(connection, "audit_log"):
        return

    connection.execute(
        """
        INSERT INTO audit_log(
            actor,
            action,
            entity_type,
            entity_uuid,
            before_json,
            after_json,
            note,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "local_user",
            action,
            "library_row",
            entity_uuid or "",
            json.dumps(before, ensure_ascii=False, sort_keys=True) if before is not None else None,
            json.dumps(after, ensure_ascii=False, sort_keys=True) if after is not None else None,
            note,
            now_iso(),
        ),
    )


def copy_to_storage(source_file: str, storage_root: str, filearea: str, version_uuid: str, dry_run: bool):
    if not storage_root:
        raise RuntimeError("StorageRoot is required when CopyFile is used.")

    source = Path(source_file)
    target_dir = Path(storage_root) / (filearea or "media_original")
    safe_stem = safe_filename_part(source.stem)
    target = target_dir / f"{version_uuid}_{safe_stem}{source.suffix}"

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source), str(target))

    return {
        "storage_area_path": str(target_dir),
        "storage_path": str(target),
        "stored_filename": target.name,
        "filearea": filearea or "media_original",
        "copied": not dry_run,
    }


def main():
    db_path_text = sys.argv[1]
    file_path_text = sys.argv[2]
    metadata_path_text = sys.argv[3]
    storage_root = sys.argv[4]
    import_batch = sys.argv[5]
    mode = sys.argv[6]
    copy_file = sys.argv[7] == "1"
    allow_human_verified_override = sys.argv[8] == "1"

    db_path = Path(db_path_text)
    file_path = Path(file_path_text)

    if not db_path.exists() or not db_path.is_file():
        emit(
            result(
                success=False,
                result_text="db_not_found",
                path=file_path_text,
                errors=[
                    message(
                        "ERR_DB_NOT_FOUND",
                        "blocking",
                        f"SQLite database not found: {db_path_text}",
                        "DbPath",
                    )
                ],
            ),
            1,
        )

    if not file_path.exists() or not file_path.is_file():
        emit(
            result(
                success=False,
                result_text="file_not_found",
                path=file_path_text,
                errors=[
                    message(
                        "ERR_FILE_NOT_FOUND",
                        "blocking",
                        f"File not found: {file_path_text}",
                        "FilePath",
                    )
                ],
            ),
            1,
        )

    try:
        metadata = json.loads(Path(metadata_path_text).read_text(encoding="utf-8-sig"))
    except Exception as exc:
        emit(
            result(
                success=False,
                result_text="metadata_invalid_json",
                path=file_path_text,
                errors=[
                    message(
                        "ERR_JSON_PARSE",
                        "blocking",
                        f"MetadataJson is invalid JSON: {exc}",
                        "MetadataJson",
                    )
                ],
            ),
            1,
        )

    warnings, errors = validate_metadata(metadata, allow_human_verified_override)
    facts = file_facts(file_path_text)

    if not import_batch:
        import_batch = "manual_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row

    try:
        if not db_table_exists(connection, "library_rows"):
            emit(
                result(
                    success=False,
                    result_text="db_schema_invalid",
                    path=file_path_text,
                    errors=[
                        message(
                            "ERR_DB_SCHEMA",
                            "blocking",
                            "SQLite table not found: library_rows",
                            "DbPath",
                        )
                    ],
                ),
                1,
            )

        preliminary = build_row_data(metadata, facts, "", import_batch)
        version_uuid = preliminary["version_uuid"]
        media_uuid = preliminary["media_uuid"]

        if errors:
            try:
                insert_intake_log(
                    connection,
                    version_uuid,
                    file_path_text,
                    Path(metadata_path_text).read_text(encoding="utf-8-sig"),
                    metadata,
                    "blocked",
                    errors,
                )
                connection.commit()
            except Exception:
                connection.rollback()

            emit(
                result(
                    success=False,
                    result_text="metadata_blocked",
                    path=file_path_text,
                    version_uuid=version_uuid,
                    media_uuid=media_uuid,
                    data={"validation": {"is_valid": False, "is_blocked": True}},
                    warnings=warnings,
                    errors=errors,
                ),
                1,
            )

        existing = fetch_one_by_version(connection, version_uuid)
        duplicates = fetch_by_sha256(connection, facts["sha256"])

        if existing is not None and mode == "InsertNew":
            emit(
                result(
                    success=False,
                    result_text="duplicate_version_uuid",
                    path=file_path_text,
                    entity_uuid=version_uuid,
                    version_uuid=version_uuid,
                    media_uuid=media_uuid,
                    data={"existing_row": existing},
                    warnings=warnings,
                    errors=[
                        message(
                            "ERR_VERSION_UUID_DUPLICATE",
                            "blocking",
                            "version_uuid already exists; InsertNew refuses to overwrite existing rows.",
                            "version_uuid",
                            details={"version_uuid": version_uuid},
                        )
                    ],
                ),
                1,
            )

        if existing is None and mode == "UpdateExisting":
            emit(
                result(
                    success=False,
                    result_text="version_uuid_not_found",
                    path=file_path_text,
                    entity_uuid=version_uuid,
                    version_uuid=version_uuid,
                    media_uuid=media_uuid,
                    warnings=warnings,
                    errors=[
                        message(
                            "ERR_VERSION_UUID_MISSING",
                            "blocking",
                            "UpdateExisting requires an existing version_uuid.",
                            "version_uuid",
                            details={"version_uuid": version_uuid},
                        )
                    ],
                ),
                1,
            )

        if duplicates:
            warnings.append(
                message(
                    "WARN_DUPLICATE_SHA256",
                    "warning",
                    "One or more existing rows have the same sha256.",
                    "sha256",
                    details={
                        "sha256": facts["sha256"],
                        "duplicate_count": len(duplicates),
                        "duplicates": duplicates,
                    },
                )
            )

        storage_copy = None
        storage_path = ""

        if copy_file:
            storage_copy = copy_to_storage(
                file_path_text,
                storage_root,
                preliminary.get("filearea") or "media_original",
                version_uuid,
                mode == "DryRun",
            )
            storage_path = storage_copy["storage_path"]
        else:
            warnings.append(
                message(
                    "WARN_STORAGE_COPY_SKIPPED",
                    "warning",
                    "File was referenced in place; it was not copied into 02_STORAGE.",
                    "storage_path",
                )
            )

        row_data = build_row_data(
            metadata,
            facts,
            storage_path,
            import_batch,
            media_uuid=media_uuid,
            version_uuid=version_uuid,
        )

        if mode == "DryRun":
            emit(
                result(
                    success=True,
                    result_text="dry_run",
                    path=file_path_text,
                    entity_uuid=version_uuid,
                    version_uuid=version_uuid,
                    media_uuid=media_uuid,
                    data={
                        "mode": mode,
                        "db_path": db_path_text,
                        "file_facts": facts,
                        "row_preview": row_data,
                        "storage_copy": storage_copy,
                        "duplicate_rows": duplicates,
                        "import_batch": import_batch,
                    },
                    warnings=warnings,
                    errors=[],
                ),
                0,
            )

        if existing is not None and mode in {"UpdateExisting", "Upsert"}:
            update_row(connection, row_data, version_uuid)
            insert_audit_log(connection, "library_row_updated", version_uuid, existing, row_data, f"Add-KoaLibraryRow.ps1 Mode={mode}")
            insert_intake_log(
                connection,
                version_uuid,
                file_path_text,
                Path(metadata_path_text).read_text(encoding="utf-8-sig"),
                row_data,
                "integrated_updated",
                [],
            )
            connection.commit()

            updated = fetch_one_by_version(connection, version_uuid)

            emit(
                result(
                    success=True,
                    result_text="updated",
                    path=file_path_text,
                    entity_uuid=version_uuid,
                    version_uuid=version_uuid,
                    media_uuid=media_uuid,
                    data={
                        "mode": mode,
                        "db_path": db_path_text,
                        "file_facts": facts,
                        "row": updated,
                        "storage_copy": storage_copy,
                        "duplicate_rows": duplicates,
                        "import_batch": import_batch,
                    },
                    warnings=warnings,
                    errors=[],
                ),
                0,
            )

        insert_row(connection, row_data)
        insert_audit_log(connection, "library_row_inserted", version_uuid, None, row_data, f"Add-KoaLibraryRow.ps1 Mode={mode}")

        if copy_file:
            insert_audit_log(connection, "file_copied_to_storage", version_uuid, None, storage_copy, "Add-KoaLibraryRow.ps1")

        insert_intake_log(
            connection,
            version_uuid,
            file_path_text,
            Path(metadata_path_text).read_text(encoding="utf-8-sig"),
            row_data,
            "integrated_inserted",
            [],
        )

        connection.commit()

        inserted = fetch_one_by_version(connection, version_uuid)

        emit(
            result(
                success=True,
                result_text="inserted",
                path=file_path_text,
                entity_uuid=version_uuid,
                version_uuid=version_uuid,
                media_uuid=media_uuid,
                data={
                    "mode": mode,
                    "db_path": db_path_text,
                    "file_facts": facts,
                    "row": inserted,
                    "storage_copy": storage_copy,
                    "duplicate_rows": duplicates,
                    "import_batch": import_batch,
                },
                warnings=warnings,
                errors=[],
            ),
            0,
        )
    except SystemExit:
        raise
    except Exception as exc:
        connection.rollback()
        emit(
            result(
                success=False,
                result_text="failed",
                path=file_path_text,
                errors=[
                    message(
                        "ERR_ADD_LIBRARY_ROW_FAILED",
                        "blocking",
                        str(exc),
                        "Add-KoaLibraryRow",
                        details={"traceback": traceback.format_exc()},
                    )
                ],
            ),
            1,
        )
    finally:
        connection.close()


if __name__ == "__main__":
    main()
'@

    Set-Content -LiteralPath $scriptPath -Value $pythonCode -Encoding UTF8

    try {
        $allArgs = @()
        $allArgs += $pythonArgs
        $allArgs += $scriptPath
        $allArgs += $DbPath
        $allArgs += $FilePath
        $allArgs += $metadataPath
        $allArgs += $StorageRoot
        $allArgs += $ImportBatch
        $allArgs += $Mode
        $allArgs += ($(if ($CopyFile.IsPresent) { "1" } else { "0" }))
        $allArgs += ($(if ($AllowHumanVerifiedOverride.IsPresent) { "1" } else { "0" }))

        $stdout = & $pythonExe @allArgs 2>$stderrPath
        $exitCode = $LASTEXITCODE
        $raw = ($stdout | Out-String)

        if ($null -eq $raw) {
            $raw = ""
        }

        $raw = $raw.Trim()

        if ([string]::IsNullOrWhiteSpace($raw)) {
            $stderr = ""

            if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
                $stderrContent = Get-Content -LiteralPath $stderrPath -Raw -ErrorAction SilentlyContinue
                if ($null -ne $stderrContent) {
                    $stderr = ([string] $stderrContent).Trim()
                }
            }

            $fallback = New-KoaLocalResult `
                -Success $false `
                -Result "failed" `
                -Path $FilePath `
                -Errors @(
                    New-KoaLocalMessage `
                        -Code "ERR_ADD_LIBRARY_ROW_FAILED" `
                        -Severity "blocking" `
                        -Message "Python helper produced no JSON output. ExitCode=$exitCode Stderr=$stderr" `
                        -Field "python"
                )

            Write-KoaLocalJsonResult -Result $fallback
            exit 1
        }

        [Console]::Out.WriteLine($raw)
        exit $exitCode
    }
    finally {
        if (Test-Path -LiteralPath $tempDir) {
            Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

try {
    Invoke-KoaPythonAddLibraryRow
}
catch {
    $errorResult = New-KoaLocalResult `
        -Success $false `
        -Result "failed" `
        -Path $FilePath `
        -Errors @(
            New-KoaLocalMessage `
                -Code "ERR_ADD_LIBRARY_ROW_FAILED" `
                -Severity "blocking" `
                -Message $_.Exception.Message `
                -Field "Add-KoaLibraryRow"
        )

    Write-KoaLocalJsonResult -Result $errorResult
    exit 1
}