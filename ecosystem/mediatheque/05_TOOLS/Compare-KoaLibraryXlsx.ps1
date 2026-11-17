# 05_TOOLS/Compare-KoaLibraryXlsx.ps1
# Médiathèque kOA — Compare XLSX Library sheet against SQLite without applying changes
# PowerShell 7 only. Emits exactly one JSON result to stdout.
# Uses Python sqlite3 + openpyxl. Does not require Excel, ImportExcel, or sqlite3.exe.

#requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $DbPath,

    [Parameter(Mandatory)]
    [string] $XlsxPath,

    [ValidateSet("normal", "repair")]
    [string] $Mode = "normal"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$Operation = "Compare-KoaLibraryXlsx"

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

        [string] $EntityType = "xlsx_import",

        [string] $EntityUuid = "",

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
        version_uuid = ""
        media_uuid   = ""
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

    throw "Python was not found. Compare-KoaLibraryXlsx.ps1 requires Python with sqlite3 and openpyxl."
}

function Invoke-KoaPythonCompare {
    param(
        [Parameter(Mandatory)]
        [string] $DatabasePath,

        [Parameter(Mandatory)]
        [string] $WorkbookPath,

        [Parameter(Mandatory)]
        [string] $CompareMode
    )

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

    $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("koa_xlsx_compare_" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

    $scriptPath = Join-Path $tempDir "compare_xlsx.py"
    $stderrPath = Join-Path $tempDir "python_stderr.txt"

    $pythonCode = @'
from __future__ import annotations

import json
import sqlite3
import sys
import traceback
from pathlib import Path
from uuid import uuid4


OPERATION = "Compare-KoaLibraryXlsx"
LIBRARY_SHEET_NAME = "Library"

ALLOWED_ACTIONS = {"update", "ignore", "archive", "new"}

PROTECTED_FIELDS_NORMAL = {
    "id",
    "media_uuid",
    "version_uuid",
    "filename",
    "original_path",
    "storage_path",
    "sha256",
    "filesize",
    "mimetype",
    "extension",
    "created_at",
    "updated_at",
}

INTERNAL_COLUMNS = {"xlsx_action", "action"}

JSON_ALIAS_TO_DB = {
    "collections": "collections_json",
    "tags": "tags_json",
    "relations": "relations_json",
    "content_flags": "content_flags_json",
}

DB_JSON_TO_XLSX_ALIAS = {
    "collections_json": "collections",
    "tags_json": "tags",
    "relations_json": "relations",
    "content_flags_json": "content_flags",
}


def message(code, severity, message, field=None, row_number=None, details=None):
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "field": field,
        "row_number": row_number,
        "details": details or {},
    }


def result(
    *,
    success: bool,
    result_text: str,
    path: str = "",
    entity_uuid: str = "",
    data=None,
    warnings=None,
    errors=None,
):
    return {
        "success": success,
        "operation": OPERATION,
        "result": result_text,
        "entity_type": "xlsx_import",
        "entity_uuid": entity_uuid or "",
        "version_uuid": "",
        "media_uuid": "",
        "path": path or "",
        "data": data or {},
        "warnings": warnings or [],
        "errors": errors or [],
    }


def emit(payload, exit_code: int) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=False))
    raise SystemExit(exit_code)


def clean_cell(value):
    if value is None:
        return None

    if isinstance(value, str):
        text = value.strip()
        return text if text else None

    return value


def clean_string(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_action(value) -> str:
    text = clean_string(value).lower()
    return text if text else "ignore"


def is_empty_row(row: dict) -> bool:
    return all(value is None or clean_string(value) == "" for value in row.values())


def normalize_compare_value(value) -> str:
    if value is None:
        return ""

    if isinstance(value, bool):
        return "1" if value else "0"

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    text = str(value).strip()

    if text.lower() in {"true", "yes", "oui"}:
        return "1"

    if text.lower() in {"false", "no", "non"}:
        return "0"

    return text


def normalize_json_array_text(value) -> str:
    if value is None:
        return "[]"

    if isinstance(value, list):
        return json.dumps(
            [clean_string(item) for item in value if clean_string(item)],
            ensure_ascii=False,
            sort_keys=True,
        )

    text = str(value).strip()

    if not text:
        return "[]"

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return json.dumps(
                [clean_string(item) for item in parsed if clean_string(item)],
                ensure_ascii=False,
                sort_keys=True,
            )
        return json.dumps([parsed], ensure_ascii=False, sort_keys=True)
    except Exception:
        pass

    if ";" in text:
        values = [part.strip() for part in text.split(";") if part.strip()]
        return json.dumps(values, ensure_ascii=False, sort_keys=True)

    return json.dumps([text], ensure_ascii=False, sort_keys=True)


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        LIMIT 1
        """,
        (table_name,),
    ).fetchone()

    return row is not None


def table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    cursor = connection.execute(f"PRAGMA table_info({table_name})")
    try:
        return {str(row[1]) for row in cursor.fetchall()}
    finally:
        cursor.close()


def fetch_library_rows(db_path: Path) -> tuple[dict[str, dict], set[str]]:
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row

    try:
        if not table_exists(connection, "library_rows"):
            raise RuntimeError("SQLite table not found: library_rows")

        columns = table_columns(connection, "library_rows")

        cursor = connection.execute(
            """
            SELECT *
            FROM library_rows
            """
        )

        try:
            rows = [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()

        by_version_uuid = {
            clean_string(row.get("version_uuid")): row
            for row in rows
            if clean_string(row.get("version_uuid"))
        }

        return by_version_uuid, columns
    finally:
        connection.close()


def read_library_sheet(xlsx_path: Path) -> list[dict]:
    try:
        from openpyxl import load_workbook
    except Exception as exc:
        raise RuntimeError(
            "Python package openpyxl is required. Install it in the active Python environment."
        ) from exc

    workbook = load_workbook(str(xlsx_path), data_only=True)

    if LIBRARY_SHEET_NAME not in workbook.sheetnames:
        raise RuntimeError("Workbook must contain a Library sheet.")

    worksheet = workbook[LIBRARY_SHEET_NAME]
    header_values = next(worksheet.iter_rows(min_row=1, max_row=1, values_only=True), None)

    if not header_values:
        return []

    headers = [
        str(value).strip() if value is not None else ""
        for value in header_values
    ]

    rows = []

    for row_number, values in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
        row = {
            headers[index]: clean_cell(value)
            for index, value in enumerate(values)
            if index < len(headers) and headers[index]
        }

        if is_empty_row(row):
            continue

        row["_row_number"] = row_number
        rows.append(row)

    return rows


def xlsx_row_to_updates(
    row: dict,
    *,
    table_column_names: set[str],
    mode: str,
    include_protected: bool = False,
) -> tuple[dict, list[str]]:
    updates = {}
    ignored_protected = []

    for key, value in row.items():
        if key == "_row_number" or key in INTERNAL_COLUMNS:
            continue

        db_key = JSON_ALIAS_TO_DB.get(key, key)

        if db_key not in table_column_names:
            continue

        if not include_protected and mode != "repair" and db_key in PROTECTED_FIELDS_NORMAL:
            if value is not None:
                ignored_protected.append(db_key)
            continue

        if value is None:
            continue

        if db_key in DB_JSON_TO_XLSX_ALIAS:
            updates[db_key] = normalize_json_array_text(value)
        else:
            updates[db_key] = value

    return updates, sorted(set(ignored_protected))


def diff_updates(existing: dict, updates: dict) -> list[dict]:
    diffs = []

    for key in sorted(updates):
        before = existing.get(key)
        after = updates.get(key)

        if normalize_compare_value(before) == normalize_compare_value(after):
            continue

        diffs.append(
            {
                "field": key,
                "before": before,
                "after": after,
            }
        )

    return diffs


def row_summary(row: dict) -> dict:
    return {
        "media_uuid": clean_string(row.get("media_uuid")),
        "version_uuid": clean_string(row.get("version_uuid")),
        "title": clean_string(row.get("title")),
        "filename": clean_string(row.get("filename")),
        "sha256": clean_string(row.get("sha256")),
        "status": clean_string(row.get("status")),
    }


def compare(db_path: Path, xlsx_path: Path, mode: str) -> dict:
    compare_uuid = str(uuid4())
    warnings = []
    errors = []
    changes = []

    db_rows, table_column_names = fetch_library_rows(db_path)
    xlsx_rows = read_library_sheet(xlsx_path)

    counts = {
        "rows_total": len(xlsx_rows),
        "rows_update": 0,
        "rows_new": 0,
        "rows_archive": 0,
        "rows_ignore": 0,
        "rows_blocked": 0,
        "rows_nochange": 0,
    }

    for row in xlsx_rows:
        row_number = int(row.get("_row_number") or 0)
        action = normalize_action(row.get("xlsx_action", row.get("action")))
        version_uuid = clean_string(row.get("version_uuid"))

        if action not in ALLOWED_ACTIONS:
            row_error = message(
                "ERR_XLSX_INVALID_ACTION",
                "blocking",
                f"Invalid XLSX action: {action}",
                "xlsx_action",
                row_number,
                {"allowed": sorted(ALLOWED_ACTIONS)},
            )
            errors.append(row_error)
            counts["rows_blocked"] += 1
            changes.append(
                {
                    "row_number": row_number,
                    "action": action,
                    "result": "blocked",
                    "version_uuid": version_uuid,
                    "errors": [row_error],
                    "raw_row": row,
                }
            )
            continue

        if action == "ignore":
            counts["rows_ignore"] += 1
            changes.append(
                {
                    "row_number": row_number,
                    "action": "ignore",
                    "result": "ignored",
                    "version_uuid": version_uuid,
                    "raw_row": row,
                }
            )
            continue

        if action in {"update", "archive"} and not version_uuid:
            row_error = message(
                "ERR_VERSION_UUID_MISSING",
                "blocking",
                "version_uuid is required for update and archive actions.",
                "version_uuid",
                row_number,
            )
            errors.append(row_error)
            counts["rows_blocked"] += 1
            changes.append(
                {
                    "row_number": row_number,
                    "action": action,
                    "result": "blocked",
                    "version_uuid": "",
                    "errors": [row_error],
                    "raw_row": row,
                }
            )
            continue

        if action in {"update", "archive"} and version_uuid not in db_rows:
            row_error = message(
                "ERR_VERSION_UUID_MISSING",
                "blocking",
                "version_uuid was not found in SQLite.",
                "version_uuid",
                row_number,
                {"version_uuid": version_uuid},
            )
            errors.append(row_error)
            counts["rows_blocked"] += 1
            changes.append(
                {
                    "row_number": row_number,
                    "action": action,
                    "result": "blocked",
                    "version_uuid": version_uuid,
                    "errors": [row_error],
                    "raw_row": row,
                }
            )
            continue

        if action == "archive":
            existing = db_rows[version_uuid]
            counts["rows_archive"] += 1
            changes.append(
                {
                    "row_number": row_number,
                    "action": "archive",
                    "result": "would_archive",
                    "version_uuid": version_uuid,
                    "media_uuid": clean_string(existing.get("media_uuid")),
                    "title": clean_string(existing.get("title")),
                    "before": row_summary(existing),
                    "after": {
                        **row_summary(existing),
                        "status": "archived",
                    },
                    "diffs": [
                        {
                            "field": "status",
                            "before": existing.get("status"),
                            "after": "archived",
                        }
                    ],
                    "raw_row": row,
                }
            )
            continue

        if action == "new":
            counts["rows_new"] += 1

            updates, ignored_protected = xlsx_row_to_updates(
                row,
                table_column_names=table_column_names,
                mode="repair",
                include_protected=True,
            )

            if version_uuid and version_uuid in db_rows:
                row_error = message(
                    "ERR_VERSION_UUID_DUPLICATE",
                    "blocking",
                    "version_uuid already exists in SQLite.",
                    "version_uuid",
                    row_number,
                    {"version_uuid": version_uuid},
                )
                errors.append(row_error)
                counts["rows_blocked"] += 1
                changes.append(
                    {
                        "row_number": row_number,
                        "action": "new",
                        "result": "blocked",
                        "version_uuid": version_uuid,
                        "errors": [row_error],
                        "raw_row": row,
                    }
                )
                continue

            changes.append(
                {
                    "row_number": row_number,
                    "action": "new",
                    "result": "would_insert",
                    "version_uuid": version_uuid,
                    "media_uuid": clean_string(row.get("media_uuid")),
                    "title": clean_string(row.get("title")),
                    "updates": updates,
                    "ignored_protected_changes": ignored_protected,
                    "raw_row": row,
                }
            )
            continue

        existing = db_rows[version_uuid]
        updates, ignored_protected = xlsx_row_to_updates(
            row,
            table_column_names=table_column_names,
            mode=mode,
            include_protected=False,
        )
        diffs = diff_updates(existing, updates)

        counts["rows_update"] += 1

        if not diffs:
            counts["rows_nochange"] += 1
            change_result = "no_changes"
        else:
            change_result = "would_update"

        changes.append(
            {
                "row_number": row_number,
                "action": "update",
                "result": change_result,
                "version_uuid": version_uuid,
                "media_uuid": clean_string(existing.get("media_uuid")),
                "title": clean_string(row.get("title") or existing.get("title")),
                "before": row_summary(existing),
                "updates": updates,
                "diffs": diffs,
                "ignored_protected_changes": ignored_protected,
                "raw_row": row,
            }
        )

    is_blocked = len(errors) > 0

    return result(
        success=not is_blocked,
        result_text="comparison_blocked" if is_blocked else "comparison_completed",
        path=str(xlsx_path),
        entity_uuid=compare_uuid,
        data={
            "compare_uuid": compare_uuid,
            "mode": mode,
            "db_path": str(db_path),
            "xlsx_path": str(xlsx_path),
            **counts,
            "changes": changes,
            "note": "No SQLite data was modified by Compare-KoaLibraryXlsx.ps1.",
        },
        warnings=warnings,
        errors=errors,
    )


def main() -> None:
    db_path = Path(sys.argv[1]).expanduser()
    xlsx_path = Path(sys.argv[2]).expanduser()
    mode = sys.argv[3] if len(sys.argv) > 3 else "normal"

    if not db_path.exists() or not db_path.is_file():
        emit(
            result(
                success=False,
                result_text="db_not_found",
                path=str(xlsx_path),
                errors=[
                    message(
                        "ERR_DB_NOT_FOUND",
                        "blocking",
                        f"SQLite database not found: {db_path}",
                        "DbPath",
                        details={"db_path": str(db_path)},
                    )
                ],
            ),
            1,
        )

    if not xlsx_path.exists() or not xlsx_path.is_file():
        emit(
            result(
                success=False,
                result_text="xlsx_not_found",
                path=str(xlsx_path),
                errors=[
                    message(
                        "ERR_FILE_NOT_FOUND",
                        "blocking",
                        f"XLSX file not found: {xlsx_path}",
                        "XlsxPath",
                        details={"xlsx_path": str(xlsx_path)},
                    )
                ],
            ),
            1,
        )

    if mode not in {"normal", "repair"}:
        emit(
            result(
                success=False,
                result_text="invalid_mode",
                path=str(xlsx_path),
                errors=[
                    message(
                        "ERR_INVALID_ENUM",
                        "blocking",
                        f"Invalid mode: {mode}",
                        "Mode",
                        details={"allowed": ["normal", "repair"]},
                    )
                ],
            ),
            1,
        )

    try:
        payload = compare(db_path, xlsx_path, mode)
        emit(payload, 1 if not payload["success"] else 0)
    except Exception as exc:
        emit(
            result(
                success=False,
                result_text="failed",
                path=str(xlsx_path),
                errors=[
                    message(
                        "ERR_XLSX_COMPARE_FAILED",
                        "blocking",
                        str(exc),
                        "Compare-KoaLibraryXlsx",
                        details={"traceback": traceback.format_exc()},
                    )
                ],
            ),
            1,
        )


if __name__ == "__main__":
    main()
'@

    Set-Content -LiteralPath $scriptPath -Value $pythonCode -Encoding UTF8

    try {
        $allArgs = @()
        $allArgs += $pythonArgs
        $allArgs += $scriptPath
        $allArgs += $DatabasePath
        $allArgs += $WorkbookPath
        $allArgs += $CompareMode

        $stdout = & $pythonExe @allArgs 2>$stderrPath
        $exitCode = $LASTEXITCODE
        $raw = ($stdout | Out-String)
        $stderr = ""

        if ($null -eq $raw) {
            $raw = ""
        }

        $raw = $raw.Trim()

        if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
            $stderrContent = Get-Content -LiteralPath $stderrPath -Raw -ErrorAction SilentlyContinue
            if ($null -ne $stderrContent) {
                $stderr = $stderrContent.Trim()
            }
        }

        if ([string]::IsNullOrWhiteSpace($raw)) {
            $fallback = New-KoaLocalResult `
                -Success $false `
                -Result "failed" `
                -Path $WorkbookPath `
                -Errors @(
                    New-KoaLocalMessage `
                        -Code "ERR_XLSX_COMPARE_FAILED" `
                        -Severity "blocking" `
                        -Message "Python helper produced no JSON output. $stderr" `
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
    Invoke-KoaPythonCompare `
        -DatabasePath $DbPath `
        -WorkbookPath $XlsxPath `
        -CompareMode $Mode
}
catch {
    $errorResult = New-KoaLocalResult `
        -Success $false `
        -Result "failed" `
        -Path $XlsxPath `
        -Errors @(
            New-KoaLocalMessage `
                -Code "ERR_XLSX_COMPARE_FAILED" `
                -Severity "blocking" `
                -Message $_.Exception.Message `
                -Field "Compare-KoaLibraryXlsx"
        )

    Write-KoaLocalJsonResult -Result $errorResult
    exit 1
}