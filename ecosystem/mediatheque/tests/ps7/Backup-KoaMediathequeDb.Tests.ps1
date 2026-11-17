# tests/ps7/Backup-KoaMediathequeDb.Tests.ps1
# Médiathèque kOA — Pester tests for 05_TOOLS/Backup-KoaMediathequeDb.ps1

#requires -Version 7.0

Set-StrictMode -Version Latest

BeforeAll {
    $ErrorActionPreference = "Stop"

    $script:RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "../..")
    $script:ToolPath = Join-Path $script:RepoRoot "05_TOOLS/Backup-KoaMediathequeDb.ps1"
    $script:SchemaDir = Join-Path $script:RepoRoot "schemas/sqlite"

    function Get-KoaTestPythonCommand {
        $candidatePaths = @()

        if (-not [string]::IsNullOrWhiteSpace($env:KOA_TEST_PYTHON)) {
            $candidatePaths += $env:KOA_TEST_PYTHON
        }

        if (-not [string]::IsNullOrWhiteSpace($env:PYTHON)) {
            $candidatePaths += $env:PYTHON
        }

        $candidatePaths += @(
            (Join-Path $script:RepoRoot ".venv/Scripts/python.exe"),
            (Join-Path $script:RepoRoot ".venv/bin/python")
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

        throw "Python is required for these tests because SQLite setup uses Python sqlite3."
    }

    function New-KoaTestWorkspace {
        $root = Join-Path ([System.IO.Path]::GetTempPath()) (
            "koa_backup_tests_" + [guid]::NewGuid().ToString("N")
        )

        New-Item -ItemType Directory -Path $root -Force | Out-Null

        [pscustomobject]@{
            Root      = $root
            DbPath    = Join-Path $root "koa_mediatheque.sqlite"
            BackupDir = Join-Path $root "07_BACKUPS"
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

        $pythonCommand = Get-KoaTestPythonCommand
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

        $tempScript = Join-Path ([System.IO.Path]::GetTempPath()) (
            "koa_sqlite_setup_" + [guid]::NewGuid().ToString("N") + ".py"
        )

        try {
            $Code | Set-Content -LiteralPath $tempScript -Encoding UTF8

            $allArgs = @()
            $allArgs += $pythonArgs
            $allArgs += $tempScript
            $allArgs += $Arguments

            $output = & $pythonExe @allArgs 2>&1
            $exitCode = $LASTEXITCODE

            if ($exitCode -ne 0) {
                throw "Python helper failed with exit code $exitCode.`n$($output | Out-String)"
            }
        }
        finally {
            if (Test-Path -LiteralPath $tempScript) {
                Remove-Item -LiteralPath $tempScript -Force -ErrorAction SilentlyContinue
            }
        }
    }

    function Initialize-KoaBackupTestDatabase {
        param(
            [Parameter(Mandatory)]
            [string] $DbPath,

            [Parameter(Mandatory)]
            [string] $SchemaDir
        )

        $code = @'
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

db_path = Path(sys.argv[1])
schema_dir = Path(sys.argv[2])

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

    connection.execute(
        """
        INSERT INTO library_rows (
            media_uuid,
            version_uuid,
            title,
            original_path,
            filename
        )
        VALUES (
            '22222222-2222-4222-8222-222222222222',
            '11111111-1111-4111-8111-111111111111',
            'Backup test row',
            'C:/tmp/backup-test.txt',
            'backup-test.txt'
        );
        """
    )

    connection.commit()
finally:
    connection.close()
'@

        Invoke-KoaPython -Code $code -Arguments @($DbPath, $SchemaDir)
    }

    function Get-KoaTableCount {
        param(
            [Parameter(Mandatory)]
            [string] $DbPath,

            [Parameter(Mandatory)]
            [string] $TableName
        )

        $code = @'
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

db_path = Path(sys.argv[1])
table_name = sys.argv[2]

connection = sqlite3.connect(str(db_path))
try:
    cursor = connection.execute(f"SELECT COUNT(*) FROM {table_name};")
    try:
        row = cursor.fetchone()
    finally:
        cursor.close()

    print(row[0])
finally:
    connection.close()
'@

        $pythonCommand = Get-KoaTestPythonCommand
        $pythonExe = [string] $pythonCommand.Exe
        $pythonArgs = @($pythonCommand.Args)

        $tempScript = Join-Path ([System.IO.Path]::GetTempPath()) (
            "koa_sqlite_count_" + [guid]::NewGuid().ToString("N") + ".py"
        )

        try {
            $code | Set-Content -LiteralPath $tempScript -Encoding UTF8

            $allArgs = @()
            $allArgs += $pythonArgs
            $allArgs += $tempScript
            $allArgs += $DbPath
            $allArgs += $TableName

            $count = & $pythonExe @allArgs 2>&1

            if ($LASTEXITCODE -ne 0) {
                throw "Python table count failed with exit code $LASTEXITCODE.`n$($count | Out-String)"
            }

            return [int] $count
        }
        finally {
            if (Test-Path -LiteralPath $tempScript) {
                Remove-Item -LiteralPath $tempScript -Force -ErrorAction SilentlyContinue
            }
        }
    }

    function Invoke-KoaBackupScript {
        param(
            [Parameter(Mandatory)]
            [string] $DbPath,

            [Parameter(Mandatory)]
            [string] $BackupDir,

            [Parameter()]
            [string] $Reason = "manual"
        )

        $stderrPath = Join-Path ([System.IO.Path]::GetTempPath()) (
            "koa_backup_stderr_" + [guid]::NewGuid().ToString("N") + ".txt"
        )

        $arguments = @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", $script:ToolPath,
            "-DbPath", $DbPath,
            "-BackupDir", $BackupDir,
            "-Reason", $Reason
        )

        try {
            $stdout = & pwsh @arguments 2>$stderrPath
            $exitCode = $LASTEXITCODE
            $joined = ($stdout | Out-String).Trim()

            $stderr = ""
            if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
                $stderrContent = Get-Content -LiteralPath $stderrPath -Raw -ErrorAction SilentlyContinue
                if ($null -ne $stderrContent) {
                    $stderr = $stderrContent.Trim()
                }
            }

            if ([string]::IsNullOrWhiteSpace($joined)) {
                throw "Backup-KoaMediathequeDb.ps1 produced no stdout. ExitCode=$exitCode`nStderr:`n$stderr"
            }

            try {
                return $joined | ConvertFrom-Json -ErrorAction Stop
            }
            catch {
                throw "Backup-KoaMediathequeDb.ps1 stdout is not valid JSON. ExitCode=$exitCode`nStdout:`n$joined`nStderr:`n$stderr"
            }
        }
        finally {
            if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
                Remove-Item -LiteralPath $stderrPath -Force -ErrorAction SilentlyContinue
            }
        }
    }

    function Assert-KoaJsonArrayProperty {
        param(
            [Parameter(Mandatory)]
            [object] $Object,

            [Parameter(Mandatory)]
            [string] $PropertyName
        )

        $Object.PSObject.Properties.Name | Should -Contain $PropertyName
        @($Object.$PropertyName).Count | Should -BeGreaterOrEqual 0
    }
}

Describe "Backup-KoaMediathequeDb.ps1" {
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
        $result = Invoke-KoaBackupScript `
            -DbPath $script:Workspace.DbPath `
            -BackupDir $script:Workspace.BackupDir `
            -Reason "missing-db"

        $result.success | Should -BeFalse
        $result.operation | Should -Be "Backup-KoaMediathequeDb"
        $result.result | Should -Not -BeNullOrEmpty
        $result.PSObject.Properties.Name | Should -Contain "errors"
        @($result.errors).Count | Should -BeGreaterThan 0
    }

    It "creates the backup directory when it does not exist" {
        Initialize-KoaBackupTestDatabase `
            -DbPath $script:Workspace.DbPath `
            -SchemaDir $script:SchemaDir

        Test-Path -LiteralPath $script:Workspace.BackupDir | Should -BeFalse

        $result = Invoke-KoaBackupScript `
            -DbPath $script:Workspace.DbPath `
            -BackupDir $script:Workspace.BackupDir `
            -Reason "manual"

        $result.success | Should -BeTrue
        $result.operation | Should -Be "Backup-KoaMediathequeDb"
        $result.path | Should -Not -BeNullOrEmpty

        Test-Path -LiteralPath $script:Workspace.BackupDir | Should -BeTrue
        Test-Path -LiteralPath $result.path | Should -BeTrue
    }

    It "creates a SQLite backup with the canonical filename pattern" {
        Initialize-KoaBackupTestDatabase `
            -DbPath $script:Workspace.DbPath `
            -SchemaDir $script:SchemaDir

        $result = Invoke-KoaBackupScript `
            -DbPath $script:Workspace.DbPath `
            -BackupDir $script:Workspace.BackupDir `
            -Reason "before-import"

        $result.success | Should -BeTrue
        $result.operation | Should -Be "Backup-KoaMediathequeDb"
        $result.result | Should -BeIn @("created", "created_by_copy")
        $result.path | Should -Match "koa_mediatheque_\d{8}_\d{6}_before_import\.sqlite$"

        Test-Path -LiteralPath $result.path | Should -BeTrue
    }

    It "preserves schema and data in the backup database" {
        Initialize-KoaBackupTestDatabase `
            -DbPath $script:Workspace.DbPath `
            -SchemaDir $script:SchemaDir

        $result = Invoke-KoaBackupScript `
            -DbPath $script:Workspace.DbPath `
            -BackupDir $script:Workspace.BackupDir `
            -Reason "preserve-data"

        $result.success | Should -BeTrue
        Test-Path -LiteralPath $result.path | Should -BeTrue

        $sourceCount = Get-KoaTableCount `
            -DbPath $script:Workspace.DbPath `
            -TableName "library_rows"

        $backupCount = Get-KoaTableCount `
            -DbPath $result.path `
            -TableName "library_rows"

        $sourceCount | Should -Be 1
        $backupCount | Should -Be $sourceCount
    }

    It "sanitizes the reason in the backup filename" {
        Initialize-KoaBackupTestDatabase `
            -DbPath $script:Workspace.DbPath `
            -SchemaDir $script:SchemaDir

        $result = Invoke-KoaBackupScript `
            -DbPath $script:Workspace.DbPath `
            -BackupDir $script:Workspace.BackupDir `
            -Reason "Before XLSX import / user review"

        $result.success | Should -BeTrue
        $result.path | Should -Match "koa_mediatheque_\d{8}_\d{6}_before_xlsx_import_user_review\.sqlite$"
        Test-Path -LiteralPath $result.path | Should -BeTrue
    }

    It "uses manual as the fallback reason when reason is blank" {
        Initialize-KoaBackupTestDatabase `
            -DbPath $script:Workspace.DbPath `
            -SchemaDir $script:SchemaDir

        $result = Invoke-KoaBackupScript `
            -DbPath $script:Workspace.DbPath `
            -BackupDir $script:Workspace.BackupDir `
            -Reason ""

        $result.success | Should -BeTrue
        $result.path | Should -Match "koa_mediatheque_\d{8}_\d{6}_manual\.sqlite$"
        Test-Path -LiteralPath $result.path | Should -BeTrue
    }

    It "returns valid standard JSON fields on success" {
        Initialize-KoaBackupTestDatabase `
            -DbPath $script:Workspace.DbPath `
            -SchemaDir $script:SchemaDir

        $result = Invoke-KoaBackupScript `
            -DbPath $script:Workspace.DbPath `
            -BackupDir $script:Workspace.BackupDir `
            -Reason "json-contract"

        $result.success | Should -BeTrue
        $result.operation | Should -Be "Backup-KoaMediathequeDb"
        $result.result | Should -Not -BeNullOrEmpty
        $result.entity_type | Should -Be "backup"
        $result.path | Should -Not -BeNullOrEmpty

        $result.PSObject.Properties.Name | Should -Contain "data"
        $result.data | Should -Not -Be $null

        Assert-KoaJsonArrayProperty -Object $result -PropertyName "warnings"
        Assert-KoaJsonArrayProperty -Object $result -PropertyName "errors"
        @($result.errors).Count | Should -Be 0
    }
}