#Requires -Version 7.0

<#
.SYNOPSIS
Pester tests for 05_TOOLS/Export-KoaManifest.ps1.

These tests verify the PS7 contract for manifest export:

- script exists
- stdout is valid JSON
- JSON result follows OperationResult-style shape
- manifest.json is created
- manifest includes canonical app/export fields
- manifest includes row UUIDs, hashes, MIME, visibility, public state,
  restriction, suitability, provenance, relations, collections, tags,
  validation state, and export policy
- invalid parameter values are rejected cleanly

The test creates an isolated temporary SQLite database using Python's built-in
sqlite3 module so it does not depend on a production database.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

BeforeAll {
    function Get-TestRepoRoot {
        $current = Split-Path -Parent $PSCommandPath

        while ($current) {
            $candidate = Join-Path $current "05_TOOLS"
            if (Test-Path -LiteralPath $candidate -PathType Container) {
                return $current
            }

            $parent = Split-Path -Parent $current
            if ($parent -eq $current) {
                break
            }

            $current = $parent
        }

        throw "Could not locate repository root containing 05_TOOLS from $PSCommandPath"
    }

    function Get-PythonCommand {
        $repoVenvPython = Join-Path $script:RepoRoot ".venv/Scripts/python.exe"

        if (Test-Path -LiteralPath $repoVenvPython -PathType Leaf) {
            return [pscustomobject]@{
                Exe  = $repoVenvPython
                Args = @()
            }
        }

        if (-not [string]::IsNullOrWhiteSpace($env:KOA_TEST_PYTHON)) {
            if (Test-Path -LiteralPath $env:KOA_TEST_PYTHON -PathType Leaf) {
                return [pscustomobject]@{
                    Exe  = $env:KOA_TEST_PYTHON
                    Args = @()
                }
            }
        }

        if (-not [string]::IsNullOrWhiteSpace($env:PYTHON)) {
            if (Test-Path -LiteralPath $env:PYTHON -PathType Leaf) {
                return [pscustomobject]@{
                    Exe  = $env:PYTHON
                    Args = @()
                }
            }
        }

        $python = Get-Command python -ErrorAction SilentlyContinue
        if ($python) {
            return [pscustomobject]@{
                Exe  = $python.Source
                Args = @()
            }
        }

        $python3 = Get-Command python3 -ErrorAction SilentlyContinue
        if ($python3) {
            return [pscustomobject]@{
                Exe  = $python3.Source
                Args = @()
            }
        }

        $py = Get-Command py -ErrorAction SilentlyContinue
        if ($py) {
            return [pscustomobject]@{
                Exe  = $py.Source
                Args = @("-3")
            }
        }

        throw "Python was not found. These tests need Python's built-in sqlite3 module to create a fixture database."
    }

    function Read-TextFileSafe {
        param(
            [Parameter(Mandatory)]
            [string] $Path
        )

        if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
            return ""
        }

        $content = Get-Content -LiteralPath $Path -Raw -ErrorAction SilentlyContinue

        if ($null -eq $content) {
            return ""
        }

        return [string] $content
    }

    function Convert-StreamToTextSafe {
        param(
            [AllowNull()]
            [object] $Value
        )

        if ($null -eq $Value) {
            return ""
        }

        return ($Value | Out-String)
    }

    function Invoke-PythonFixtureScript {
        param(
            [Parameter(Mandatory)]
            [string] $Code,

            [Parameter(Mandatory)]
            [string[]] $Arguments
        )

        if (-not $script:TempRoot) {
            throw "TempRoot is not initialized."
        }

        New-Item -ItemType Directory -Path $script:TempRoot -Force | Out-Null

        $pythonCommand = Get-PythonCommand
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

        $tempScript = Join-Path $script:TempRoot (
            "fixture_script_" + [guid]::NewGuid().ToString("N") + ".py"
        )

        Set-Content -LiteralPath $tempScript -Value $Code -Encoding UTF8

        try {
            $allArgs = @()
            $allArgs += $pythonArgs
            $allArgs += $tempScript
            $allArgs += $Arguments

            $output = & $pythonExe @allArgs 2>&1
            $exitCode = $LASTEXITCODE

            if ($exitCode -ne 0) {
                $outputText = Convert-StreamToTextSafe -Value $output
                throw "Python fixture script failed with exit code $exitCode.`n$outputText"
            }
        }
        finally {
            if (Test-Path -LiteralPath $tempScript -PathType Leaf) {
                Remove-Item -LiteralPath $tempScript -Force -ErrorAction SilentlyContinue
            }
        }
    }

    function Select-JsonObjectText {
        param(
            [AllowNull()]
            [string] $Text
        )

        if ([string]::IsNullOrWhiteSpace($Text)) {
            return ""
        }

        $candidate = $Text.Trim()

        try {
            $candidate | ConvertFrom-Json -ErrorAction Stop | Out-Null
            return $candidate
        }
        catch {
            # Continue with extraction below.
        }

        $start = $candidate.IndexOf("{")
        $end = $candidate.LastIndexOf("}")

        if ($start -lt 0 -or $end -lt $start) {
            return $candidate
        }

        return $candidate.Substring($start, ($end - $start + 1)).Trim()
    }

    function Invoke-JsonScript {
        param(
            [Parameter(Mandatory)]
            [string] $ScriptPath,

            [Parameter(Mandatory)]
            [hashtable] $Parameters
        )

        Test-Path -LiteralPath $ScriptPath -PathType Leaf | Should -BeTrue

        $stdoutPath = Join-Path $script:TempRoot (
            "stdout_" + [guid]::NewGuid().ToString("N") + ".txt"
        )
        $stderrPath = Join-Path $script:TempRoot (
            "stderr_" + [guid]::NewGuid().ToString("N") + ".txt"
        )

        try {
            $argumentList = @(
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                $ScriptPath
            )

            foreach ($key in $Parameters.Keys) {
                $argumentList += "-$key"
                $argumentList += [string] $Parameters[$key]
            }

            & pwsh @argumentList 1>$stdoutPath 2>$stderrPath
            $exitCode = $LASTEXITCODE

            $raw = (Read-TextFileSafe -Path $stdoutPath).Trim()
            $stderr = (Read-TextFileSafe -Path $stderrPath).Trim()
            $jsonText = Select-JsonObjectText -Text $raw

            if ([string]::IsNullOrWhiteSpace($jsonText)) {
                throw "Script produced no JSON on stdout. ExitCode=$exitCode`nRaw stdout:`n$raw`nStderr:`n$stderr"
            }

            try {
                $json = $jsonText | ConvertFrom-Json -ErrorAction Stop
            }
            catch {
                throw "Script stdout was not valid JSON. ExitCode=$exitCode`nRaw stdout:`n$raw`nExtracted JSON:`n$jsonText`nStderr:`n$stderr"
            }

            return [pscustomobject]@{
                Raw      = $jsonText
                Json     = $json
                ExitCode = $exitCode
                Stderr   = $stderr
            }
        }
        finally {
            foreach ($path in @($stdoutPath, $stderrPath)) {
                if (Test-Path -LiteralPath $path -PathType Leaf) {
                    Remove-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
                }
            }
        }
    }

    function New-TestKoaSqliteDatabase {
        param(
            [Parameter(Mandatory)]
            [string] $DbPath
        )

        $dbParent = Split-Path -Parent $DbPath
        New-Item -ItemType Directory -Path $dbParent -Force | Out-Null

        $code = @'
import sqlite3
import sys
from pathlib import Path

db_path = Path(sys.argv[1])
db_path.parent.mkdir(parents=True, exist_ok=True)

connection = sqlite3.connect(str(db_path))
cursor = connection.cursor()

try:
    cursor.executescript("""
CREATE TABLE schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE library_rows (
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

CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT,
    action TEXT,
    entity_type TEXT,
    entity_uuid TEXT,
    before_json TEXT,
    after_json TEXT,
    note TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
""")

    cursor.execute(
        """
        INSERT INTO schema_meta (key, value)
        VALUES
            ('app_component', 'koa_mediatheque'),
            ('schema_version', '001_initial_schema')
        """
    )

    rows = [
        {
            "media_uuid": "11111111-1111-4111-8111-111111111111",
            "version_uuid": "22222222-2222-4222-8222-222222222222",
            "title": "Document public exportable",
            "subtitle": "Fixture",
            "description": "Description test",
            "summary": "Résumé test",
            "original_path": "C:/fixture/public.pdf",
            "storage_path": "02_STORAGE/media_original/22222222-2222-4222-8222-222222222222_public.pdf",
            "filename": "public.pdf",
            "extension": ".pdf",
            "mimetype": "application/pdf",
            "filesize": 12345,
            "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "filearea": "media_original",
            "media_type": "pdf",
            "language": "fr",
            "library_scope": "koa",
            "uckk_relevance": "uckk_reference",
            "target_system": "uckkarchive",
            "target_export_allowed": 1,
            "public_state": "public",
            "visibility": "public",
            "access_level": "public",
            "ownership_scope": "koa_owned",
            "source_type": "produced_by_uckk",
            "source_ownership": "uckk_created",
            "rights_status": "owned",
            "rights_note": "Owned fixture rights",
            "restriction_state": "none",
            "restriction_reason": "",
            "redaction_required": 0,
            "status": "active",
            "provenance": "ai_assisted",
            "ai_validation_state": "ai_validated",
            "ai_confidence": 0.91,
            "canonical_validation_state": "human_reviewed",
            "human_review_required": 0,
            "review_queue": "",
            "review_reason": "",
            "collections_json": '["test_collection"]',
            "tags_json": '["alpha","beta"]',
            "relations_json": '["references:33333333-3333-4333-8333-333333333333"]',
            "content_flags_json": '[]',
            "audience_suitability": "general",
            "export_to_uckk": "yes",
            "export_to_public": "yes",
            "export_policy_note": "Fixture export allowed",
            "import_batch": "test_batch",
            "notes": "Fixture note",
        },
        {
            "media_uuid": "44444444-4444-4444-8444-444444444444",
            "version_uuid": "55555555-5555-4555-8555-555555555555",
            "title": "Document privé non exportable",
            "subtitle": "",
            "description": "Private fixture",
            "summary": "Private summary",
            "original_path": "C:/fixture/private.pdf",
            "storage_path": "02_STORAGE/media_original/55555555-5555-4555-8555-555555555555_private.pdf",
            "filename": "private.pdf",
            "extension": ".pdf",
            "mimetype": "application/pdf",
            "filesize": 67890,
            "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "filearea": "media_original",
            "media_type": "pdf",
            "language": "fr",
            "library_scope": "koa",
            "uckk_relevance": "not_uckk",
            "target_system": "none",
            "target_export_allowed": 0,
            "public_state": "private",
            "visibility": "private",
            "access_level": "private",
            "ownership_scope": "unknown",
            "source_type": "unknown",
            "source_ownership": "unknown_source",
            "rights_status": "unknown",
            "rights_note": "Unknown rights",
            "restriction_state": "possible",
            "restriction_reason": "Private fixture",
            "redaction_required": 1,
            "status": "active",
            "provenance": "ai_assisted",
            "ai_validation_state": "ai_uncertain",
            "ai_confidence": 0.42,
            "canonical_validation_state": "unverified",
            "human_review_required": 1,
            "review_queue": "rights_review",
            "review_reason": "Private fixture needs review",
            "collections_json": '["private_collection"]',
            "tags_json": '["private"]',
            "relations_json": '[]',
            "content_flags_json": '["privacy"]',
            "audience_suitability": "restricted",
            "export_to_uckk": "no",
            "export_to_public": "no",
            "export_policy_note": "Do not export",
            "import_batch": "test_batch",
            "notes": "Private fixture note",
        },
    ]

    insert_columns = [
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
        "collections_json",
        "tags_json",
        "relations_json",
        "content_flags_json",
        "audience_suitability",
        "export_to_uckk",
        "export_to_public",
        "export_policy_note",
        "import_batch",
        "notes",
    ]

    placeholders = ", ".join("?" for _ in insert_columns)
    column_sql = ", ".join(insert_columns)

    for row in rows:
        cursor.execute(
            f"""
            INSERT INTO library_rows ({column_sql})
            VALUES ({placeholders})
            """,
            [row[column] for column in insert_columns],
        )

    connection.commit()
finally:
    cursor.close()
    connection.close()
'@

        Invoke-PythonFixtureScript -Code $code -Arguments @($DbPath)
    }

    $script:RepoRoot = Get-TestRepoRoot
    $script:ScriptPath = Join-Path $script:RepoRoot "05_TOOLS/Export-KoaManifest.ps1"

    $script:TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) (
        "koa_manifest_tests_" + [guid]::NewGuid().ToString("N")
    )

    $script:DbPath = Join-Path $script:TempRoot "01_DB/koa_mediatheque.sqlite"
    $script:OutputDir = Join-Path $script:TempRoot "04_EXPORTS/manifests"

    New-Item -ItemType Directory -Path $script:TempRoot -Force | Out-Null
    New-Item -ItemType Directory -Path (Split-Path -Parent $script:DbPath) -Force | Out-Null
    New-Item -ItemType Directory -Path $script:OutputDir -Force | Out-Null

    New-TestKoaSqliteDatabase -DbPath $script:DbPath
}

AfterAll {
    if ($script:TempRoot -and (Test-Path -LiteralPath $script:TempRoot)) {
        Remove-Item -LiteralPath $script:TempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Describe "Export-KoaManifest.ps1" {
    It "exists in 05_TOOLS" {
        Test-Path -LiteralPath $script:ScriptPath -PathType Leaf | Should -BeTrue
    }

    It "exports a koa_manifest manifest and returns OperationResult JSON" {
        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Parameters @{
                DbPath     = $script:DbPath
                OutputDir  = $script:OutputDir
                ExportType = "koa_manifest"
                FilterJson = "{}"
                Actor      = "pester"
                Reason     = "unit test manifest export"
            }

        $result.Json.success | Should -BeTrue
        $result.Json.operation | Should -Be "Export-KoaManifest"
        $result.Json.result | Should -BeIn @("exported", "success")
        $result.Json.PSObject.Properties.Name | Should -Contain "errors"
        @($result.Json.errors).Count | Should -Be 0

        $result.Json.path | Should -Not -BeNullOrEmpty
        Test-Path -LiteralPath $result.Json.path -PathType Leaf | Should -BeTrue

        Split-Path -Leaf $result.Json.path | Should -Be "manifest.json"
    }

    It "writes manifest.json with canonical top-level fields" {
        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Parameters @{
                DbPath     = $script:DbPath
                OutputDir  = $script:OutputDir
                ExportType = "koa_manifest"
                FilterJson = "{}"
                Actor      = "pester"
                Reason     = "canonical field test"
            }

        $manifest = Get-Content -LiteralPath $result.Json.path -Raw |
            ConvertFrom-Json -ErrorAction Stop

        $manifest.app_name | Should -Be "Médiathèque kOA"
        $manifest.app_component | Should -Be "koa_mediatheque"
        $manifest.export_uuid | Should -Not -BeNullOrEmpty
        $manifest.export_timestamp | Should -Not -BeNullOrEmpty
        $manifest.export_actor | Should -Be "pester"
        $manifest.export_reason | Should -Be "canonical field test"
        $manifest.export_type | Should -Be "koa_manifest"
        $manifest.row_count | Should -BeGreaterOrEqual 2
        $manifest.rows | Should -Not -BeNullOrEmpty
    }

    It "includes row identity, file facts, access, provenance, validation, and export policy" {
        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Parameters @{
                DbPath     = $script:DbPath
                OutputDir  = $script:OutputDir
                ExportType = "koa_manifest"
                FilterJson = "{}"
                Actor      = "pester"
                Reason     = "row field test"
            }

        $manifest = Get-Content -LiteralPath $result.Json.path -Raw |
            ConvertFrom-Json -ErrorAction Stop

        $row = @($manifest.rows) |
            Where-Object { $_.version_uuid -eq "22222222-2222-4222-8222-222222222222" } |
            Select-Object -First 1

        $row | Should -Not -BeNullOrEmpty

        $row.media_uuid | Should -Be "11111111-1111-4111-8111-111111111111"
        $row.version_uuid | Should -Be "22222222-2222-4222-8222-222222222222"
        $row.sha256 | Should -Be "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        $row.filesize | Should -Be 12345
        $row.mimetype | Should -Be "application/pdf"

        $row.visibility | Should -Be "public"
        $row.public_state | Should -Be "public"
        $row.restriction_state | Should -Be "none"
        $row.audience_suitability | Should -Be "general"

        $row.provenance | Should -Be "ai_assisted"
        $row.canonical_validation_state | Should -Be "human_reviewed"

        $row.export_to_uckk | Should -Be "yes"
        $row.export_to_public | Should -Be "yes"
        $row.target_system | Should -Be "uckkarchive"
        $row.target_export_allowed | Should -Be 1
    }

    It "includes collections, tags, relations, and content flags as arrays" {
        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Parameters @{
                DbPath     = $script:DbPath
                OutputDir  = $script:OutputDir
                ExportType = "koa_manifest"
                FilterJson = "{}"
                Actor      = "pester"
                Reason     = "array field test"
            }

        $manifest = Get-Content -LiteralPath $result.Json.path -Raw |
            ConvertFrom-Json -ErrorAction Stop

        $row = @($manifest.rows) |
            Where-Object { $_.version_uuid -eq "22222222-2222-4222-8222-222222222222" } |
            Select-Object -First 1

        @($row.collections) | Should -Contain "test_collection"
        @($row.tags) | Should -Contain "alpha"
        @($row.tags) | Should -Contain "beta"
        @($row.relations) | Should -Contain "references:33333333-3333-4333-8333-333333333333"
        @($row.content_flags).Count | Should -Be 0
    }

    It "supports uckkarchive_candidate export type" {
        $candidateOutputDir = Join-Path $script:TempRoot "04_EXPORTS/uckkarchive"

        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Parameters @{
                DbPath     = $script:DbPath
                OutputDir  = $candidateOutputDir
                ExportType = "uckkarchive_candidate"
                FilterJson = "{}"
                Actor      = "pester"
                Reason     = "uckk candidate test"
            }

        $result.Json.success | Should -BeTrue
        $result.Json.PSObject.Properties.Name | Should -Contain "errors"
        @($result.Json.errors).Count | Should -Be 0
        $result.Json.path | Should -Not -BeNullOrEmpty
        Test-Path -LiteralPath $result.Json.path -PathType Leaf | Should -BeTrue

        $manifest = Get-Content -LiteralPath $result.Json.path -Raw |
            ConvertFrom-Json -ErrorAction Stop

        $manifest.export_type | Should -Be "uckkarchive_candidate"
    }

    It "supports public_review_package export type" {
        $publicOutputDir = Join-Path $script:TempRoot "04_EXPORTS/public_review"

        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Parameters @{
                DbPath     = $script:DbPath
                OutputDir  = $publicOutputDir
                ExportType = "public_review_package"
                FilterJson = "{}"
                Actor      = "pester"
                Reason     = "public review test"
            }

        $result.Json.success | Should -BeTrue
        $result.Json.PSObject.Properties.Name | Should -Contain "errors"
        @($result.Json.errors).Count | Should -Be 0
        $result.Json.path | Should -Not -BeNullOrEmpty
        Test-Path -LiteralPath $result.Json.path -PathType Leaf | Should -BeTrue

        $manifest = Get-Content -LiteralPath $result.Json.path -Raw |
            ConvertFrom-Json -ErrorAction Stop

        $manifest.export_type | Should -Be "public_review_package"
    }

    It "fails with valid JSON when export type is invalid" {
        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Parameters @{
                DbPath     = $script:DbPath
                OutputDir  = $script:OutputDir
                ExportType = "invalid_export_type"
                FilterJson = "{}"
                Actor      = "pester"
                Reason     = "invalid export type test"
            }

        $result.Json.success | Should -BeFalse
        $result.Json.operation | Should -Be "Export-KoaManifest"
        $result.Json.result | Should -Be "invalid_export_type"
        $result.Json.PSObject.Properties.Name | Should -Contain "errors"
        @($result.Json.errors).Count | Should -BeGreaterThan 0
    }

    It "fails with valid JSON when database path does not exist" {
        $missingDbPath = Join-Path $script:TempRoot "missing.sqlite"

        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Parameters @{
                DbPath     = $missingDbPath
                OutputDir  = $script:OutputDir
                ExportType = "koa_manifest"
                FilterJson = "{}"
                Actor      = "pester"
                Reason     = "missing db test"
            }

        $result.Json.success | Should -BeFalse
        $result.Json.operation | Should -Be "Export-KoaManifest"
        $result.Json.PSObject.Properties.Name | Should -Contain "errors"
        @($result.Json.errors).Count | Should -BeGreaterThan 0
    }
}