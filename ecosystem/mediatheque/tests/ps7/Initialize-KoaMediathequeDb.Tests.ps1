# tests/ps7/Initialize-KoaMediathequeDb.Tests.ps1
# Pester 5 tests for 05_TOOLS/Initialize-KoaMediathequeDb.ps1

Set-StrictMode -Version Latest

BeforeAll {
    $ErrorActionPreference = "Stop"

    $TestFile = $PSCommandPath
    $TestsDir = Split-Path -Parent $TestFile
    $ProjectRoot = Split-Path -Parent (Split-Path -Parent $TestsDir)

    $ScriptPath = Join-Path $ProjectRoot "05_TOOLS/Initialize-KoaMediathequeDb.ps1"
    $SchemaDir = Join-Path $ProjectRoot "schemas/sqlite"

    function New-KoaTestTempDir {
        $path = Join-Path ([System.IO.Path]::GetTempPath()) ("koa_mediatheque_tests_" + [System.Guid]::NewGuid().ToString("N"))
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        return $path
    }

    function Invoke-KoaInitializeDb {
        param(
            [Parameter(Mandatory)]
            [string] $DbPath,

            [Parameter(Mandatory)]
            [string] $SchemaDir,

            [switch] $Force
        )

        $args = @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", $ScriptPath,
            "-DbPath", $DbPath,
            "-SchemaDir", $SchemaDir
        )

        if ($Force) {
            $args += "-Force"
        }

        $output = & pwsh @args 2>&1
        $exitCode = $LASTEXITCODE

        return [pscustomobject]@{
            ExitCode = $exitCode
            RawOutput = ($output | Out-String).Trim()
            Lines = @($output)
        }
    }

    function ConvertFrom-KoaJsonOutput {
        param(
            [Parameter(Mandatory)]
            [string] $RawOutput
        )

        $RawOutput | Should -Not -BeNullOrEmpty

        try {
            return $RawOutput | ConvertFrom-Json -ErrorAction Stop
        }
        catch {
            throw "Output is not valid JSON. Output was:`n$RawOutput"
        }
    }

    function Test-KoaSqliteTableExists {
        param(
            [Parameter(Mandatory)]
            [string] $DbPath,

            [Parameter(Mandatory)]
            [string] $TableName
        )

        $python = Get-Command python -ErrorAction SilentlyContinue
        if (-not $python) {
            $python = Get-Command python3 -ErrorAction SilentlyContinue
        }

        if (-not $python) {
            throw "Python is required for this test because it uses the standard sqlite3 module."
        }

        $code = @"
import sqlite3
import sys

db_path = sys.argv[1]
table_name = sys.argv[2]

with sqlite3.connect(db_path) as connection:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()

print("1" if row else "0")
"@

        $result = & $python.Source -c $code $DbPath $TableName
        return (($result | Out-String).Trim() -eq "1")
    }

    function Get-KoaSqliteTableCount {
        param(
            [Parameter(Mandatory)]
            [string] $DbPath
        )

        $python = Get-Command python -ErrorAction SilentlyContinue
        if (-not $python) {
            $python = Get-Command python3 -ErrorAction SilentlyContinue
        }

        if (-not $python) {
            throw "Python is required for this test because it uses the standard sqlite3 module."
        }

        $code = @"
import sqlite3
import sys

db_path = sys.argv[1]

with sqlite3.connect(db_path) as connection:
    count = connection.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'"
    ).fetchone()[0]

print(count)
"@

        $result = & $python.Source -c $code $DbPath
        return [int](($result | Out-String).Trim())
    }
}

Describe "Initialize-KoaMediathequeDb.ps1" {
    It "exists in 05_TOOLS" {
        Test-Path -LiteralPath $ScriptPath | Should -BeTrue
    }

    It "creates a SQLite database and returns valid JSON" {
        $tempDir = New-KoaTestTempDir
        try {
            $dbPath = Join-Path $tempDir "koa_mediatheque.sqlite"

            $result = Invoke-KoaInitializeDb -DbPath $dbPath -SchemaDir $SchemaDir
            $json = ConvertFrom-KoaJsonOutput -RawOutput $result.RawOutput

            $json.success | Should -BeTrue
            $json.operation | Should -Be "Initialize-KoaMediathequeDb"
            $json.result | Should -BeIn @("created", "initialized", "ok")
            $json.errors.Count | Should -Be 0

            Test-Path -LiteralPath $dbPath | Should -BeTrue
        }
        finally {
            Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    It "creates the required canonical tables" {
        $tempDir = New-KoaTestTempDir
        try {
            $dbPath = Join-Path $tempDir "koa_mediatheque.sqlite"

            $result = Invoke-KoaInitializeDb -DbPath $dbPath -SchemaDir $SchemaDir
            $json = ConvertFrom-KoaJsonOutput -RawOutput $result.RawOutput

            $json.success | Should -BeTrue

            $requiredTables = @(
                "library_rows",
                "chatgpt_intake_log",
                "xlsx_import_log",
                "file_scan_log",
                "audit_log",
                "schema_meta"
            )

            foreach ($tableName in $requiredTables) {
                Test-KoaSqliteTableExists -DbPath $dbPath -TableName $tableName | Should -BeTrue
            }
        }
        finally {
            Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    It "applies schema files and produces a non-empty database schema" {
        $tempDir = New-KoaTestTempDir
        try {
            $dbPath = Join-Path $tempDir "koa_mediatheque.sqlite"

            $result = Invoke-KoaInitializeDb -DbPath $dbPath -SchemaDir $SchemaDir
            $json = ConvertFrom-KoaJsonOutput -RawOutput $result.RawOutput

            $json.success | Should -BeTrue

            $tableCount = Get-KoaSqliteTableCount -DbPath $dbPath
            $tableCount | Should -BeGreaterOrEqual 6
        }
        finally {
            Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    It "can overwrite an existing database when -Force is supplied" {
        $tempDir = New-KoaTestTempDir
        try {
            $dbPath = Join-Path $tempDir "koa_mediatheque.sqlite"

            "not a sqlite database" | Set-Content -LiteralPath $dbPath -Encoding UTF8

            $result = Invoke-KoaInitializeDb -DbPath $dbPath -SchemaDir $SchemaDir -Force
            $json = ConvertFrom-KoaJsonOutput -RawOutput $result.RawOutput

            $json.success | Should -BeTrue
            Test-Path -LiteralPath $dbPath | Should -BeTrue
            Test-KoaSqliteTableExists -DbPath $dbPath -TableName "library_rows" | Should -BeTrue
        }
        finally {
            Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    It "returns JSON failure when SchemaDir does not exist" {
        $tempDir = New-KoaTestTempDir
        try {
            $dbPath = Join-Path $tempDir "koa_mediatheque.sqlite"
            $missingSchemaDir = Join-Path $tempDir "missing_schema_versions"

            $result = Invoke-KoaInitializeDb -DbPath $dbPath -SchemaDir $missingSchemaDir
            $json = ConvertFrom-KoaJsonOutput -RawOutput $result.RawOutput

            $json.success | Should -BeFalse
            $json.operation | Should -Be "Initialize-KoaMediathequeDb"
            $json.errors.Count | Should -BeGreaterThan 0
        }
        finally {
            Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    It "returns only one JSON object on stdout" {
        $tempDir = New-KoaTestTempDir
        try {
            $dbPath = Join-Path $tempDir "koa_mediatheque.sqlite"

            $result = Invoke-KoaInitializeDb -DbPath $dbPath -SchemaDir $SchemaDir
            $result.RawOutput | Should -Match "^\s*\{[\s\S]*\}\s*$"

            $json = ConvertFrom-KoaJsonOutput -RawOutput $result.RawOutput
            $json.PSObject.Properties.Name | Should -Contain "success"
            $json.PSObject.Properties.Name | Should -Contain "operation"
            $json.PSObject.Properties.Name | Should -Contain "result"
            $json.PSObject.Properties.Name | Should -Contain "warnings"
            $json.PSObject.Properties.Name | Should -Contain "errors"
        }
        finally {
            Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}