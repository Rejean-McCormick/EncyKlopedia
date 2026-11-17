# 05_TOOLS/Export-KoaManifest.ps1
# Médiathèque kOA — Export canonical manifest.json from SQLite library_rows
# PowerShell 7 only. Emits exactly one JSON result to stdout.

#requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $DbPath,

    [Parameter(Mandatory)]
    [string] $OutputDir,

    [Parameter(Mandatory)]
    [string] $ExportType,

    [string] $FilterJson = "",

    [string] $Actor = "local_user",

    [string] $Reason = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Operation = "Export-KoaManifest"

$AllowedExportTypes = @(
    "xlsx_inventory",
    "koa_manifest",
    "uckkarchive_candidate",
    "public_review_package",
    "backup_snapshot"
)

function New-KoaLocalUuid {
    return [guid]::NewGuid().ToString()
}

function Get-KoaLocalTimestamp {
    return [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
}

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

        [string] $EntityType = "manifest_export",

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

function Get-KoaLocalPythonCommand {
    $repoRoot = Resolve-KoaRepoRoot
    $candidatePaths = @()

    if (-not [string]::IsNullOrWhiteSpace($env:KOA_TEST_PYTHON)) {
        $candidatePaths += $env:KOA_TEST_PYTHON
    }

    if (-not [string]::IsNullOrWhiteSpace($env:PYTHON)) {
        $candidatePaths += $env:PYTHON
    }

    if (-not [string]::IsNullOrWhiteSpace($repoRoot)) {
        $candidatePaths += Join-Path $repoRoot ".venv/Scripts/python.exe"
        $candidatePaths += Join-Path $repoRoot ".venv/bin/python"
    }

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
                Exe  = $resolved.Source
                Args = @()
            }
        }
    }

    foreach ($candidate in @("python", "python3")) {
        $resolved = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($resolved) {
            return [pscustomobject]@{
                Exe  = $resolved.Source
                Args = @()
            }
        }
    }

    $py = Get-Command "py" -ErrorAction SilentlyContinue
    if ($py) {
        return [pscustomobject]@{
            Exe  = $py.Source
            Args = @("-3")
        }
    }

    throw "Python was not found. Export-KoaManifest.ps1 requires Python sqlite3 support."
}

function Resolve-KoaRepoRoot {
    $current = $PSScriptRoot

    while (-not [string]::IsNullOrWhiteSpace($current)) {
        if (
            (Test-Path -LiteralPath (Join-Path $current "pyproject.toml") -PathType Leaf) -and
            (Test-Path -LiteralPath (Join-Path $current "05_TOOLS") -PathType Container)
        ) {
            return $current
        }

        $parent = Split-Path -Parent $current

        if ($parent -eq $current) {
            break
        }

        $current = $parent
    }

    return ""
}

function Invoke-KoaLocalPythonJson {
    param(
        [Parameter(Mandatory)]
        [string] $Code,

        [string[]] $Arguments = @()
    )

    $pythonCommand = Get-KoaLocalPythonCommand
    $pythonExe = [string] $pythonCommand.Exe
    $pythonArgs = @($pythonCommand.Args)

    if ([string]::IsNullOrWhiteSpace($pythonExe)) {
        throw "Python executable path resolved to an empty string."
    }

    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "koa_manifest_helpers"
    New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

    $tempScript = Join-Path $tempRoot ("manifest_helper_" + [guid]::NewGuid().ToString("N") + ".py")
    $stderrPath = Join-Path $tempRoot ("manifest_helper_stderr_" + [guid]::NewGuid().ToString("N") + ".txt")

    try {
        Set-Content -LiteralPath $tempScript -Value $Code -Encoding UTF8

        $allArgs = @()
        $allArgs += $pythonArgs
        $allArgs += $tempScript
        $allArgs += $Arguments

        $stdout = & $pythonExe @allArgs 2>$stderrPath
        $exitCode = $LASTEXITCODE
        $raw = ($stdout | Out-String).Trim()

        $stderr = ""
        if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
            $stderrContent = Get-Content -LiteralPath $stderrPath -Raw -ErrorAction SilentlyContinue
            if ($null -ne $stderrContent) {
                $stderr = $stderrContent.Trim()
            }
        }

        if ($exitCode -ne 0) {
            throw "Python helper failed with exit code $exitCode. Stderr: $stderr Stdout: $raw"
        }

        if ([string]::IsNullOrWhiteSpace($raw)) {
            return $null
        }

        return $raw | ConvertFrom-Json -Depth 100 -ErrorAction Stop
    }
    finally {
        if (Test-Path -LiteralPath $tempScript -PathType Leaf) {
            Remove-Item -LiteralPath $tempScript -Force -ErrorAction SilentlyContinue
        }

        if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
            Remove-Item -LiteralPath $stderrPath -Force -ErrorAction SilentlyContinue
        }
    }
}

function ConvertTo-KoaLocalHashtable {
    param(
        [AllowNull()]
        [object] $Value
    )

    if ($null -eq $Value) {
        return @{}
    }

    if ($Value -is [hashtable]) {
        return $Value
    }

    if ($Value -is [System.Collections.Specialized.OrderedDictionary]) {
        $hash = @{}
        foreach ($key in $Value.Keys) {
            $hash[$key] = $Value[$key]
        }
        return $hash
    }

    $result = @{}
    foreach ($property in $Value.PSObject.Properties) {
        $result[$property.Name] = $property.Value
    }

    return $result
}

function ConvertFrom-KoaLocalFilterJson {
    param(
        [AllowNull()]
        [string] $JsonText
    )

    if ([string]::IsNullOrWhiteSpace($JsonText)) {
        return @{}
    }

    try {
        $value = $JsonText | ConvertFrom-Json -Depth 100 -ErrorAction Stop
        return ConvertTo-KoaLocalHashtable -Value $value
    }
    catch {
        throw "FilterJson is not valid JSON: $($_.Exception.Message)"
    }
}

function ConvertTo-KoaLocalJsonArray {
    param(
        [AllowNull()]
        [object] $Value
    )

    if ($null -eq $Value) {
        return @()
    }

    if ($Value -is [System.Array]) {
        $items = @()

        foreach ($item in @($Value)) {
            if ($null -eq $item) {
                continue
            }

            if ($item -is [string] -and [string]::IsNullOrWhiteSpace($item)) {
                continue
            }

            $items += $item
        }

        return @($items)
    }

    if ($Value -is [string]) {
        $text = $Value.Trim()

        if ([string]::IsNullOrWhiteSpace($text)) {
            return @()
        }

        if ($text -eq "[]") {
            return @()
        }

        try {
            $parsed = $text | ConvertFrom-Json -Depth 100 -ErrorAction Stop

            if ($null -eq $parsed) {
                return @()
            }

            if ($parsed -is [System.Array]) {
                return @($parsed)
            }

            return @($parsed)
        }
        catch {
            return @($text)
        }
    }

    if ($Value -is [System.Management.Automation.PSCustomObject]) {
        $propertyNames = @($Value.PSObject.Properties.Name)

        if ($propertyNames.Count -eq 0) {
            return @()
        }

        return @($Value)
    }

    return @($Value)
}

function ConvertFrom-KoaManifestJsonArrayText {
    param(
        [AllowNull()]
        [object] $JsonText,

        [AllowNull()]
        [object] $FallbackValue = $null
    )

    if ($null -ne $JsonText) {
        $text = ([string] $JsonText).Trim()

        if ([string]::IsNullOrWhiteSpace($text)) {
            return @()
        }

        if ($text -eq "[]") {
            return @()
        }

        try {
            $parsed = $text | ConvertFrom-Json -Depth 100 -ErrorAction Stop

            if ($null -eq $parsed) {
                return @()
            }

            if ($parsed -is [System.Array]) {
                return @($parsed)
            }

            return @($parsed)
        }
        catch {
            if ($text -match "^\s*\[") {
                return @()
            }

            return @($text)
        }
    }

    return ConvertTo-KoaLocalJsonArray -Value $FallbackValue
}

function Get-KoaLocalSha256 {
    param(
        [Parameter(Mandatory)]
        [string] $FilePath
    )

    return (Get-FileHash -LiteralPath $FilePath -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-KoaManifestRows {
    param(
        [Parameter(Mandatory)]
        [string] $DatabasePath,

        [Parameter(Mandatory)]
        [string] $RequestedExportType,

        [Parameter(Mandatory)]
        [string] $FilterJsonText
    )

    $code = @'
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

db_path = Path(sys.argv[1])
export_type = sys.argv[2]
filter_json = sys.argv[3] or "{}"

try:
    filters = json.loads(filter_json)
    if filters is None:
        filters = {}
    if not isinstance(filters, dict):
        raise ValueError("FilterJson must be a JSON object.")
except Exception as exc:
    print(json.dumps({
        "ok": False,
        "code": "ERR_INVALID_FILTER_JSON",
        "message": str(exc),
        "rows": [],
        "schema_meta": {},
    }, ensure_ascii=False))
    sys.exit(0)

if not db_path.exists():
    print(json.dumps({
        "ok": False,
        "code": "ERR_DB_NOT_FOUND",
        "message": f"SQLite database not found: {db_path}",
        "rows": [],
        "schema_meta": {},
    }, ensure_ascii=False))
    sys.exit(0)

ARRAY_FIELDS = {
    "collections_json": "collections",
    "tags_json": "tags",
    "relations_json": "relations",
    "content_flags_json": "content_flags",
}

def parse_array(value):
    if value is None:
        return []

    if isinstance(value, list):
        return value

    text = str(value).strip()
    if not text:
        return []

    try:
        parsed = json.loads(text)
        if parsed is None:
            return []
        if isinstance(parsed, list):
            return parsed
        return [parsed]
    except Exception:
        return [part.strip() for part in text.split(";") if part.strip()]

def row_to_manifest(row):
    data = dict(row)

    for source, target in ARRAY_FIELDS.items():
        data[target] = parse_array(data.get(source))

    data["is_uckk_candidate"] = (
        str(data.get("export_to_uckk") or "").lower() == "yes"
        or str(data.get("target_system") or "") == "uckkarchive"
        or str(data.get("uckk_relevance") or "") not in {"", "unknown", "not_uckk"}
    )

    data["is_public_candidate"] = (
        str(data.get("export_to_public") or "").lower() == "yes"
        or str(data.get("public_state") or "") == "public"
        or str(data.get("visibility") or "") == "public"
    )

    data["requires_human_review"] = int(data.get("human_review_required") or 0) == 1

    return data

def export_type_where(export_type):
    if export_type == "uckkarchive_candidate":
        return """
        WHERE COALESCE(status, 'active') != 'deleted_soft'
          AND (
                export_to_uckk = 'yes'
             OR target_system = 'uckkarchive'
             OR (
                    uckk_relevance IS NOT NULL
                AND uckk_relevance NOT IN ('', 'unknown', 'not_uckk')
                )
          )
        """

    if export_type == "public_review_package":
        return """
        WHERE COALESCE(status, 'active') != 'deleted_soft'
          AND (
                export_to_public = 'yes'
             OR public_state = 'public'
             OR visibility = 'public'
             OR human_review_required = 1
          )
        """

    return "WHERE COALESCE(status, 'active') != 'deleted_soft'"

def safe_filter_columns(connection):
    rows = connection.execute("PRAGMA table_info(library_rows)").fetchall()
    return {row[1] for row in rows}

connection = sqlite3.connect(str(db_path))
connection.row_factory = sqlite3.Row

try:
    table = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='library_rows' LIMIT 1"
    ).fetchone()

    if table is None:
        print(json.dumps({
            "ok": False,
            "code": "ERR_DB_SCHEMA",
            "message": "SQLite database does not contain library_rows.",
            "rows": [],
            "schema_meta": {},
        }, ensure_ascii=False))
        sys.exit(0)

    where_sql = export_type_where(export_type)
    params = []
    allowed = safe_filter_columns(connection)

    for key, value in filters.items():
        if key not in allowed:
            continue

        if value is None or value == "":
            continue

        if isinstance(value, list):
            values = [item for item in value if item is not None and str(item).strip() != ""]
            if not values:
                continue
            placeholders = ", ".join("?" for _ in values)
            where_sql += f" AND {key} IN ({placeholders})"
            params.extend(values)
        else:
            where_sql += f" AND {key} = ?"
            params.append(value)

    query = f"""
    SELECT *
    FROM library_rows
    {where_sql}
    ORDER BY updated_at DESC, id ASC
    """

    rows = [
        row_to_manifest(row)
        for row in connection.execute(query, params).fetchall()
    ]

    schema_meta = {}
    if connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_meta' LIMIT 1"
    ).fetchone():
        for row in connection.execute("SELECT key, value FROM schema_meta").fetchall():
            schema_meta[str(row["key"])] = row["value"]

    print(json.dumps({
        "ok": True,
        "code": "",
        "message": "",
        "rows": rows,
        "schema_meta": schema_meta,
    }, ensure_ascii=False, sort_keys=True, default=str))
finally:
    connection.close()
'@

    return Invoke-KoaLocalPythonJson `
        -Code $code `
        -Arguments @($DatabasePath, $RequestedExportType, $FilterJsonText)
}

function Write-KoaManifestAuditLog {
    param(
        [Parameter(Mandatory)]
        [string] $DatabasePath,

        [Parameter(Mandatory)]
        [string] $ExportUuid,

        [Parameter(Mandatory)]
        [string] $RequestedExportType,

        [Parameter(Mandatory)]
        [string] $ManifestPath,

        [Parameter(Mandatory)]
        [int] $RowCount,

        [Parameter(Mandatory)]
        [string] $ActorValue,

        [Parameter(Mandatory)]
        [string] $ReasonValue,

        [Parameter(Mandatory)]
        [string] $FilterJsonText
    )

    $code = @'
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

db_path = Path(sys.argv[1])
export_uuid = sys.argv[2]
export_type = sys.argv[3]
manifest_path = sys.argv[4]
row_count = int(sys.argv[5])
actor = sys.argv[6]
reason = sys.argv[7]
filter_json = sys.argv[8]

def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

if not db_path.exists():
    print(json.dumps({"ok": True, "audit_written": False}, ensure_ascii=False))
    sys.exit(0)

connection = sqlite3.connect(str(db_path))

try:
    table = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='audit_log' LIMIT 1"
    ).fetchone()

    if table is None:
        print(json.dumps({"ok": True, "audit_written": False}, ensure_ascii=False))
        sys.exit(0)

    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(audit_log)").fetchall()
    }

    payload = {
        "action": "manifest_exported",
        "entity_type": "manifest_export",
        "entity_uuid": export_uuid,
        "before_json": "{}",
        "after_json": json.dumps({
            "export_uuid": export_uuid,
            "export_type": export_type,
            "manifest_path": manifest_path,
            "row_count": row_count,
            "reason": reason,
            "filters": json.loads(filter_json or "{}"),
        }, ensure_ascii=False, sort_keys=True),
        "actor": actor,
        "note": f"Export-KoaManifest.ps1 ExportType={export_type} Reason={reason}",
        "created_at": now_iso(),
    }

    filtered = {
        key: value
        for key, value in payload.items()
        if key in columns
    }

    if filtered:
        column_sql = ", ".join(filtered.keys())
        placeholders = ", ".join("?" for _ in filtered)
        connection.execute(
            f"INSERT INTO audit_log ({column_sql}) VALUES ({placeholders})",
            list(filtered.values()),
        )
        connection.commit()

    print(json.dumps({"ok": True, "audit_written": bool(filtered)}, ensure_ascii=False))
finally:
    connection.close()
'@

    try {
        Invoke-KoaLocalPythonJson `
            -Code $code `
            -Arguments @(
                $DatabasePath,
                $ExportUuid,
                $RequestedExportType,
                $ManifestPath,
                ([string] $RowCount),
                $ActorValue,
                $ReasonValue,
                $FilterJsonText
            ) | Out-Null
    }
    catch {
        # Audit failure must not break manifest export.
    }
}

function New-KoaManifestPolicyIssues {
    param(
        [Parameter(Mandatory)]
        [object] $Row,

        [Parameter(Mandatory)]
        [string] $RequestedExportType
    )

    $issues = @()

    if ($RequestedExportType -eq "uckkarchive_candidate") {
        if ([string] $Row.target_system -ne "uckkarchive") {
            $issues += [ordered]@{
                code     = "WARN_TARGET_SYSTEM_NOT_UCKKARCHIVE"
                severity = "warning"
                field    = "target_system"
                message  = "Row is included as a UCKK candidate but target_system is not uckkarchive."
            }
        }

        if ([int] ($Row.target_export_allowed ?? 0) -ne 1) {
            $issues += [ordered]@{
                code     = "WARN_TARGET_EXPORT_NOT_ALLOWED"
                severity = "warning"
                field    = "target_export_allowed"
                message  = "Row is included as a UCKK candidate but target_export_allowed is not 1."
            }
        }
    }

    if ($RequestedExportType -eq "public_review_package") {
        if ([string] $Row.visibility -ne "public" -and [string] $Row.public_state -ne "public") {
            $issues += [ordered]@{
                code     = "WARN_NOT_PUBLIC"
                severity = "warning"
                field    = "visibility"
                message  = "Row is included in public review but is not currently public."
            }
        }
    }

    if ([int] ($Row.human_review_required ?? 0) -eq 1) {
        $issues += [ordered]@{
            code     = "INFO_HUMAN_REVIEW_REQUIRED"
            severity = "info"
            field    = "human_review_required"
            message  = "Row requires human review."
        }
    }

    return @($issues)
}

function ConvertTo-KoaManifestRows {
    param(
        [Parameter(Mandatory)]
        [object[]] $Rows,

        [Parameter(Mandatory)]
        [string] $RequestedExportType
    )

    $manifestRows = @()

    foreach ($row in @($Rows)) {
        $manifestRows += [ordered]@{
            id                         = $row.id
            media_uuid                 = $row.media_uuid
            version_uuid               = $row.version_uuid
            title                      = $row.title
            subtitle                   = $row.subtitle
            description                = $row.description
            summary                    = $row.summary

            original_path              = $row.original_path
            storage_path               = $row.storage_path
            filename                   = $row.filename
            extension                  = $row.extension
            mimetype                   = $row.mimetype
            filesize                   = $row.filesize
            sha256                     = $row.sha256
            filearea                   = $row.filearea

            media_type                 = $row.media_type
            language                   = $row.language
            library_scope              = $row.library_scope

            uckk_relevance             = $row.uckk_relevance
            target_system              = $row.target_system
            target_export_allowed      = $row.target_export_allowed
            export_to_uckk             = $row.export_to_uckk
            export_to_public           = $row.export_to_public
            export_policy_note         = $row.export_policy_note

            public_state               = $row.public_state
            visibility                 = $row.visibility
            access_level               = $row.access_level
            ownership_scope            = $row.ownership_scope
            source_type                = $row.source_type
            source_ownership           = $row.source_ownership
            rights_status              = $row.rights_status
            rights_note                = $row.rights_note
            restriction_state          = $row.restriction_state
            restriction_reason         = $row.restriction_reason
            redaction_required         = $row.redaction_required

            status                     = $row.status
            provenance                 = $row.provenance
            ai_validation_state        = $row.ai_validation_state
            ai_confidence              = $row.ai_confidence
            canonical_validation_state = $row.canonical_validation_state
            human_review_required      = $row.human_review_required
            review_queue               = $row.review_queue
            review_reason              = $row.review_reason
            audience_suitability       = $row.audience_suitability

            collections                = @(ConvertFrom-KoaManifestJsonArrayText -JsonText $row.collections_json -FallbackValue $row.collections)
            tags                       = @(ConvertFrom-KoaManifestJsonArrayText -JsonText $row.tags_json -FallbackValue $row.tags)
            relations                  = @(ConvertFrom-KoaManifestJsonArrayText -JsonText $row.relations_json -FallbackValue $row.relations)
            content_flags              = @(ConvertFrom-KoaManifestJsonArrayText -JsonText $row.content_flags_json -FallbackValue $row.content_flags)

            collections_json           = $row.collections_json
            tags_json                  = $row.tags_json
            relations_json             = $row.relations_json
            content_flags_json         = $row.content_flags_json

            import_batch               = $row.import_batch
            notes                      = $row.notes
            created_at                 = $row.created_at
            updated_at                 = $row.updated_at

            is_uckk_candidate          = $row.is_uckk_candidate
            is_public_candidate        = $row.is_public_candidate
            requires_human_review      = $row.requires_human_review
            policy_issues              = New-KoaManifestPolicyIssues -Row $row -RequestedExportType $RequestedExportType
        }
    }

    return @($manifestRows)
}

function New-KoaManifestDocument {
    param(
        [Parameter(Mandatory)]
        [object[]] $Rows,

        [Parameter(Mandatory)]
        [string] $ExportUuid,

        [Parameter(Mandatory)]
        [string] $RequestedExportType,

        [Parameter(Mandatory)]
        [string] $ActorValue,

        [Parameter(Mandatory)]
        [string] $ReasonValue,

        [Parameter(Mandatory)]
        [hashtable] $Filters,

        [Parameter(Mandatory)]
        [hashtable] $SchemaMeta
    )

    $timestamp = Get-KoaLocalTimestamp
    $manifestRows = ConvertTo-KoaManifestRows -Rows $Rows -RequestedExportType $RequestedExportType

    return [ordered]@{
        app_name         = "Médiathèque kOA"
        app_public_name  = "Médiathèque kOA"
        app_component    = "koa_mediatheque"
        schema_meta      = $SchemaMeta

        export_uuid      = $ExportUuid
        export_timestamp = $timestamp
        export_actor     = $ActorValue
        export_reason    = $ReasonValue
        export_type      = $RequestedExportType
        filters          = $Filters

        row_count        = @($manifestRows).Count
        summary          = [ordered]@{
            total_rows            = @($manifestRows).Count
            export_type           = $RequestedExportType
            uckk_candidates       = @($manifestRows | Where-Object { $_.is_uckk_candidate }).Count
            public_candidates     = @($manifestRows | Where-Object { $_.is_public_candidate }).Count
            human_review_required = @($manifestRows | Where-Object { $_.requires_human_review }).Count
        }

        rows             = @($manifestRows)
    }
}

try {
    if ($AllowedExportTypes -notcontains $ExportType) {
        $result = New-KoaLocalResult `
            -Success $false `
            -Result "invalid_export_type" `
            -EntityType "manifest_export" `
            -Path $OutputDir `
            -Errors @(
                New-KoaLocalMessage `
                    -Code "ERR_INVALID_EXPORT_TYPE" `
                    -Severity "blocking" `
                    -Message "Invalid ExportType: $ExportType" `
                    -Field "ExportType" `
                    -Details @{ allowed_values = $AllowedExportTypes }
            )

        Write-KoaLocalJsonResult -Result $result
        exit 1
    }

    if (-not (Test-Path -LiteralPath $DbPath -PathType Leaf)) {
        $result = New-KoaLocalResult `
            -Success $false `
            -Result "db_not_found" `
            -EntityType "manifest_export" `
            -Path $OutputDir `
            -Errors @(
                New-KoaLocalMessage `
                    -Code "ERR_DB_NOT_FOUND" `
                    -Severity "blocking" `
                    -Message "SQLite database not found: $DbPath" `
                    -Field "DbPath"
            )

        Write-KoaLocalJsonResult -Result $result
        exit 1
    }

    $filters = ConvertFrom-KoaLocalFilterJson -JsonText $FilterJson
    $normalizedFilterJson = $filters | ConvertTo-Json -Depth 100 -Compress

    $outputDirItem = New-Item -ItemType Directory -Force -Path $OutputDir
    $manifestPath = Join-Path $outputDirItem.FullName "manifest.json"

    $queryResult = Get-KoaManifestRows `
        -DatabasePath $DbPath `
        -RequestedExportType $ExportType `
        -FilterJsonText $normalizedFilterJson

    if ($null -eq $queryResult -or -not [bool] $queryResult.ok) {
        $code = "ERR_MANIFEST_QUERY_FAILED"
        $message = "Manifest query failed."

        if ($null -ne $queryResult) {
            if (-not [string]::IsNullOrWhiteSpace([string] $queryResult.code)) {
                $code = [string] $queryResult.code
            }

            if (-not [string]::IsNullOrWhiteSpace([string] $queryResult.message)) {
                $message = [string] $queryResult.message
            }
        }

        $result = New-KoaLocalResult `
            -Success $false `
            -Result "failed" `
            -EntityType "manifest_export" `
            -Path $OutputDir `
            -Errors @(
                New-KoaLocalMessage `
                    -Code $code `
                    -Severity "blocking" `
                    -Message $message
            )

        Write-KoaLocalJsonResult -Result $result
        exit 1
    }

    $rows = @($queryResult.rows)
    $schemaMeta = ConvertTo-KoaLocalHashtable -Value $queryResult.schema_meta
    $warnings = @()

    if (@($rows).Count -eq 0) {
        $warnings += New-KoaLocalMessage `
            -Code "WARN_EMPTY_EXPORT" `
            -Severity "warning" `
            -Message "No rows matched the manifest export filters." `
            -Details @{
                export_type = $ExportType
                filters     = $filters
            }
    }

    $exportUuid = New-KoaLocalUuid

    $manifest = New-KoaManifestDocument `
        -Rows $rows `
        -ExportUuid $exportUuid `
        -RequestedExportType $ExportType `
        -ActorValue $Actor `
        -ReasonValue $Reason `
        -Filters $filters `
        -SchemaMeta $schemaMeta

    $manifestJson = $manifest | ConvertTo-Json -Depth 100 -Compress:$false
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($manifestPath, $manifestJson, $utf8NoBom)

    $manifestItem = Get-Item -LiteralPath $manifestPath
    $manifestSha256 = Get-KoaLocalSha256 -FilePath $manifestItem.FullName

    Write-KoaManifestAuditLog `
        -DatabasePath $DbPath `
        -ExportUuid $exportUuid `
        -RequestedExportType $ExportType `
        -ManifestPath $manifestItem.FullName `
        -RowCount @($rows).Count `
        -ActorValue $Actor `
        -ReasonValue $Reason `
        -FilterJsonText $normalizedFilterJson

    $result = New-KoaLocalResult `
        -Success $true `
        -Result "exported" `
        -EntityType "manifest_export" `
        -EntityUuid $exportUuid `
        -Path $manifestItem.FullName `
        -Data @{
            app_name        = "Médiathèque kOA"
            app_component   = "koa_mediatheque"
            export_uuid     = $exportUuid
            export_type     = $ExportType
            db_path         = $DbPath
            output_dir      = $outputDirItem.FullName
            manifest_path   = $manifestItem.FullName
            manifest_name   = "manifest.json"
            manifest_sha256 = $manifestSha256
            filesize        = $manifestItem.Length
            row_count       = @($rows).Count
            actor           = $Actor
            reason          = $Reason
            filters         = $filters
            summary         = $manifest.summary
            created_at      = $manifest.export_timestamp
        } `
        -Warnings $warnings `
        -Errors @()

    Write-KoaLocalJsonResult -Result $result
    exit 0
}
catch {
    $errorResult = New-KoaLocalResult `
        -Success $false `
        -Result "failed" `
        -EntityType "manifest_export" `
        -Path $OutputDir `
        -Errors @(
            New-KoaLocalMessage `
                -Code "ERR_MANIFEST_EXPORT_FAILED" `
                -Severity "blocking" `
                -Message $_.Exception.Message
        )

    Write-KoaLocalJsonResult -Result $errorResult
    exit 1
}