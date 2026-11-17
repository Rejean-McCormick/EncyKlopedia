# 05_TOOLS/Initialize-KoaMediathequeDb.ps1
# Médiathèque kOA — Initialize SQLite database
# PowerShell 7 only. Emits exactly one JSON result to stdout.

#requires -Version 7.0

[CmdletBinding()]
param(
    [string] $DbPath = "",

    [string] $SchemaDir = "",

    [switch] $Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Operation = "Initialize-KoaMediathequeDb"

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
        entity_type  = "database"
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

    return (Split-Path -Parent $StartingPath)
}

function Get-KoaPythonCommand {
    foreach ($candidate in @("python", "py", "python3")) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue

        if ($command) {
            try {
                $null = & $command.Source --version 2>&1

                if ($LASTEXITCODE -eq 0) {
                    return [string] $command.Source
                }
            }
            catch {
                continue
            }
        }
    }

    throw "Python was not found in PATH. Python is required because this script uses Python's built-in sqlite3 module instead of sqlite3.exe."
}

function Get-KoaSchemaFiles {
    param(
        [Parameter(Mandatory)]
        [string] $SchemaDirectory
    )

    if ([string]::IsNullOrWhiteSpace($SchemaDirectory)) {
        return @()
    }

    if (-not (Test-Path -LiteralPath $SchemaDirectory -PathType Container)) {
        return @()
    }

    return @(
        Get-ChildItem -LiteralPath $SchemaDirectory -Filter "*.sql" -File |
            Sort-Object Name
    )
}

function Invoke-KoaPythonSql {
    param(
        [Parameter(Mandatory)]
        [string] $PythonExe,

        [Parameter(Mandatory)]
        [string] $DatabasePath,

        [Parameter(Mandatory)]
        [string] $SqlText,

        [Parameter(Mandatory)]
        [string] $SourceName
    )

    if ([string]::IsNullOrWhiteSpace($SqlText)) {
        throw "SQL source is empty: $SourceName"
    }

    $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("koa_sql_" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

    $scriptPath = Join-Path $tempDir "apply_sql.py"
    $sqlPath = Join-Path $tempDir "schema.sql"

    Set-Content -LiteralPath $sqlPath -Value $SqlText -Encoding UTF8

    $pythonCode = @'
from __future__ import annotations

import pathlib
import sqlite3
import sys

db_path = pathlib.Path(sys.argv[1])
sql_path = pathlib.Path(sys.argv[2])

db_path.parent.mkdir(parents=True, exist_ok=True)
sql_text = sql_path.read_text(encoding="utf-8-sig")

connection = sqlite3.connect(str(db_path))
try:
    connection.executescript(sql_text)
    connection.commit()
finally:
    connection.close()
'@

    Set-Content -LiteralPath $scriptPath -Value $pythonCode -Encoding UTF8

    try {
        $output = & $PythonExe $scriptPath $DatabasePath $sqlPath 2>&1

        if ($LASTEXITCODE -ne 0) {
            throw "Python sqlite apply failed for $SourceName. Output: $($output | Out-String)"
        }
    }
    finally {
        Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Get-KoaDbFacts {
    param(
        [Parameter(Mandatory)]
        [string] $PythonExe,

        [Parameter(Mandatory)]
        [string] $DatabasePath
    )

    $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("koa_facts_" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

    $scriptPath = Join-Path $tempDir "db_facts.py"

    $pythonCode = @'
from __future__ import annotations

import json
import sqlite3
import sys

db_path = sys.argv[1]

connection = sqlite3.connect(db_path)
try:
    tables = [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()
    ]

    try:
        row_count = connection.execute("SELECT COUNT(*) FROM library_rows").fetchone()[0]
    except sqlite3.Error:
        row_count = 0

    try:
        schema_version_row = connection.execute(
            "SELECT value FROM schema_meta WHERE key = 'schema_version' LIMIT 1"
        ).fetchone()
        schema_version = schema_version_row[0] if schema_version_row else ""
    except sqlite3.Error:
        schema_version = ""

    print(
        json.dumps(
            {
                "tables": tables,
                "row_count": row_count,
                "schema_version": schema_version,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
finally:
    connection.close()
'@

    Set-Content -LiteralPath $scriptPath -Value $pythonCode -Encoding UTF8

    try {
        $output = & $PythonExe $scriptPath $DatabasePath 2>&1

        if ($LASTEXITCODE -ne 0) {
            throw "Python sqlite fact query failed. Output: $($output | Out-String)"
        }

        $jsonText = ($output | Out-String).Trim()

        if ([string]::IsNullOrWhiteSpace($jsonText)) {
            throw "Python sqlite fact query returned empty output."
        }

        return ($jsonText | ConvertFrom-Json -ErrorAction Stop)
    }
    finally {
        Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Add-KoaAuditRow {
    param(
        [Parameter(Mandatory)]
        [string] $PythonExe,

        [Parameter(Mandatory)]
        [string] $DatabasePath,

        [Parameter(Mandatory)]
        [hashtable] $After
    )

    $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("koa_audit_" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

    $scriptPath = Join-Path $tempDir "audit.py"
    $jsonPath = Join-Path $tempDir "after.json"

    Set-Content `
        -LiteralPath $jsonPath `
        -Value ($After | ConvertTo-Json -Depth 100 -Compress) `
        -Encoding UTF8

    $pythonCode = @'
from __future__ import annotations

import pathlib
import sqlite3
import sys

db_path = sys.argv[1]
after_json = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8-sig")

connection = sqlite3.connect(db_path)
try:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'audit_log' LIMIT 1"
    ).fetchone()

    if row is not None:
        connection.execute(
            """
            INSERT INTO audit_log(
                action,
                entity_type,
                entity_uuid,
                before_json,
                after_json,
                actor,
                note,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                "database_initialized",
                "database",
                None,
                None,
                after_json,
                "local_user",
                "Initialize-KoaMediathequeDb.ps1",
            ),
        )
        connection.commit()
finally:
    connection.close()
'@

    Set-Content -LiteralPath $scriptPath -Value $pythonCode -Encoding UTF8

    try {
        $output = & $PythonExe $scriptPath $DatabasePath $jsonPath 2>&1

        if ($LASTEXITCODE -ne 0) {
            throw "Python sqlite audit insert failed. Output: $($output | Out-String)"
        }
    }
    finally {
        Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Get-KoaEmbeddedInitialSchemaSql {
    return @"
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS library_rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_uuid TEXT NOT NULL,
    version_uuid TEXT NOT NULL UNIQUE,

    title TEXT NOT NULL,
    subtitle TEXT,
    description TEXT,
    summary TEXT,

    original_path TEXT NOT NULL,
    storage_path TEXT,
    filename TEXT NOT NULL,
    extension TEXT,
    mimetype TEXT,
    filesize INTEGER,
    sha256 TEXT,
    filearea TEXT DEFAULT 'media_original',

    media_type TEXT DEFAULT 'document',
    language TEXT DEFAULT 'fr',
    library_scope TEXT DEFAULT 'koa',
    uckk_relevance TEXT DEFAULT 'unknown',
    target_system TEXT DEFAULT 'none',
    target_export_allowed INTEGER DEFAULT 0,

    public_state TEXT DEFAULT 'unknown',
    visibility TEXT DEFAULT 'private',
    access_level TEXT DEFAULT 'private',

    ownership_scope TEXT DEFAULT 'unknown',
    source_type TEXT DEFAULT 'unknown',
    source_ownership TEXT DEFAULT 'unknown_source',
    rights_status TEXT DEFAULT 'unknown',
    rights_note TEXT,

    restriction_state TEXT DEFAULT 'none',
    restriction_reason TEXT,
    redaction_required INTEGER DEFAULT 0,

    status TEXT DEFAULT 'active',
    provenance TEXT DEFAULT 'ai_assisted',
    ai_validation_state TEXT DEFAULT 'ai_uncertain',
    ai_confidence REAL,
    canonical_validation_state TEXT DEFAULT 'unverified',
    human_review_required INTEGER DEFAULT 0,
    review_queue TEXT,
    review_reason TEXT,

    collections_json TEXT DEFAULT '[]',
    tags_json TEXT DEFAULT '[]',
    relations_json TEXT DEFAULT '[]',
    content_flags_json TEXT DEFAULT '[]',
    audience_suitability TEXT DEFAULT 'unknown',

    export_to_uckk TEXT DEFAULT 'no',
    export_to_public TEXT DEFAULT 'no',
    export_policy_note TEXT,

    import_batch TEXT,
    notes TEXT,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chatgpt_intake_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_uuid TEXT,
    file_path TEXT,
    prompt_template TEXT,
    raw_response TEXT,
    parsed_json TEXT,
    validation_status TEXT,
    validation_errors TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS xlsx_import_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_uuid TEXT,
    xlsx_path TEXT,
    action TEXT,
    version_uuid TEXT,
    row_number INTEGER,
    before_json TEXT,
    after_json TEXT,
    validation_status TEXT,
    validation_errors TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS file_scan_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_batch TEXT,
    scan_root TEXT,
    file_path TEXT,
    sha256 TEXT,
    filesize INTEGER,
    mimetype TEXT,
    status TEXT,
    message TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_uuid TEXT,
    before_json TEXT,
    after_json TEXT,
    actor TEXT DEFAULT 'local_user',
    note TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_library_rows_media_uuid ON library_rows(media_uuid);
CREATE INDEX IF NOT EXISTS idx_library_rows_version_uuid ON library_rows(version_uuid);
CREATE INDEX IF NOT EXISTS idx_library_rows_sha256 ON library_rows(sha256);
CREATE INDEX IF NOT EXISTS idx_library_rows_status ON library_rows(status);
CREATE INDEX IF NOT EXISTS idx_library_rows_visibility ON library_rows(visibility);
CREATE INDEX IF NOT EXISTS idx_library_rows_uckk_relevance ON library_rows(uckk_relevance);
CREATE INDEX IF NOT EXISTS idx_library_rows_public_state ON library_rows(public_state);
CREATE INDEX IF NOT EXISTS idx_library_rows_review ON library_rows(human_review_required, review_queue);

CREATE INDEX IF NOT EXISTS idx_chatgpt_intake_log_version_uuid ON chatgpt_intake_log(version_uuid);
CREATE INDEX IF NOT EXISTS idx_xlsx_import_log_import_uuid ON xlsx_import_log(import_uuid);
CREATE INDEX IF NOT EXISTS idx_xlsx_import_log_version_uuid ON xlsx_import_log(version_uuid);
CREATE INDEX IF NOT EXISTS idx_file_scan_log_import_batch ON file_scan_log(import_batch);
CREATE INDEX IF NOT EXISTS idx_file_scan_log_sha256 ON file_scan_log(sha256);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_uuid);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);

CREATE TRIGGER IF NOT EXISTS trg_library_rows_updated_at
AFTER UPDATE ON library_rows
FOR EACH ROW
BEGIN
    UPDATE library_rows
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.id;
END;

INSERT INTO schema_meta(key, value, updated_at)
VALUES
    ('app_public_name', 'Médiathèque kOA', CURRENT_TIMESTAMP),
    ('app_short_name', 'kOA', CURRENT_TIMESTAMP),
    ('app_technical_name', 'koa-mediatheque', CURRENT_TIMESTAMP),
    ('app_component', 'koa_mediatheque', CURRENT_TIMESTAMP),
    ('app_db_filename', 'koa_mediatheque.sqlite', CURRENT_TIMESTAMP),
    ('schema_version', '001', CURRENT_TIMESTAMP),
    ('schema_initialized_at', strftime('%Y-%m-%dT%H:%M:%SZ', 'now'), CURRENT_TIMESTAMP)
ON CONFLICT(key) DO UPDATE SET
    value = excluded.value,
    updated_at = CURRENT_TIMESTAMP;
"@
}

try {
    $warnings = @()
    $appliedSources = @()

    $rootPath = Resolve-KoaRootPath -StartingPath $PSScriptRoot

    $contentRoot = if (-not [string]::IsNullOrWhiteSpace($env:KOA_CONTENT_ROOT)) {
        [System.IO.Path]::GetFullPath($env:KOA_CONTENT_ROOT)
    } else {
        [System.IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $rootPath) "content"))
    }

    if ([string]::IsNullOrWhiteSpace($DbPath)) {
        $DbPath = Join-Path $contentRoot "01_DB/koa_mediatheque.sqlite"
    }

    if ([string]::IsNullOrWhiteSpace($SchemaDir)) {
        $SchemaDir = Join-Path $rootPath "schemas/sqlite"
    }

    $DbPath = [System.IO.Path]::GetFullPath($DbPath)
    $SchemaDir = [System.IO.Path]::GetFullPath($SchemaDir)

    if (-not (Test-Path -LiteralPath $SchemaDir -PathType Container)) {
        $result = New-KoaOperationResult `
            -Success $false `
            -Result "schema_dir_not_found" `
            -Path $DbPath `
            -Errors @(
                New-KoaMessage `
                    -Code "ERR_SCHEMA_DIR_NOT_FOUND" `
                    -Severity "blocking" `
                    -Message "Schema directory not found: $SchemaDir" `
                    -Field "SchemaDir" `
                    -Details @{ schema_dir = $SchemaDir }
            )

        Write-KoaJsonResult -Result $result
        exit 1
    }

    $pythonExe = Get-KoaPythonCommand

    $dbParent = Split-Path -Parent $DbPath

    if (-not [string]::IsNullOrWhiteSpace($dbParent) -and -not (Test-Path -LiteralPath $dbParent -PathType Container)) {
        New-Item -ItemType Directory -Path $dbParent -Force | Out-Null
    }

    if ((Test-Path -LiteralPath $DbPath -PathType Leaf) -and $Force) {
        Remove-Item -LiteralPath $DbPath -Force

        foreach ($sidecar in @("$DbPath-wal", "$DbPath-shm")) {
            if (Test-Path -LiteralPath $sidecar -PathType Leaf) {
                Remove-Item -LiteralPath $sidecar -Force
            }
        }
    }
    elseif ((Test-Path -LiteralPath $DbPath -PathType Leaf) -and -not $Force) {
        $warnings += New-KoaMessage `
            -Code "WARN_DB_ALREADY_EXISTS" `
            -Severity "warning" `
            -Message "Database already exists; initialization will run idempotent schema creation only." `
            -Field "DbPath" `
            -Details @{ db_path = $DbPath }
    }

    $schemaFiles = Get-KoaSchemaFiles -SchemaDirectory $SchemaDir

    if ($schemaFiles.Count -gt 0) {
        foreach ($schemaFile in $schemaFiles) {
            $sqlText = Get-Content -LiteralPath $schemaFile.FullName -Raw -Encoding UTF8

            Invoke-KoaPythonSql `
                -PythonExe $pythonExe `
                -DatabasePath $DbPath `
                -SqlText $sqlText `
                -SourceName $schemaFile.Name

            $appliedSources += $schemaFile.FullName
        }
    }
    else {
        $warnings += New-KoaMessage `
            -Code "WARN_SCHEMA_FILES_NOT_FOUND" `
            -Severity "warning" `
            -Message "No SQL schema files found; applied embedded canonical schema." `
            -Field "SchemaDir" `
            -Details @{ schema_dir = $SchemaDir }

        Invoke-KoaPythonSql `
            -PythonExe $pythonExe `
            -DatabasePath $DbPath `
            -SqlText (Get-KoaEmbeddedInitialSchemaSql) `
            -SourceName "embedded_initial_schema"

        $appliedSources += "embedded_initial_schema"
    }

    $requiredTables = @(
        "schema_meta",
        "library_rows",
        "chatgpt_intake_log",
        "xlsx_import_log",
        "file_scan_log",
        "audit_log"
    )

    $facts = Get-KoaDbFacts -PythonExe $pythonExe -DatabasePath $DbPath
    $existingTables = @($facts.tables)
    $missingTables = @($requiredTables | Where-Object { $existingTables -notcontains $_ })

    if ($missingTables.Count -gt 0) {
        $result = New-KoaOperationResult `
            -Success $false `
            -Result "schema_incomplete" `
            -Path $DbPath `
            -Data @{
                db_path         = $DbPath
                schema_dir      = $SchemaDir
                applied_sources = $appliedSources
                existing_tables = $existingTables
                missing_tables  = $missingTables
            } `
            -Warnings $warnings `
            -Errors @(
                New-KoaMessage `
                    -Code "ERR_DB_SCHEMA" `
                    -Severity "blocking" `
                    -Message "Database initialized but required tables are missing." `
                    -Field "schema" `
                    -Details @{ missing_tables = $missingTables }
            )

        Write-KoaJsonResult -Result $result
        exit 1
    }

    $auditPayload = @{
        db_path         = $DbPath
        schema_dir      = $SchemaDir
        applied_sources = $appliedSources
        force           = [bool] $Force
    }

    Add-KoaAuditRow `
        -PythonExe $pythonExe `
        -DatabasePath $DbPath `
        -After $auditPayload

    $facts = Get-KoaDbFacts -PythonExe $pythonExe -DatabasePath $DbPath

    $result = New-KoaOperationResult `
        -Success $true `
        -Result "initialized" `
        -Path $DbPath `
        -Data @{
            app_public_name = "Médiathèque kOA"
            app_component   = "koa_mediatheque"
            db_path         = $DbPath
            schema_dir      = $SchemaDir
            schema_version  = $facts.schema_version
            applied_sources = $appliedSources
            tables          = $requiredTables
            row_count       = $facts.row_count
            force           = [bool] $Force
            initialized_at  = Get-KoaTimestamp
        } `
        -Warnings $warnings `
        -Errors @()

    Write-KoaJsonResult -Result $result
    exit 0
}
catch {
    $result = New-KoaOperationResult `
        -Success $false `
        -Result "failed" `
        -Path $DbPath `
        -Errors @(
            New-KoaMessage `
                -Code "ERR_INITIALIZE_DB_FAILED" `
                -Severity "blocking" `
                -Message $_.Exception.Message
        )

    Write-KoaJsonResult -Result $result
    exit 1
}