# tests/ps7/Compare-KoaLibraryXlsx.Tests.ps1
#requires -Version 7.0

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Describe "Compare-KoaLibraryXlsx.ps1" {
    BeforeAll {
        function Get-TestRepoRoot {
            $current = Split-Path -Parent $PSCommandPath

            while ($current -and (Split-Path -Leaf $current) -ne "") {
                $candidate = Join-Path $current "05_TOOLS/Compare-KoaLibraryXlsx.ps1"

                if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                    return $current
                }

                $parent = Split-Path -Parent $current

                if ($parent -eq $current) {
                    break
                }

                $current = $parent
            }

            throw "Unable to locate repository root from $PSCommandPath"
        }

        function Get-TestPythonCommand {
            $repoRoot = $script:RepoRoot

            if ([string]::IsNullOrWhiteSpace($repoRoot)) {
                $repoRoot = Get-TestRepoRoot
            }

            $candidatePaths = @()

            if (-not [string]::IsNullOrWhiteSpace($env:KOA_TEST_PYTHON)) {
                $candidatePaths += $env:KOA_TEST_PYTHON
            }

            if (-not [string]::IsNullOrWhiteSpace($env:PYTHON)) {
                $candidatePaths += $env:PYTHON
            }

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

            throw "Python is required for this test because the app stack is Python + SQLite + XLSX."
        }

        function Invoke-TestPythonCode {
            param(
                [Parameter(Mandatory)]
                [string] $Code,

                [Parameter(Mandatory)]
                [string] $ScriptName,

                [string[]] $Arguments = @()
            )

            if ([string]::IsNullOrWhiteSpace($script:TempRoot)) {
                throw "TempRoot is not initialized."
            }

            $pythonCommand = Get-TestPythonCommand
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

            $scriptDir = Join-Path $script:TempRoot "python_helpers"
            New-Item -ItemType Directory -Force -Path $scriptDir | Out-Null

            $scriptPath = Join-Path $scriptDir $ScriptName
            $stderrPath = Join-Path $scriptDir ("stderr_" + [guid]::NewGuid().ToString("N") + ".txt")

            Set-Content -LiteralPath $scriptPath -Value $Code -Encoding UTF8

            try {
                $allArgs = @()
                $allArgs += $pythonArgs
                $allArgs += $scriptPath
                $allArgs += $Arguments

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

                if ($exitCode -ne 0) {
                    throw "Python helper failed with exit code $exitCode.`nScript: $scriptPath`nStderr:`n$stderr`nStdout:`n$raw"
                }

                return $raw
            }
            finally {
                if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
                    Remove-Item -LiteralPath $stderrPath -Force -ErrorAction SilentlyContinue
                }
            }
        }

        function Invoke-JsonScript {
            param(
                [Parameter(Mandatory)]
                [string] $ScriptPath,

                [Parameter(Mandatory)]
                [string[]] $Arguments
            )

            Test-Path -LiteralPath $ScriptPath -PathType Leaf | Should -BeTrue

            if ([string]::IsNullOrWhiteSpace($script:TempRoot)) {
                throw "TempRoot is not initialized."
            }

            $stderrPath = Join-Path $script:TempRoot ("script_stderr_" + [guid]::NewGuid().ToString("N") + ".txt")

            try {
                $stdout = & pwsh -NoProfile -ExecutionPolicy Bypass -File $ScriptPath @Arguments 2>$stderrPath
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
                    throw "Script produced no JSON on stdout. ExitCode=$exitCode`nStderr:`n$stderr"
                }

                try {
                    return $raw | ConvertFrom-Json -ErrorAction Stop
                }
                catch {
                    throw "Script did not return valid JSON. ExitCode=$exitCode`nRaw stdout:`n$raw`nStderr:`n$stderr"
                }
            }
            finally {
                if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
                    Remove-Item -LiteralPath $stderrPath -Force -ErrorAction SilentlyContinue
                }
            }
        }

        function New-TestDatabaseAndXlsx {
            param(
                [Parameter(Mandatory)]
                [string] $DbPath,

                [Parameter(Mandatory)]
                [string] $XlsxPath,

                [Parameter(Mandatory)]
                [ValidateSet("same", "changed", "new", "archive")]
                [string] $Scenario
            )

            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $DbPath) | Out-Null
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $XlsxPath) | Out-Null

            $code = @'
import sqlite3
import sys
from pathlib import Path

from openpyxl import Workbook

db_path = Path(sys.argv[1])
xlsx_path = Path(sys.argv[2])
scenario = sys.argv[3]

db_path.parent.mkdir(parents=True, exist_ok=True)
xlsx_path.parent.mkdir(parents=True, exist_ok=True)

if db_path.exists():
    db_path.unlink()

connection = sqlite3.connect(str(db_path))

try:
    connection.execute("""
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
    human_review_required INTEGER DEFAULT 1,
    review_queue TEXT,
    review_reason TEXT,
    collections_json TEXT DEFAULT '[]',
    tags_json TEXT DEFAULT '[]',
    relations_json TEXT DEFAULT '[]',
    content_flags_json TEXT DEFAULT '[]',
    audience_suitability TEXT DEFAULT 'general',
    export_to_uckk TEXT DEFAULT 'no',
    export_to_public TEXT DEFAULT 'no',
    import_batch TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

    connection.execute("""
INSERT INTO library_rows (
    media_uuid,
    version_uuid,
    title,
    subtitle,
    description,
    summary,
    original_path,
    storage_path,
    filename,
    extension,
    mimetype,
    filesize,
    sha256,
    filearea,
    media_type,
    language,
    library_scope,
    uckk_relevance,
    target_system,
    target_export_allowed,
    public_state,
    visibility,
    access_level,
    ownership_scope,
    source_type,
    source_ownership,
    rights_status,
    rights_note,
    restriction_state,
    restriction_reason,
    redaction_required,
    status,
    provenance,
    ai_validation_state,
    ai_confidence,
    canonical_validation_state,
    human_review_required,
    review_queue,
    review_reason,
    collections_json,
    tags_json,
    relations_json,
    content_flags_json,
    audience_suitability,
    export_to_uckk,
    export_to_public,
    import_batch,
    notes
)
VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
)
""", (
        "11111111-1111-4111-8111-111111111111",
        "22222222-2222-4222-8222-222222222222",
        "Titre original",
        "Sous-titre original",
        "Description originale",
        "Résumé original",
        "/tmp/original.txt",
        "",
        "original.txt",
        ".txt",
        "text/plain",
        123,
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "media_original",
        "document",
        "fr",
        "koa",
        "unknown",
        "none",
        0,
        "unknown",
        "private",
        "private",
        "unknown",
        "unknown",
        "unknown_source",
        "unknown",
        "Droits inconnus.",
        "none",
        "",
        0,
        "active",
        "ai_assisted",
        "ai_uncertain",
        0.5,
        "unverified",
        1,
        "rights_review",
        "Revue requise.",
        '["collection-a"]',
        '["tag-a"]',
        "[]",
        "[]",
        "general",
        "no",
        "no",
        "test_batch",
        "Notes originales",
    ))

    connection.commit()
finally:
    connection.close()

headers = [
    "xlsx_action",
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
    "import_batch",
    "notes",
]

base_row = {
    "xlsx_action": "update",
    "media_uuid": "11111111-1111-4111-8111-111111111111",
    "version_uuid": "22222222-2222-4222-8222-222222222222",
    "title": "Titre original",
    "subtitle": "Sous-titre original",
    "description": "Description originale",
    "summary": "Résumé original",
    "original_path": "/tmp/original.txt",
    "storage_path": "",
    "filename": "original.txt",
    "extension": ".txt",
    "mimetype": "text/plain",
    "filesize": 123,
    "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
    "rights_note": "Droits inconnus.",
    "restriction_state": "none",
    "restriction_reason": "",
    "redaction_required": 0,
    "status": "active",
    "provenance": "ai_assisted",
    "ai_validation_state": "ai_uncertain",
    "ai_confidence": 0.5,
    "canonical_validation_state": "unverified",
    "human_review_required": 1,
    "review_queue": "rights_review",
    "review_reason": "Revue requise.",
    "collections_json": '["collection-a"]',
    "tags_json": '["tag-a"]',
    "relations_json": "[]",
    "content_flags_json": "[]",
    "audience_suitability": "general",
    "export_to_uckk": "no",
    "export_to_public": "no",
    "import_batch": "test_batch",
    "notes": "Notes originales",
}

if scenario == "changed":
    base_row["title"] = "Titre modifie XLSX"
    base_row["description"] = "Description modifiee XLSX"

if scenario == "archive":
    base_row["xlsx_action"] = "archive"

rows = [base_row]

if scenario == "new":
    new_row = dict(base_row)
    new_row["xlsx_action"] = "new"
    new_row["media_uuid"] = "33333333-3333-4333-8333-333333333333"
    new_row["version_uuid"] = "44444444-4444-4444-8444-444444444444"
    new_row["title"] = "Nouveau titre XLSX"
    new_row["filename"] = "new.txt"
    new_row["original_path"] = "/tmp/new.txt"
    new_row["sha256"] = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    new_row["filesize"] = 456
    rows.append(new_row)

workbook = Workbook()
worksheet = workbook.active
worksheet.title = "Library"
worksheet.append(headers)

for row in rows:
    worksheet.append([row.get(header) for header in headers])

report = workbook.create_sheet("Import_Report")
report.append(["key", "value"])
report.append(["scenario", scenario])

lists = workbook.create_sheet("Lists")
lists.append(["field", "value"])
lists.append(["xlsx_action", "update"])

workbook.save(str(xlsx_path))
print("ok")
'@

            $result = Invoke-TestPythonCode `
                -Code $code `
                -ScriptName "create_compare_fixture.py" `
                -Arguments @($DbPath, $XlsxPath, $Scenario)

            $result | Should -Be "ok"
            Test-Path -LiteralPath $DbPath -PathType Leaf | Should -BeTrue
            Test-Path -LiteralPath $XlsxPath -PathType Leaf | Should -BeTrue
        }

        function Get-TestDbScalar {
            param(
                [Parameter(Mandatory)]
                [string] $DbPath,

                [Parameter(Mandatory)]
                [string] $Sql,

                [string[]] $Arguments = @()
            )

            $code = @'
import sqlite3
import sys

db_path = sys.argv[1]
sql = sys.argv[2]
params = tuple(sys.argv[3:])

connection = sqlite3.connect(db_path)
try:
    cursor = connection.execute(sql, params)
    try:
        row = cursor.fetchone()
    finally:
        cursor.close()

    if row is None or row[0] is None:
        print("")
    else:
        print(row[0])
finally:
    connection.close()
'@

            return Invoke-TestPythonCode `
                -Code $code `
                -ScriptName "db_scalar.py" `
                -Arguments (@($DbPath, $Sql) + $Arguments)
        }

        $script:RepoRoot = Get-TestRepoRoot
        $script:ScriptPath = Join-Path $script:RepoRoot "05_TOOLS/Compare-KoaLibraryXlsx.ps1"
    }

    BeforeEach {
        $script:TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("KOA_COMPARE_XLSX_TEST_" + [guid]::NewGuid().ToString("N"))
        New-Item -ItemType Directory -Force -Path $script:TempRoot | Out-Null

        $script:DbDir = Join-Path $script:TempRoot "01_DB"
        $script:ExportDir = Join-Path $script:TempRoot "04_EXPORTS"

        New-Item -ItemType Directory -Force -Path $script:DbDir | Out-Null
        New-Item -ItemType Directory -Force -Path $script:ExportDir | Out-Null

        $script:DbPath = Join-Path $script:DbDir "koa_mediatheque.sqlite"
        $script:XlsxPath = Join-Path $script:ExportDir "library.xlsx"
    }

    AfterEach {
        if ($script:TempRoot -and (Test-Path -LiteralPath $script:TempRoot)) {
            Remove-Item -LiteralPath $script:TempRoot -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    It "exists at the canonical tools path" {
        Test-Path -LiteralPath $script:ScriptPath -PathType Leaf | Should -BeTrue
    }

    It "returns valid JSON when the SQLite database is missing" {
        New-TestDatabaseAndXlsx `
            -DbPath (Join-Path $script:DbDir "throwaway.sqlite") `
            -XlsxPath $script:XlsxPath `
            -Scenario "same"

        $missingDbPath = Join-Path $script:DbDir "missing.sqlite"

        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Arguments @(
                "-DbPath", $missingDbPath,
                "-XlsxPath", $script:XlsxPath
            )

        $result.success | Should -BeFalse
        $result.operation | Should -Be "Compare-KoaLibraryXlsx"
        $result.PSObject.Properties.Name | Should -Contain "errors"
        @($result.errors).Count | Should -BeGreaterThan 0
    }

    It "returns valid JSON when the XLSX file is missing" {
        New-TestDatabaseAndXlsx `
            -DbPath $script:DbPath `
            -XlsxPath $script:XlsxPath `
            -Scenario "same"

        Remove-Item -LiteralPath $script:XlsxPath -Force

        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Arguments @(
                "-DbPath", $script:DbPath,
                "-XlsxPath", $script:XlsxPath
            )

        $result.success | Should -BeFalse
        $result.operation | Should -Be "Compare-KoaLibraryXlsx"
        $result.PSObject.Properties.Name | Should -Contain "errors"
        @($result.errors).Count | Should -BeGreaterThan 0
    }

    It "returns success and zero blocked rows for an unchanged XLSX round-trip" {
        New-TestDatabaseAndXlsx `
            -DbPath $script:DbPath `
            -XlsxPath $script:XlsxPath `
            -Scenario "same"

        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Arguments @(
                "-DbPath", $script:DbPath,
                "-XlsxPath", $script:XlsxPath
            )

        $result.success | Should -BeTrue
        $result.operation | Should -Be "Compare-KoaLibraryXlsx"
        $result.PSObject.Properties.Name | Should -Contain "errors"
        @($result.errors).Count | Should -Be 0

        $raw = $result | ConvertTo-Json -Depth 50
        $raw | Should -Match "22222222-2222-4222-8222-222222222222"
    }

    It "detects changed editable fields without applying them to SQLite" {
        New-TestDatabaseAndXlsx `
            -DbPath $script:DbPath `
            -XlsxPath $script:XlsxPath `
            -Scenario "changed"

        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Arguments @(
                "-DbPath", $script:DbPath,
                "-XlsxPath", $script:XlsxPath
            )

        $result.success | Should -BeTrue
        $result.operation | Should -Be "Compare-KoaLibraryXlsx"
        $result.PSObject.Properties.Name | Should -Contain "errors"
        @($result.errors).Count | Should -Be 0

        $raw = $result | ConvertTo-Json -Depth 50
        $raw | Should -Match "Titre modifi"

        $titleAfterCompare = Get-TestDbScalar `
            -DbPath $script:DbPath `
            -Sql "SELECT title FROM library_rows WHERE version_uuid = ?" `
            -Arguments @("22222222-2222-4222-8222-222222222222")

        $titleAfterCompare | Should -Be "Titre original"
    }

    It "detects archive actions without deleting SQLite rows" {
        New-TestDatabaseAndXlsx `
            -DbPath $script:DbPath `
            -XlsxPath $script:XlsxPath `
            -Scenario "archive"

        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Arguments @(
                "-DbPath", $script:DbPath,
                "-XlsxPath", $script:XlsxPath
            )

        $result.success | Should -BeTrue
        $result.operation | Should -Be "Compare-KoaLibraryXlsx"
        $result.PSObject.Properties.Name | Should -Contain "errors"
        @($result.errors).Count | Should -Be 0

        $raw = $result | ConvertTo-Json -Depth 50
        $raw | Should -Match "archive"

        $countAfterCompare = Get-TestDbScalar `
            -DbPath $script:DbPath `
            -Sql "SELECT COUNT(*) FROM library_rows"

        $statusAfterCompare = Get-TestDbScalar `
            -DbPath $script:DbPath `
            -Sql "SELECT status FROM library_rows WHERE version_uuid = ?" `
            -Arguments @("22222222-2222-4222-8222-222222222222")

        $countAfterCompare | Should -Be "1"
        $statusAfterCompare | Should -Be "active"
    }

    It "detects new XLSX rows as preview-only changes" {
        New-TestDatabaseAndXlsx `
            -DbPath $script:DbPath `
            -XlsxPath $script:XlsxPath `
            -Scenario "new"

        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Arguments @(
                "-DbPath", $script:DbPath,
                "-XlsxPath", $script:XlsxPath
            )

        $result.success | Should -BeTrue
        $result.operation | Should -Be "Compare-KoaLibraryXlsx"
        $result.PSObject.Properties.Name | Should -Contain "errors"
        @($result.errors).Count | Should -Be 0

        $raw = $result | ConvertTo-Json -Depth 50
        $raw | Should -Match "Nouveau titre XLSX"

        $countAfterCompare = Get-TestDbScalar `
            -DbPath $script:DbPath `
            -Sql "SELECT COUNT(*) FROM library_rows"

        $countAfterCompare | Should -Be "1"
    }

    It "always returns the standard operation result envelope" {
        New-TestDatabaseAndXlsx `
            -DbPath $script:DbPath `
            -XlsxPath $script:XlsxPath `
            -Scenario "changed"

        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Arguments @(
                "-DbPath", $script:DbPath,
                "-XlsxPath", $script:XlsxPath
            )

        $result.PSObject.Properties.Name | Should -Contain "success"
        $result.PSObject.Properties.Name | Should -Contain "operation"
        $result.PSObject.Properties.Name | Should -Contain "result"
        $result.PSObject.Properties.Name | Should -Contain "data"
        $result.PSObject.Properties.Name | Should -Contain "warnings"
        $result.PSObject.Properties.Name | Should -Contain "errors"

        $result.operation | Should -Be "Compare-KoaLibraryXlsx"
        $result.PSObject.Properties.Name | Should -Contain "warnings"
        $result.PSObject.Properties.Name | Should -Contain "errors"
    }
}