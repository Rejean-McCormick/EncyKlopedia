# 05_TOOLS/Export-KoaLibraryXlsx.ps1
# Médiathèque kOA — Export library_rows to XLSX
# PowerShell 7 only. Emits exactly one JSON result to stdout.
# Uses Python sqlite3 + openpyxl. Does not require Excel, ImportExcel, or sqlite3.exe.

#requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $DbPath,

    [Parameter(Mandatory)]
    [string] $OutputPath,

    [string] $FilterJson = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$Operation = "Export-KoaLibraryXlsx"

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

        [string] $EntityType = "xlsx_export",

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

    Write-Output ($Result | ConvertTo-Json -Depth 100 -Compress:$false)
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

    throw "Python was not found. Export-KoaLibraryXlsx.ps1 requires Python with sqlite3 and openpyxl."
}

function Invoke-KoaPythonExport {
    param(
        [Parameter(Mandatory)]
        [string] $DatabasePath,

        [Parameter(Mandatory)]
        [string] $WorkbookPath,

        [string] $FilterJsonText = ""
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

    $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("koa_xlsx_export_" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

    $scriptPath = Join-Path $tempDir "export_xlsx.py"
    $stderrPath = Join-Path $tempDir "python_stderr.txt"

    $pythonCode = @'
from __future__ import annotations

import json
import sqlite3
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


OPERATION = "Export-KoaLibraryXlsx"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
        "entity_type": "xlsx_export",
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


def parse_filter_json(text: str) -> dict:
    if text is None or not str(text).strip():
        return {}

    parsed = json.loads(text)

    if parsed is None:
        return {}

    if not isinstance(parsed, dict):
        raise ValueError("FilterJson must be a JSON object.")

    return parsed


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    cursor = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        LIMIT 1
        """,
        (table_name,),
    )

    try:
        return cursor.fetchone() is not None
    finally:
        cursor.close()


def table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    cursor = connection.execute(f"PRAGMA table_info({table_name})")
    try:
        return {str(row[1]) for row in cursor.fetchall()}
    finally:
        cursor.close()


def normalize_json_array_text(value) -> str:
    if value is None:
        return ""

    text = str(value).strip()
    if not text:
        return ""

    try:
        parsed = json.loads(text)
    except Exception:
        return text

    if parsed is None:
        return ""

    if not isinstance(parsed, list):
        parsed = [parsed]

    items = []
    for item in parsed:
        if item is None:
            continue

        if isinstance(item, (dict, list)):
            item_text = json.dumps(item, ensure_ascii=False, sort_keys=True)
        else:
            item_text = str(item).strip()

        if item_text:
            items.append(item_text)

    return "; ".join(items)


def get_row_value(row: dict, key: str, default=""):
    value = row.get(key, default)
    if value is None:
        return ""
    return value


def build_where_clause(filters: dict, available_columns: set[str]):
    clauses = []
    params = []

    for key, value in filters.items():
        if key not in available_columns:
            continue

        if value is None:
            continue

        if isinstance(value, str) and not value.strip():
            continue

        if isinstance(value, list):
            values = [item for item in value if item is not None and str(item).strip()]
            if not values:
                continue

            placeholders = ", ".join("?" for _ in values)
            clauses.append(f"{key} IN ({placeholders})")
            params.extend(values)
            continue

        clauses.append(f"{key} = ?")
        params.append(value)

    if not clauses:
        return "", []

    return "WHERE " + " AND ".join(clauses), params


def fetch_library_rows(db_path: Path, filters: dict):
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row

    try:
        if not table_exists(connection, "library_rows"):
            raise RuntimeError("SQLite table not found: library_rows")

        columns = table_columns(connection, "library_rows")
        where_sql, params = build_where_clause(filters, columns)

        cursor = connection.execute(
            f"""
            SELECT *
            FROM library_rows
            {where_sql}
            ORDER BY title COLLATE NOCASE ASC, id ASC
            """,
            params,
        )

        try:
            return [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()
    finally:
        connection.close()


def insert_audit_log(db_path: Path, export_uuid: str, output_path: Path, row_count: int, filters: dict):
    connection = sqlite3.connect(str(db_path))

    try:
        if not table_exists(connection, "audit_log"):
            return

        columns = table_columns(connection, "audit_log")

        payload = {
            "actor": "ps7",
            "action": "xlsx_exported",
            "entity_type": "xlsx_export",
            "entity_uuid": export_uuid,
            "before_json": "{}",
            "after_json": json.dumps(
                {
                    "output_path": str(output_path),
                    "row_count": row_count,
                    "filters": filters,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            "note": "Export-KoaLibraryXlsx.ps1",
            "created_at": now_iso(),
        }

        filtered = {key: value for key, value in payload.items() if key in columns}

        if not filtered:
            return

        column_sql = ", ".join(filtered)
        placeholders = ", ".join("?" for _ in filtered)

        cursor = connection.execute(
            f"""
            INSERT INTO audit_log ({column_sql})
            VALUES ({placeholders})
            """,
            list(filtered.values()),
        )

        try:
            connection.commit()
        finally:
            cursor.close()
    finally:
        connection.close()


LIBRARY_HEADERS = [
    "action",
    "media_uuid",
    "version_uuid",
    "title",
    "subtitle",
    "description",
    "summary",
    "original_path",
    "storage_path",
    "filename",
    "extension",
    "mimetype",
    "filesize",
    "sha256",
    "filearea",
    "media_type",
    "language",
    "library_scope",
    "uckk_relevance",
    "target_system",
    "target_export_allowed",
    "public_state",
    "visibility",
    "access_level",
    "ownership_scope",
    "source_type",
    "source_ownership",
    "rights_status",
    "rights_note",
    "restriction_state",
    "restriction_reason",
    "redaction_required",
    "status",
    "provenance",
    "ai_validation_state",
    "ai_confidence",
    "canonical_validation_state",
    "human_review_required",
    "review_queue",
    "review_reason",
    "collections",
    "tags",
    "relations",
    "content_flags",
    "audience_suitability",
    "export_to_uckk",
    "export_to_public",
    "export_policy_note",
    "import_batch",
    "notes",
    "created_at",
    "updated_at",
]


LISTS_ROWS = [
    ("xlsx_action", "update"),
    ("xlsx_action", "ignore"),
    ("xlsx_action", "archive"),
    ("xlsx_action", "new"),
    ("visibility", "public"),
    ("visibility", "private"),
    ("visibility", "restricted"),
    ("visibility", "unknown"),
    ("public_state", "public"),
    ("public_state", "private"),
    ("public_state", "non_public"),
    ("public_state", "unknown"),
    ("rights_status", "owned"),
    ("rights_status", "third_party"),
    ("rights_status", "unknown"),
    ("rights_status", "fair_use_reference"),
    ("restriction_state", "none"),
    ("restriction_state", "possible"),
    ("restriction_state", "restricted"),
    ("export_to_public", "yes"),
    ("export_to_public", "no"),
    ("export_to_uckk", "yes"),
    ("export_to_uckk", "no"),
    ("target_system", "uckkarchive"),
    ("target_system", "none"),
    ("target_export_allowed", "0"),
    ("target_export_allowed", "1"),
    ("canonical_validation_state", "unverified"),
    ("canonical_validation_state", "human_reviewed"),
    ("canonical_validation_state", "verified"),
]


def library_row_to_xlsx_row(row: dict) -> list:
    return [
        "update",
        get_row_value(row, "media_uuid"),
        get_row_value(row, "version_uuid"),
        get_row_value(row, "title"),
        get_row_value(row, "subtitle"),
        get_row_value(row, "description"),
        get_row_value(row, "summary"),
        get_row_value(row, "original_path"),
        get_row_value(row, "storage_path"),
        get_row_value(row, "filename"),
        get_row_value(row, "extension"),
        get_row_value(row, "mimetype"),
        get_row_value(row, "filesize"),
        get_row_value(row, "sha256"),
        get_row_value(row, "filearea"),
        get_row_value(row, "media_type"),
        get_row_value(row, "language"),
        get_row_value(row, "library_scope"),
        get_row_value(row, "uckk_relevance"),
        get_row_value(row, "target_system"),
        get_row_value(row, "target_export_allowed"),
        get_row_value(row, "public_state"),
        get_row_value(row, "visibility"),
        get_row_value(row, "access_level"),
        get_row_value(row, "ownership_scope"),
        get_row_value(row, "source_type"),
        get_row_value(row, "source_ownership"),
        get_row_value(row, "rights_status"),
        get_row_value(row, "rights_note"),
        get_row_value(row, "restriction_state"),
        get_row_value(row, "restriction_reason"),
        get_row_value(row, "redaction_required"),
        get_row_value(row, "status"),
        get_row_value(row, "provenance"),
        get_row_value(row, "ai_validation_state"),
        get_row_value(row, "ai_confidence"),
        get_row_value(row, "canonical_validation_state"),
        get_row_value(row, "human_review_required"),
        get_row_value(row, "review_queue"),
        get_row_value(row, "review_reason"),
        normalize_json_array_text(row.get("collections_json")),
        normalize_json_array_text(row.get("tags_json")),
        normalize_json_array_text(row.get("relations_json")),
        normalize_json_array_text(row.get("content_flags_json")),
        get_row_value(row, "audience_suitability"),
        get_row_value(row, "export_to_uckk"),
        get_row_value(row, "export_to_public"),
        get_row_value(row, "export_policy_note"),
        get_row_value(row, "import_batch"),
        get_row_value(row, "notes"),
        get_row_value(row, "created_at"),
        get_row_value(row, "updated_at"),
    ]


def autosize_columns(worksheet):
    for column_cells in worksheet.columns:
        max_len = 0
        column_letter = column_cells[0].column_letter

        for cell in column_cells:
            value = cell.value
            if value is None:
                continue

            max_len = max(max_len, len(str(value)))

        worksheet.column_dimensions[column_letter].width = min(max(max_len + 2, 10), 60)


def create_workbook(output_path: Path, rows: list[dict], filters: dict):
    try:
        from openpyxl import Workbook
    except Exception as exc:
        raise RuntimeError(
            "Python package openpyxl is required. Install it in the active Python environment."
        ) from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()

    library = workbook.active
    library.title = "Library"
    library.append(LIBRARY_HEADERS)

    for row in rows:
        library.append(library_row_to_xlsx_row(row))

    library.freeze_panes = "A2"
    autosize_columns(library)

    lists = workbook.create_sheet("Lists")
    lists.append(["field", "allowed_value"])

    for field, allowed_value in LISTS_ROWS:
        lists.append([field, allowed_value])

    lists.freeze_panes = "A2"
    autosize_columns(lists)

    report = workbook.create_sheet("Import_Report")
    report.append(["row_number", "version_uuid", "action", "result", "message", "changed_fields"])

    report.append([
        1,
        "",
        "export",
        "created",
        f"Exported {len(rows)} library row(s).",
        "",
    ])

    for index, row in enumerate(rows, start=2):
        report.append([
            index,
            row.get("version_uuid") or "",
            "export",
            "ready",
            "Row exported for XLSX review.",
            "",
        ])

    report.append([
        len(rows) + 2,
        "",
        "filter",
        "applied",
        json.dumps(filters, ensure_ascii=False, sort_keys=True),
        "",
    ])

    report.freeze_panes = "A2"
    autosize_columns(report)

    workbook.save(str(output_path))


def main() -> None:
    db_path = Path(sys.argv[1]).expanduser()
    output_path = Path(sys.argv[2]).expanduser()
    filter_json = sys.argv[3] if len(sys.argv) > 3 else ""

    warnings = []

    if output_path.suffix.lower() != ".xlsx":
        if output_path.suffix:
            output_path = output_path.with_suffix(output_path.suffix + ".xlsx")
        else:
            output_path = output_path.with_suffix(".xlsx")

        warnings.append(
            message(
                "WARN_FIELD_NORMALIZED",
                "warning",
                "OutputPath did not end with .xlsx; extension was appended.",
                "OutputPath",
                details={"output_path": str(output_path)},
            )
        )

    try:
        filters = parse_filter_json(filter_json)
    except Exception as exc:
        emit(
            result(
                success=False,
                result_text="invalid_filter_json",
                path=str(output_path),
                errors=[
                    message(
                        "ERR_JSON_PARSE",
                        "blocking",
                        f"FilterJson is invalid JSON: {exc}",
                        "FilterJson",
                    )
                ],
            ),
            1,
        )

    if not db_path.exists() or not db_path.is_file():
        emit(
            result(
                success=False,
                result_text="db_not_found",
                path=str(output_path),
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

    export_uuid = str(uuid4())
    created_at = now_iso()

    try:
        rows = fetch_library_rows(db_path, filters)
        create_workbook(output_path, rows, filters)

        try:
            insert_audit_log(db_path, export_uuid, output_path, len(rows), filters)
        except Exception:
            pass

        file_size = output_path.stat().st_size if output_path.exists() else 0

        emit(
            result(
                success=True,
                result_text="exported",
                path=str(output_path),
                entity_uuid=export_uuid,
                data={
                    "app_public_name": "Médiathèque kOA",
                    "app_component": "koa_mediatheque",
                    "export_uuid": export_uuid,
                    "export_type": "xlsx_inventory",
                    "db_path": str(db_path),
                    "output_path": str(output_path),
                    "row_count": len(rows),
                    "sheet_names": ["Library", "Lists", "Import_Report"],
                    "filters": filters,
                    "filesize": file_size,
                    "created_at": created_at,
                },
                warnings=warnings,
                errors=[],
            ),
            0,
        )
    except Exception as exc:
        emit(
            result(
                success=False,
                result_text="failed",
                path=str(output_path),
                errors=[
                    message(
                        "ERR_XLSX_EXPORT_FAILED",
                        "blocking",
                        str(exc),
                        "Export-KoaLibraryXlsx",
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
        $allArgs += $FilterJsonText

        $stdout = & $pythonExe @allArgs 2>$stderrPath
        $exitCode = $LASTEXITCODE

        $raw = ($stdout | Out-String)
        if ($null -eq $raw) {
            $raw = ""
        }

        $raw = $raw.Trim()

        $stderr = ""
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
                        -Code "ERR_XLSX_EXPORT_FAILED" `
                        -Severity "blocking" `
                        -Message "Python helper produced no JSON output." `
                        -Field "python" `
                        -Details @{
                            exit_code = $exitCode
                            stderr    = $stderr
                        }
                )

            Write-KoaLocalJsonResult -Result $fallback
            exit 1
        }

        Write-Output $raw
        exit $exitCode
    }
    finally {
        if (Test-Path -LiteralPath $tempDir) {
            Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

try {
    Invoke-KoaPythonExport `
        -DatabasePath $DbPath `
        -WorkbookPath $OutputPath `
        -FilterJsonText $FilterJson
}
catch {
    $errorResult = New-KoaLocalResult `
        -Success $false `
        -Result "failed" `
        -Path $OutputPath `
        -Errors @(
            New-KoaLocalMessage `
                -Code "ERR_XLSX_EXPORT_FAILED" `
                -Severity "blocking" `
                -Message $_.Exception.Message `
                -Field "Export-KoaLibraryXlsx"
        )

    Write-KoaLocalJsonResult -Result $errorResult
    exit 1
}