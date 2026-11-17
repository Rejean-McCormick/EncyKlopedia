# 05_TOOLS/Purge-KoaSoftDeletedRows.ps1
# Médiathèque kOA — Permanently purge library_rows marked deleted_soft
# PowerShell 7 only. Emits exactly one JSON result to stdout.
#
# Safety:
# - Applies by default.
# - Use -DryRun to preview without deleting.
# - Creates a SQLite backup before deletion.
# - Deletes DB rows only. Never deletes files from original_path or storage_path.

#requires -Version 7.0

[CmdletBinding()]
param(
    [string] $DbPath = "",

    [string] $BackupDir = "",

    [switch] $DryRun,

    [int] $Limit = 0,

    [string] $Actor = "local_user",

    [string] $Reason = "purge deleted_soft rows"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Operation = "Purge-KoaSoftDeletedRows"

function Get-KoaTimestamp {
    return [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function New-KoaMessage {
    param(
        [Parameter(Mandatory)]
        [string] $Code,

        [Parameter(Mandatory)]
        [string] $Severity,

        [Parameter(Mandatory)]
        [string] $Message,

        [string] $Field = "",

        [hashtable] $Details = @{}
    )

    return [ordered]@{
        code       = $Code
        severity   = $Severity
        message    = $Message
        field      = $Field
        row_number = $null
        details    = $Details
    }
}

function New-KoaOperationResult {
    param(
        [Parameter(Mandatory)]
        [bool] $Success,

        [Parameter(Mandatory)]
        [string] $Result,

        [string] $Path = "",

        [hashtable] $Data = @{},

        [array] $Warnings = @(),

        [array] $Errors = @()
    )

    return [ordered]@{
        success      = $Success
        operation    = $Operation
        result       = $Result
        entity_type  = "library_rows"
        entity_uuid  = ""
        version_uuid = ""
        media_uuid   = ""
        path         = $Path
        data         = $Data
        warnings     = @($Warnings)
        errors       = @($Errors)
    }
}

function Write-KoaJsonResult {
    param(
        [Parameter(Mandatory)]
        [object] $Result
    )

    [Console]::Out.WriteLine(($Result | ConvertTo-Json -Depth 100))
}

function Resolve-KoaRootPath {
    param(
        [Parameter(Mandatory)]
        [string] $StartingPath
    )

    $resolved = Resolve-Path -LiteralPath $StartingPath -ErrorAction SilentlyContinue

    if ($resolved) {
        $currentPath = [string] $resolved.ProviderPath
    }
    else {
        $currentPath = [System.IO.Path]::GetFullPath($StartingPath)
    }

    if (Test-Path -LiteralPath $currentPath -PathType Leaf) {
        $currentPath = Split-Path -Parent $currentPath
    }

    while (-not [string]::IsNullOrWhiteSpace($currentPath)) {
        $candidate = Join-Path $currentPath "pyproject.toml"

        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $currentPath
        }

        $parent = Split-Path -Parent $currentPath

        if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $currentPath) {
            break
        }

        $currentPath = $parent
    }

    return (Split-Path -Parent $PSScriptRoot)
}

function Get-KoaPythonCommand {
    param(
        [Parameter(Mandatory)]
        [string] $RepoRoot
    )

    $venvPython = Join-Path $RepoRoot ".venv/Scripts/python.exe"

    if (Test-Path -LiteralPath $venvPython -PathType Leaf) {
        return $venvPython
    }

    foreach ($candidate in @("python", "py")) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            return $candidate
        }
    }

    throw "Python introuvable. Active la venv ou installe Python."
}

try {
    $repoRoot = Resolve-KoaRootPath -StartingPath $PSScriptRoot

    $contentRoot = if (-not [string]::IsNullOrWhiteSpace($env:KOA_CONTENT_ROOT)) {
        [System.IO.Path]::GetFullPath($env:KOA_CONTENT_ROOT)
    } else {
        [System.IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $repoRoot) "content"))
    }

    if ([string]::IsNullOrWhiteSpace($DbPath)) {
        $DbPath = Join-Path $contentRoot "01_DB/koa_mediatheque.sqlite"
    }

    if ([string]::IsNullOrWhiteSpace($BackupDir)) {
        $BackupDir = Join-Path $contentRoot "07_BACKUPS"
    }

    $dbFullPath = [System.IO.Path]::GetFullPath($DbPath)
    $backupFullDir = [System.IO.Path]::GetFullPath($BackupDir)

    if (-not (Test-Path -LiteralPath $dbFullPath -PathType Leaf)) {
        $result = New-KoaOperationResult `
            -Success $false `
            -Result "db_not_found" `
            -Path $dbFullPath `
            -Errors @(
                New-KoaMessage `
                    -Code "ERR_DB_NOT_FOUND" `
                    -Severity "blocking" `
                    -Message "Base SQLite introuvable : $dbFullPath" `
                    -Details @{ db_path = $dbFullPath }
            )

        Write-KoaJsonResult -Result $result
        exit 1
    }

    if ($Limit -lt 0) {
        $result = New-KoaOperationResult `
            -Success $false `
            -Result "invalid_limit" `
            -Path $dbFullPath `
            -Errors @(
                New-KoaMessage `
                    -Code "ERR_INVALID_LIMIT" `
                    -Severity "blocking" `
                    -Message "Limit doit être >= 0."
            )

        Write-KoaJsonResult -Result $result
        exit 1
    }

    $python = Get-KoaPythonCommand -RepoRoot $repoRoot

    $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("koa_purge_soft_deleted_" + [System.Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

    $pythonScript = Join-Path $tempDir "purge_soft_deleted.py"

    $pythonCode = @'
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def msg(
    code: str,
    severity: str,
    message: str,
    field: str = "",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "field": field,
        "row_number": None,
        "details": details or {},
    }


def result(
    *,
    success: bool,
    result_text: str,
    db_path: str,
    data: dict[str, Any] | None = None,
    warnings: list[dict[str, Any]] | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "success": success,
        "operation": "Purge-KoaSoftDeletedRows",
        "result": result_text,
        "entity_type": "library_rows",
        "entity_uuid": "",
        "version_uuid": "",
        "media_uuid": "",
        "path": db_path,
        "data": data or {},
        "warnings": warnings or [],
        "errors": errors or [],
    }


def table_exists(con: sqlite3.Connection, table_name: str) -> bool:
    row = con.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def get_columns(con: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in con.execute(f"PRAGMA table_info({table_name})").fetchall()}


def fetch_deleted_rows(con: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    sql = """
        SELECT *
        FROM library_rows
        WHERE COALESCE(status, '') = 'deleted_soft'
        ORDER BY id
    """

    params: tuple[Any, ...] = ()

    if limit > 0:
        sql += " LIMIT ?"
        params = (limit,)

    return list(con.execute(sql, params).fetchall())


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def insert_audit_rows(
    con: sqlite3.Connection,
    *,
    rows: list[sqlite3.Row],
    actor: str,
    reason: str,
) -> None:
    if not table_exists(con, "audit_log"):
        return

    audit_columns = get_columns(con, "audit_log")
    required = {
        "actor",
        "action",
        "entity_type",
        "entity_uuid",
        "before_json",
        "after_json",
        "note",
        "created_at",
    }

    if not required.issubset(audit_columns):
        return

    now = utc_now_iso()

    for row in rows:
        before = row_to_dict(row)
        version_uuid = str(before.get("version_uuid") or "")

        con.execute(
            """
            INSERT INTO audit_log (
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
                actor,
                "library_rows_purged_deleted_soft",
                "library_row",
                version_uuid,
                json.dumps(before, ensure_ascii=False, sort_keys=True),
                None,
                reason,
                now,
            ),
        )


def make_backup(db_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"before_purge_deleted_soft_{stamp}.sqlite"
    shutil.copy2(db_path, backup_path)
    return backup_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--backup-dir", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--actor", default="local_user")
    parser.add_argument("--reason", default="purge deleted_soft rows")
    args = parser.parse_args()

    db_path = Path(args.db_path)
    backup_dir = Path(args.backup_dir)

    if not db_path.exists():
        print(json.dumps(result(
            success=False,
            result_text="db_not_found",
            db_path=str(db_path),
            errors=[msg("ERR_DB_NOT_FOUND", "blocking", f"Base SQLite introuvable : {db_path}")],
        ), ensure_ascii=False))
        return 1

    if args.limit < 0:
        print(json.dumps(result(
            success=False,
            result_text="invalid_limit",
            db_path=str(db_path),
            errors=[msg("ERR_INVALID_LIMIT", "blocking", "Limit doit être >= 0.")],
        ), ensure_ascii=False))
        return 1

    backup_path: Path | None = None

    try:
        with sqlite3.connect(db_path) as con:
            con.row_factory = sqlite3.Row

            if not table_exists(con, "library_rows"):
                print(json.dumps(result(
                    success=False,
                    result_text="missing_library_rows_table",
                    db_path=str(db_path),
                    errors=[msg("ERR_DB_SCHEMA", "blocking", "Table library_rows introuvable.")],
                ), ensure_ascii=False))
                return 1

            columns = get_columns(con, "library_rows")
            required_columns = {
                "id",
                "version_uuid",
                "media_uuid",
                "title",
                "filename",
                "original_path",
                "storage_path",
                "status",
            }

            missing_columns = sorted(required_columns - columns)
            if missing_columns:
                print(json.dumps(result(
                    success=False,
                    result_text="invalid_library_rows_schema",
                    db_path=str(db_path),
                    errors=[msg(
                        "ERR_DB_SCHEMA",
                        "blocking",
                        "Colonnes requises manquantes dans library_rows.",
                        details={"missing_columns": missing_columns},
                    )],
                ), ensure_ascii=False))
                return 1

            rows = fetch_deleted_rows(con, args.limit)
            rows_preview = [
                {
                    "id": row["id"],
                    "version_uuid": row["version_uuid"],
                    "media_uuid": row["media_uuid"],
                    "title": row["title"],
                    "filename": row["filename"],
                    "original_path": row["original_path"],
                    "storage_path": row["storage_path"],
                    "status": row["status"],
                }
                for row in rows
            ]

            if not args.apply:
                print(json.dumps(result(
                    success=True,
                    result_text="dry_run",
                    db_path=str(db_path),
                    data={
                        "apply": False,
                        "rows_to_purge": len(rows),
                        "limit": args.limit,
                        "backup_path": None,
                        "deleted_rows": rows_preview,
                        "files_deleted": 0,
                        "note": "Dry-run only. Run the PowerShell script without -DryRun to permanently delete rows from library_rows.",
                    },
                ), ensure_ascii=False, indent=2))
                return 0

        backup_path = make_backup(db_path, backup_dir)

        with sqlite3.connect(db_path) as con:
            con.row_factory = sqlite3.Row
            rows = fetch_deleted_rows(con, args.limit)

            if not rows:
                print(json.dumps(result(
                    success=True,
                    result_text="nothing_to_purge",
                    db_path=str(db_path),
                    data={
                        "apply": True,
                        "rows_purged": 0,
                        "limit": args.limit,
                        "backup_path": str(backup_path),
                        "files_deleted": 0,
                    },
                ), ensure_ascii=False, indent=2))
                return 0

            row_ids = [row["id"] for row in rows]

            try:
                con.execute("BEGIN")

                insert_audit_rows(
                    con,
                    rows=rows,
                    actor=args.actor,
                    reason=args.reason,
                )

                placeholders = ", ".join("?" for _ in row_ids)
                con.execute(
                    f"DELETE FROM library_rows WHERE id IN ({placeholders})",
                    row_ids,
                )

                con.commit()
            except Exception:
                con.rollback()
                raise

            print(json.dumps(result(
                success=True,
                result_text="purged",
                db_path=str(db_path),
                data={
                    "apply": True,
                    "rows_purged": len(row_ids),
                    "limit": args.limit,
                    "backup_path": str(backup_path),
                    "purged_ids": row_ids,
                    "purged_version_uuids": [row["version_uuid"] for row in rows],
                    "files_deleted": 0,
                    "note": "Only library_rows rows were deleted. No original_path or storage_path files were deleted.",
                },
            ), ensure_ascii=False, indent=2))
            return 0

    except Exception as exc:
        print(json.dumps(result(
            success=False,
            result_text="failed",
            db_path=str(db_path),
            data={
                "backup_path": str(backup_path) if backup_path else None,
            },
            errors=[msg("ERR_PURGE_SOFT_DELETED_FAILED", "blocking", str(exc))],
        ), ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
'@

    Set-Content -LiteralPath $pythonScript -Value $pythonCode -Encoding UTF8

    $argsList = @(
        $pythonScript,
        "--db-path", $dbFullPath,
        "--backup-dir", $backupFullDir,
        "--limit", [string] $Limit,
        "--actor", $Actor,
        "--reason", $Reason
    )

    if (-not $DryRun) {
        $argsList += "--apply"
    }

    & $python @argsList
    $exitCode = $LASTEXITCODE

    Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue

    exit $exitCode
}
catch {
    $errorResult = New-KoaOperationResult `
        -Success $false `
        -Result "failed" `
        -Path $DbPath `
        -Errors @(
            New-KoaMessage `
                -Code "ERR_PURGE_SOFT_DELETED_FAILED" `
                -Severity "blocking" `
                -Message $_.Exception.Message
        )

    Write-KoaJsonResult -Result $errorResult
    exit 1
}