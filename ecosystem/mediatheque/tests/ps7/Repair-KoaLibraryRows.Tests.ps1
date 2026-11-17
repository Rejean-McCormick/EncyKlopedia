# tests/ps7/Repair-KoaLibraryRows.Tests.ps1
# Médiathèque kOA — Pester tests for 05_TOOLS/Repair-KoaLibraryRows.ps1

Set-StrictMode -Version Latest

BeforeAll {
    $ErrorActionPreference = "Stop"

    $script:TestFilePath = $PSCommandPath
    $script:RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "../..")
    $script:ToolPath = Join-Path $script:RepoRoot "05_TOOLS/Repair-KoaLibraryRows.ps1"
    $script:SchemaDir = Join-Path $script:RepoRoot "schemas/sqlite"

    $script:PythonCommand = $null
    foreach ($candidate in @("python", "py", "python3")) {
        try {
            $versionOutput = & $candidate --version 2>&1
            if ($LASTEXITCODE -eq 0 -and $versionOutput) {
                $script:PythonCommand = $candidate
                break
            }
        } catch {
            continue
        }
    }

    function New-KoaTestWorkspace {
        $root = Join-Path ([System.IO.Path]::GetTempPath()) ("koa_repair_tests_" + [guid]::NewGuid().ToString("N"))
        New-Item -ItemType Directory -Path $root -Force | Out-Null

        $dbPath = Join-Path $root "koa_mediatheque.sqlite"
        $storageRoot = Join-Path $root "02_STORAGE"
        $mediaOriginal = Join-Path $storageRoot "media_original"
        New-Item -ItemType Directory -Path $mediaOriginal -Force | Out-Null

        $sourceFilePath = Join-Path $mediaOriginal "sample.txt"
        "initial test content" | Set-Content -Path $sourceFilePath -Encoding UTF8

        [pscustomobject]@{
            Root = $root
            DbPath = $dbPath
            StorageRoot = $storageRoot
            SourceFilePath = $sourceFilePath
            VersionUuid = "11111111-1111-4111-8111-111111111111"
            MediaUuid = "22222222-2222-4222-8222-222222222222"
        }
    }

    function Remove-KoaTestWorkspace {
        param(
            [Parameter(Mandatory)]
            [string] $Path
        )

        if (Test-Path -LiteralPath $Path) {
            Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    function Invoke-KoaPython {
        param(
            [Parameter(Mandatory)]
            [string] $Code,

            [Parameter()]
            [string[]] $Arguments = @()
        )

        if (-not $script:PythonCommand) {
            throw "Python is required for these tests because SQLite setup uses Python sqlite3."
        }

        $tempScript = Join-Path ([System.IO.Path]::GetTempPath()) ("koa_sqlite_setup_" + [guid]::NewGuid().ToString("N") + ".py")
        try {
            $Code | Set-Content -Path $tempScript -Encoding UTF8
            & $script:PythonCommand $tempScript @Arguments
            if ($LASTEXITCODE -ne 0) {
                throw "Python helper failed with exit code $LASTEXITCODE."
            }
        } finally {
            if (Test-Path -LiteralPath $tempScript) {
                Remove-Item -LiteralPath $tempScript -Force -ErrorAction SilentlyContinue
            }
        }
    }

    function Initialize-KoaRepairTestDatabase {
        param(
            [Parameter(Mandatory)]
            [string] $DbPath,

            [Parameter(Mandatory)]
            [string] $SchemaDir,

            [Parameter(Mandatory)]
            [string] $SourceFilePath,

            [Parameter(Mandatory)]
            [string] $VersionUuid,

            [Parameter(Mandatory)]
            [string] $MediaUuid
        )

        $code = @'
from __future__ import annotations

import hashlib
import mimetypes
import sqlite3
import sys
from pathlib import Path

db_path = Path(sys.argv[1])
schema_dir = Path(sys.argv[2])
source_file_path = Path(sys.argv[3])
version_uuid = sys.argv[4]
media_uuid = sys.argv[5]

schema_files = [
    "001_initial_schema.sql",
    "002_indexes.sql",
    "003_triggers.sql",
    "004_seed_schema_meta.sql",
]

db_path.parent.mkdir(parents=True, exist_ok=True)

connection = sqlite3.connect(str(db_path))
try:
    for schema_file in schema_files:
        sql_path = schema_dir / schema_file
        connection.executescript(sql_path.read_text(encoding="utf-8-sig"))

    data = source_file_path.read_bytes()
    sha256 = hashlib.sha256(data).hexdigest()
    filesize = source_file_path.stat().st_size
    mimetype = mimetypes.guess_type(str(source_file_path))[0] or "text/plain"

    connection.execute(
        """
        INSERT INTO library_rows (
            media_uuid,
            version_uuid,
            title,
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
            restriction_state,
            redaction_required,
            status,
            provenance,
            ai_validation_state,
            canonical_validation_state,
            human_review_required,
            collections_json,
            tags_json,
            relations_json,
            content_flags_json,
            audience_suitability,
            export_to_uckk,
            export_to_public
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            'document',
            'fr',
            'koa',
            'unknown',
            'none',
            0,
            'unknown',
            'private',
            'private',
            'unknown',
            'unknown',
            'unknown_source',
            'unknown',
            'none',
            0,
            'active',
            'ai_assisted',
            'ai_uncertain',
            'unverified',
            0,
            '[]',
            '[]',
            '[]',
            '[]',
            'unknown',
            'no',
            'no'
        );
        """,
        (
            media_uuid,
            version_uuid,
            "Sample repair test row",
            str(source_file_path),
            str(source_file_path),
            source_file_path.name,
            source_file_path.suffix.lstrip("."),
            mimetype,
            filesize,
            sha256,
            "media_original",
        ),
    )

    connection.commit()
finally:
    connection.close()
'@

        Invoke-KoaPython -Code $code -Arguments @(
            $DbPath,
            $SchemaDir,
            $SourceFilePath,
            $VersionUuid,
            $MediaUuid
        )
    }

    function Get-KoaLibraryRowFromTestDatabase {
        param(
            [Parameter(Mandatory)]
            [string] $DbPath,

            [Parameter(Mandatory)]
            [string] $VersionUuid
        )

        $code = @'
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

db_path = Path(sys.argv[1])
version_uuid = sys.argv[2]

connection = sqlite3.connect(str(db_path))
connection.row_factory = sqlite3.Row
try:
    row = connection.execute(
        "SELECT * FROM library_rows WHERE version_uuid = ?",
        (version_uuid,),
    ).fetchone()

    if row is None:
        print("{}")
    else:
        print(json.dumps(dict(row), ensure_ascii=False, sort_keys=True))
finally:
    connection.close()
'@

        $tempScript = Join-Path ([System.IO.Path]::GetTempPath()) ("koa_sqlite_read_" + [guid]::NewGuid().ToString("N") + ".py")
        try {
            $code | Set-Content -Path $tempScript -Encoding UTF8
            $json = & $script:PythonCommand $tempScript $DbPath $VersionUuid
            if ($LASTEXITCODE -ne 0) {
                throw "Python database read failed with exit code $LASTEXITCODE."
            }
            return ($json | ConvertFrom-Json)
        } finally {
            if (Test-Path -LiteralPath $tempScript) {
                Remove-Item -LiteralPath $tempScript -Force -ErrorAction SilentlyContinue
            }
        }
    }

    function Invoke-KoaRepairScript {
        param(
            [Parameter(Mandatory)]
            [string] $DbPath,

            [Parameter()]
            [string] $VersionUuid,

            [Parameter()]
            [string] $RepairMode
        )

        $arguments = @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", $script:ToolPath,
            "-DbPath", $DbPath
        )

        if ($PSBoundParameters.ContainsKey("VersionUuid")) {
            $arguments += @("-VersionUuid", $VersionUuid)
        }

        if ($PSBoundParameters.ContainsKey("RepairMode")) {
            $arguments += @("-RepairMode", $RepairMode)
        }

        $stdout = & pwsh @arguments 2>&1

        if (-not $stdout) {
            throw "Repair-KoaLibraryRows.ps1 produced no stdout."
        }

        $joined = ($stdout | Out-String).Trim()

        try {
            return $joined | ConvertFrom-Json
        } catch {
            throw "Repair-KoaLibraryRows.ps1 stdout is not valid JSON. Stdout: $joined"
        }
    }
}

Describe "Repair-KoaLibraryRows.ps1" {
    BeforeEach {
        $script:Workspace = New-KoaTestWorkspace
    }

    AfterEach {
        Remove-KoaTestWorkspace -Path $script:Workspace.Root
    }

    It "exists at the canonical tool path" {
        Test-Path -LiteralPath $script:ToolPath | Should -BeTrue
    }

    It "returns standard JSON when the database is missing" {
        $missingDbPath = Join-Path $script:Workspace.Root "missing.sqlite"

        $result = Invoke-KoaRepairScript `
            -DbPath $missingDbPath `
            -VersionUuid $script:Workspace.VersionUuid `
            -RepairMode "RecalculateFileFacts"

        $result.success | Should -BeFalse
        $result.operation | Should -Be "Repair-KoaLibraryRows"
        $result.result | Should -Not -BeNullOrEmpty
        $result.errors | Should -Not -BeNullOrEmpty
    }

    It "returns standard JSON when version_uuid is missing from the database" {
        Initialize-KoaRepairTestDatabase `
            -DbPath $script:Workspace.DbPath `
            -SchemaDir $script:SchemaDir `
            -SourceFilePath $script:Workspace.SourceFilePath `
            -VersionUuid $script:Workspace.VersionUuid `
            -MediaUuid $script:Workspace.MediaUuid

        $result = Invoke-KoaRepairScript `
            -DbPath $script:Workspace.DbPath `
            -VersionUuid "33333333-3333-4333-8333-333333333333" `
            -RepairMode "RecalculateFileFacts"

        $result.success | Should -BeFalse
        $result.operation | Should -Be "Repair-KoaLibraryRows"
        $result.version_uuid | Should -Be "33333333-3333-4333-8333-333333333333"
        $result.errors | Should -Not -BeNullOrEmpty
    }

    It "recalculates protected file facts for an existing row" {
        Initialize-KoaRepairTestDatabase `
            -DbPath $script:Workspace.DbPath `
            -SchemaDir $script:SchemaDir `
            -SourceFilePath $script:Workspace.SourceFilePath `
            -VersionUuid $script:Workspace.VersionUuid `
            -MediaUuid $script:Workspace.MediaUuid

        $before = Get-KoaLibraryRowFromTestDatabase `
            -DbPath $script:Workspace.DbPath `
            -VersionUuid $script:Workspace.VersionUuid

        "changed test content" | Set-Content -Path $script:Workspace.SourceFilePath -Encoding UTF8

        $result = Invoke-KoaRepairScript `
            -DbPath $script:Workspace.DbPath `
            -VersionUuid $script:Workspace.VersionUuid `
            -RepairMode "RecalculateFileFacts"

        $after = Get-KoaLibraryRowFromTestDatabase `
            -DbPath $script:Workspace.DbPath `
            -VersionUuid $script:Workspace.VersionUuid

        $result.success | Should -BeTrue
        $result.operation | Should -Be "Repair-KoaLibraryRows"
        $result.result | Should -BeIn @("repaired", "updated", "recalculated")
        $result.version_uuid | Should -Be $script:Workspace.VersionUuid
        $result.media_uuid | Should -Be $script:Workspace.MediaUuid

        $after.sha256 | Should -Not -Be $before.sha256
        $after.filesize | Should -Not -Be $before.filesize
        $after.filename | Should -Be "sample.txt"
        $after.extension | Should -Be "txt"
        $after.updated_at | Should -Not -BeNullOrEmpty
    }

    It "does not modify the row in DryRun mode" {
        Initialize-KoaRepairTestDatabase `
            -DbPath $script:Workspace.DbPath `
            -SchemaDir $script:SchemaDir `
            -SourceFilePath $script:Workspace.SourceFilePath `
            -VersionUuid $script:Workspace.VersionUuid `
            -MediaUuid $script:Workspace.MediaUuid

        $before = Get-KoaLibraryRowFromTestDatabase `
            -DbPath $script:Workspace.DbPath `
            -VersionUuid $script:Workspace.VersionUuid

        "changed dry run content" | Set-Content -Path $script:Workspace.SourceFilePath -Encoding UTF8

        $result = Invoke-KoaRepairScript `
            -DbPath $script:Workspace.DbPath `
            -VersionUuid $script:Workspace.VersionUuid `
            -RepairMode "DryRun"

        $after = Get-KoaLibraryRowFromTestDatabase `
            -DbPath $script:Workspace.DbPath `
            -VersionUuid $script:Workspace.VersionUuid

        $result.success | Should -BeTrue
        $result.operation | Should -Be "Repair-KoaLibraryRows"
        $result.result | Should -BeIn @("dry_run", "previewed", "no_changes_applied")
        $result.version_uuid | Should -Be $script:Workspace.VersionUuid

        $after.sha256 | Should -Be $before.sha256
        $after.filesize | Should -Be $before.filesize
    }

    It "returns standard JSON for an invalid repair mode" {
        Initialize-KoaRepairTestDatabase `
            -DbPath $script:Workspace.DbPath `
            -SchemaDir $script:SchemaDir `
            -SourceFilePath $script:Workspace.SourceFilePath `
            -VersionUuid $script:Workspace.VersionUuid `
            -MediaUuid $script:Workspace.MediaUuid

        $result = Invoke-KoaRepairScript `
            -DbPath $script:Workspace.DbPath `
            -VersionUuid $script:Workspace.VersionUuid `
            -RepairMode "InvalidMode"

        $result.success | Should -BeFalse
        $result.operation | Should -Be "Repair-KoaLibraryRows"
        $result.errors | Should -Not -BeNullOrEmpty
    }
}