# tests/ps7/Add-KoaLibraryRow.Tests.ps1
#requires -Version 7.0

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Describe "Add-KoaLibraryRow.ps1" {
    BeforeAll {
        $TestFilePath = $PSCommandPath
        $Ps7TestsRoot = Split-Path -Parent $TestFilePath
        $TestsRoot = Split-Path -Parent $Ps7TestsRoot
        $ProjectRoot = Split-Path -Parent $TestsRoot

        $ToolsRoot = Join-Path $ProjectRoot "05_TOOLS"
        $FixturesRoot = Join-Path $TestsRoot "fixtures"
        $SchemaDir = Join-Path $ProjectRoot "schemas/sqlite"

        $ScriptPath = Join-Path $ToolsRoot "Add-KoaLibraryRow.ps1"
        $InitScriptPath = Join-Path $ToolsRoot "Initialize-KoaMediathequeDb.ps1"

        $SampleMetadataValidPath = Join-Path $FixturesRoot "sample_metadata_valid.json"
        $SampleMetadataInvalidEnumPath = Join-Path $FixturesRoot "sample_metadata_invalid_enum.json"
        $SampleMetadataVerifiedBlockedPath = Join-Path $FixturesRoot "sample_metadata_verified_blocked.json"
        $SampleFileFixturePath = Join-Path $FixturesRoot "sample_file.txt"

        $PythonExe = if ($env:KOA_TEST_PYTHON -and (Test-Path -LiteralPath $env:KOA_TEST_PYTHON -PathType Leaf)) {
            $env:KOA_TEST_PYTHON
        }
        else {
            "python"
        }

        function Get-KoaPwshExe {
            $processPath = $null

            try {
                $processPath = (Get-Process -Id $PID -ErrorAction Stop).Path
            }
            catch {
                $processPath = $null
            }

            if ($processPath -and (Test-Path -LiteralPath $processPath -PathType Leaf)) {
                return $processPath
            }

            if ($PSHOME) {
                foreach ($leaf in @("pwsh.exe", "pwsh")) {
                    $candidate = Join-Path $PSHOME $leaf

                    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                        return $candidate
                    }
                }
            }

            $command = Get-Command pwsh -ErrorAction SilentlyContinue

            if ($command -and $command.Source) {
                return $command.Source
            }

            throw "PowerShell 7 executable pwsh was not found."
        }

        $PwshExe = Get-KoaPwshExe

        function Invoke-KoaPs7File {
            param(
                [Parameter(Mandatory = $true)]
                [string]$FilePath,

                [Parameter(Mandatory = $true)]
                [System.Collections.IDictionary]$Parameters
            )

            Test-Path -LiteralPath $FilePath -PathType Leaf | Should -BeTrue

            $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
            $startInfo.FileName = $PwshExe
            $startInfo.UseShellExecute = $false
            $startInfo.RedirectStandardOutput = $true
            $startInfo.RedirectStandardError = $true
            $startInfo.CreateNoWindow = $true

            foreach ($argument in @(
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                $FilePath
            )) {
                [void]$startInfo.ArgumentList.Add([string]$argument)
            }

            foreach ($name in $Parameters.Keys) {
                $value = $Parameters[$name]

                if ($null -eq $value) {
                    continue
                }

                if ($value -is [System.Management.Automation.SwitchParameter]) {
                    if ($value.IsPresent) {
                        [void]$startInfo.ArgumentList.Add("-$name")
                    }

                    continue
                }

                if ($value -is [bool]) {
                    if ($value) {
                        [void]$startInfo.ArgumentList.Add("-$name")
                    }

                    continue
                }

                [void]$startInfo.ArgumentList.Add("-$name")
                [void]$startInfo.ArgumentList.Add([string]$value)
            }

            $process = [System.Diagnostics.Process]::Start($startInfo)

            if ($null -eq $process) {
                throw "Failed to start pwsh process for: $FilePath"
            }

            $stdout = $process.StandardOutput.ReadToEnd()
            $stderr = $process.StandardError.ReadToEnd()

            $process.WaitForExit()

            return [pscustomobject]@{
                ExitCode = $process.ExitCode
                Stdout   = $stdout
                Stderr   = $stderr
            }
        }

        function ConvertFrom-KoaStdoutJson {
            param(
                [Parameter(Mandatory = $true)]
                [AllowNull()]
                [object]$Stdout
            )

            if ($null -eq $Stdout) {
                throw "stdout is null."
            }

            if ($Stdout -is [string]) {
                $text = $Stdout.Trim()
            }
            else {
                $lines = @(
                    $Stdout |
                        Where-Object { $null -ne $_ } |
                        ForEach-Object { [string]$_ }
                )

                $text = ($lines -join "`n").Trim()
            }

            $text | Should -Not -BeNullOrEmpty

            try {
                return $text | ConvertFrom-Json -ErrorAction Stop
            }
            catch {
                # Continue with extraction fallback below.
            }

            $firstBrace = $text.IndexOf("{")
            $lastBrace = $text.LastIndexOf("}")

            if ($firstBrace -ge 0 -and $lastBrace -gt $firstBrace) {
                $candidate = $text.Substring($firstBrace, $lastBrace - $firstBrace + 1)

                try {
                    return $candidate | ConvertFrom-Json -ErrorAction Stop
                }
                catch {
                    throw "stdout contains text that looks like JSON but cannot be parsed. stdout=[$text]"
                }
            }

            throw "stdout is not valid JSON and no JSON object could be extracted. stdout=[$text]"
        }

        function Assert-KoaOperationResultShape {
            param(
                [Parameter(Mandatory = $true)]
                [object]$Result
            )

            $propertyNames = @($Result.PSObject.Properties.Name)

            $propertyNames | Should -Contain "success"
            $propertyNames | Should -Contain "operation"
            $propertyNames | Should -Contain "result"
            $propertyNames | Should -Contain "warnings"
            $propertyNames | Should -Contain "errors"

            $Result.success | Should -BeOfType ([bool])
            $Result.operation | Should -BeOfType ([string])
            $Result.result | Should -BeOfType ([string])
            @($Result.warnings).Count | Should -BeGreaterOrEqual 0
            @($Result.errors).Count | Should -BeGreaterOrEqual 0
        }

        function New-KoaTestRoot {
            $root = Join-Path ([System.IO.Path]::GetTempPath()) ("KOA_MEDIATHEQUE_PS7_TEST_" + [guid]::NewGuid().ToString())

            $dirs = @(
                "01_DB",
                "schemas/sqlite",
                "02_STORAGE",
                "02_STORAGE/media_original",
                "02_STORAGE/media_preview",
                "02_STORAGE/media_thumbnail",
                "02_STORAGE/media_derivative",
                "02_STORAGE/media_caption",
                "02_STORAGE/media_transcript",
                "02_STORAGE/media_attachment",
                "02_STORAGE/content_review_files",
                "02_STORAGE/external_work_reference_files",
                "02_STORAGE/cultural_protocol_files",
                "03_IMPORTS",
                "03_IMPORTS/pending_review",
                "04_EXPORTS",
                "07_BACKUPS",
                "08_LOGS"
            )

            foreach ($dir in $dirs) {
                New-Item -ItemType Directory -Path (Join-Path $root $dir) -Force | Out-Null
            }

            return $root
        }

        function Copy-KoaSchemaIntoTestRoot {
            param(
                [Parameter(Mandatory = $true)]
                [string]$DestinationSchemaDir
            )

            if (-not (Test-Path -LiteralPath $SchemaDir -PathType Container)) {
                throw "Missing canonical schema directory: $SchemaDir"
            }

            New-Item -ItemType Directory -Path $DestinationSchemaDir -Force | Out-Null

            $schemaFiles = @(
                Get-ChildItem -LiteralPath $SchemaDir -File -Filter "*.sql" -ErrorAction Stop |
                    Sort-Object Name
            )

            if ($schemaFiles.Count -eq 0) {
                throw "No SQL schema files found in: $SchemaDir"
            }

            foreach ($file in $schemaFiles) {
                Copy-Item -LiteralPath $file.FullName -Destination $DestinationSchemaDir -Force
            }

            $copiedFiles = @(
                Get-ChildItem -LiteralPath $DestinationSchemaDir -File -Filter "*.sql" -ErrorAction Stop |
                    Sort-Object Name
            )

            if ($copiedFiles.Count -eq 0) {
                throw "Schema copy failed. Destination is empty: $DestinationSchemaDir"
            }
        }

        function New-KoaInitializedDb {
            param(
                [Parameter(Mandatory = $true)]
                [string]$Root
            )

            $dbPath = Join-Path $Root "01_DB/koa_mediatheque.sqlite"
            $schemaTarget = Join-Path $Root "schemas/sqlite"

            Copy-KoaSchemaIntoTestRoot -DestinationSchemaDir $schemaTarget

            $run = Invoke-KoaPs7File `
                -FilePath $InitScriptPath `
                -Parameters ([ordered]@{
                    DbPath    = $dbPath
                    SchemaDir = $schemaTarget
                    Force     = $true
                })

            $result = ConvertFrom-KoaStdoutJson -Stdout $run.Stdout
            Assert-KoaOperationResultShape -Result $result

            if ($run.ExitCode -ne 0) {
                throw "Initialize-KoaMediathequeDb.ps1 failed with exit code $($run.ExitCode). stdout=[$($run.Stdout)] stderr=[$($run.Stderr)]"
            }

            $result.success | Should -BeTrue
            Test-Path -LiteralPath $dbPath -PathType Leaf | Should -BeTrue

            return $dbPath
        }

        function New-KoaSampleFile {
            param(
                [Parameter(Mandatory = $true)]
                [string]$Root
            )

            $target = Join-Path $Root "03_IMPORTS/pending_review/sample_file.txt"

            if (Test-Path -LiteralPath $SampleFileFixturePath -PathType Leaf) {
                Copy-Item -LiteralPath $SampleFileFixturePath -Destination $target -Force
            }
            else {
                "Médiathèque kOA sample file for hashing, storage and intake tests." |
                    Set-Content -LiteralPath $target -Encoding UTF8
            }

            return $target
        }

        function Get-KoaFixtureJson {
            param(
                [Parameter(Mandatory = $true)]
                [string]$Path
            )

            Test-Path -LiteralPath $Path -PathType Leaf | Should -BeTrue
            return Get-Content -LiteralPath $Path -Raw -Encoding UTF8
        }

        function Invoke-KoaAddLibraryRow {
            param(
                [Parameter(Mandatory = $true)]
                [string]$DbPath,

                [Parameter(Mandatory = $true)]
                [string]$FilePath,

                [Parameter(Mandatory = $true)]
                [string]$MetadataJson,

                [Parameter(Mandatory = $true)]
                [string]$StorageRoot,

                [Parameter(Mandatory = $false)]
                [string]$ImportBatch = "pester_batch",

                [Parameter(Mandatory = $false)]
                [ValidateSet("InsertNew", "UpdateExisting", "Upsert", "DryRun")]
                [string]$Mode = "InsertNew",

                [Parameter(Mandatory = $false)]
                [switch]$CopyFile
            )

            Test-Path -LiteralPath $ScriptPath -PathType Leaf | Should -BeTrue
            Test-Path -LiteralPath $FilePath -PathType Leaf | Should -BeTrue
            $MetadataJson | Should -Not -BeNullOrEmpty
            $StorageRoot | Should -Not -BeNullOrEmpty

            $parameters = [ordered]@{
                DbPath       = $DbPath
                FilePath     = $FilePath
                MetadataJson = $MetadataJson
                StorageRoot  = $StorageRoot
                ImportBatch  = $ImportBatch
                Mode         = $Mode
            }

            if ($CopyFile.IsPresent) {
                $parameters["CopyFile"] = $true
            }

            $run = Invoke-KoaPs7File `
                -FilePath $ScriptPath `
                -Parameters $parameters

            if ([string]::IsNullOrWhiteSpace($run.Stdout)) {
                throw "Add-KoaLibraryRow.ps1 produced empty stdout. ExitCode=$($run.ExitCode) Stderr=[$($run.Stderr)]"
            }

            return $run.Stdout
        }

        function Invoke-KoaSqliteScalar {
            param(
                [Parameter(Mandatory = $true)]
                [string]$DbPath,

                [Parameter(Mandatory = $true)]
                [string]$Sql
            )

            if (-not (Test-Path -LiteralPath $DbPath -PathType Leaf)) {
                throw "SQLite database does not exist: $DbPath"
            }

            $pythonCode = @'
import sqlite3
import sys

db_path = sys.argv[1]
sql = sys.argv[2]

connection = sqlite3.connect(db_path)
try:
    cursor = connection.execute(sql)
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

            $output = & $PythonExe -c $pythonCode $DbPath $Sql 2>&1

            if ($LASTEXITCODE -ne 0) {
                throw "Python sqlite scalar query failed. Output: $($output -join "`n")"
            }

            $text = $output -join "`n"

            if ($null -eq $text) {
                return ""
            }

            return ([string] $text).Trim()
        }

        function Get-KoaSha256 {
            param(
                [Parameter(Mandatory = $true)]
                [string]$Path
            )

            $stream = [System.IO.File]::OpenRead($Path)

            try {
                $sha = [System.Security.Cryptography.SHA256]::Create()
                $bytes = $sha.ComputeHash($stream)
                return ([System.BitConverter]::ToString($bytes)).Replace("-", "").ToLowerInvariant()
            }
            finally {
                $stream.Dispose()

                if ($null -ne $sha) {
                    $sha.Dispose()
                }
            }
        }
    }

    BeforeEach {
        $KoaRoot = New-KoaTestRoot
        $DbPath = Join-Path $KoaRoot "01_DB/koa_mediatheque.sqlite"
        $StorageRoot = Join-Path $KoaRoot "02_STORAGE"
        $SampleFilePath = New-KoaSampleFile -Root $KoaRoot
        $ValidJson = Get-KoaFixtureJson -Path $SampleMetadataValidPath
        $InvalidEnumJson = Get-KoaFixtureJson -Path $SampleMetadataInvalidEnumPath
        $VerifiedBlockedJson = Get-KoaFixtureJson -Path $SampleMetadataVerifiedBlockedPath
    }

    AfterEach {
        if ($KoaRoot -and (Test-Path -LiteralPath $KoaRoot)) {
            Remove-Item -LiteralPath $KoaRoot -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    It "exists at the canonical tools path" {
        Test-Path -LiteralPath $ScriptPath -PathType Leaf | Should -BeTrue
    }

    It "returns controlled JSON when the database is missing" {
        $stdout = Invoke-KoaAddLibraryRow `
            -DbPath $DbPath `
            -FilePath $SampleFilePath `
            -MetadataJson $ValidJson `
            -StorageRoot $StorageRoot `
            -ImportBatch "missing_db_batch" `
            -Mode "InsertNew" `
            -CopyFile

        $result = ConvertFrom-KoaStdoutJson -Stdout $stdout
        Assert-KoaOperationResultShape -Result $result

        $result.success | Should -BeFalse
        $result.operation | Should -Be "Add-KoaLibraryRow"
        @($result.errors).Count | Should -BeGreaterThan 0
    }

    It "inserts a valid ChatGPT metadata response as one library_rows record" {
        $DbPath = New-KoaInitializedDb -Root $KoaRoot

        $stdout = Invoke-KoaAddLibraryRow `
            -DbPath $DbPath `
            -FilePath $SampleFilePath `
            -MetadataJson $ValidJson `
            -StorageRoot $StorageRoot `
            -ImportBatch "insert_valid_batch" `
            -Mode "InsertNew" `
            -CopyFile

        $result = ConvertFrom-KoaStdoutJson -Stdout $stdout
        Assert-KoaOperationResultShape -Result $result

        $result.success | Should -BeTrue
        $result.operation | Should -Be "Add-KoaLibraryRow"
        $result.result | Should -BeIn @("inserted", "created", "integrated")
        $result.version_uuid | Should -Not -BeNullOrEmpty
        $result.media_uuid | Should -Not -BeNullOrEmpty

        $count = Invoke-KoaSqliteScalar `
            -DbPath $DbPath `
            -Sql "SELECT COUNT(*) FROM library_rows WHERE version_uuid = '$($result.version_uuid)'"

        [int]$count | Should -Be 1
    }

    It "generates media_uuid and version_uuid locally when absent from JSON" {
        $DbPath = New-KoaInitializedDb -Root $KoaRoot

        $stdout = Invoke-KoaAddLibraryRow `
            -DbPath $DbPath `
            -FilePath $SampleFilePath `
            -MetadataJson $ValidJson `
            -StorageRoot $StorageRoot `
            -ImportBatch "uuid_generation_batch" `
            -Mode "InsertNew"

        $result = ConvertFrom-KoaStdoutJson -Stdout $stdout
        Assert-KoaOperationResultShape -Result $result

        $result.success | Should -BeTrue
        $result.version_uuid | Should -Match "^[0-9a-fA-F-]{36}$"
        $result.media_uuid | Should -Match "^[0-9a-fA-F-]{36}$"
        $result.version_uuid | Should -Not -Be $result.media_uuid
    }

    It "recalculates protected technical facts locally instead of trusting JSON metadata" {
        $DbPath = New-KoaInitializedDb -Root $KoaRoot

        $metadata = $ValidJson | ConvertFrom-Json
        $metadata | Add-Member -NotePropertyName "sha256" -NotePropertyValue ("f" * 64) -Force
        $metadata | Add-Member -NotePropertyName "filesize" -NotePropertyValue 999999 -Force
        $metadata | Add-Member -NotePropertyName "mimetype" -NotePropertyValue "application/fake" -Force
        $metadata | Add-Member -NotePropertyName "filename" -NotePropertyValue "ai_invented.pdf" -Force
        $metadata | Add-Member -NotePropertyName "extension" -NotePropertyValue ".pdf" -Force
        $metadata | Add-Member -NotePropertyName "original_path" -NotePropertyValue "/ai/invented/path" -Force
        $metadataJson = $metadata | ConvertTo-Json -Depth 20 -Compress

        $expectedSha256 = Get-KoaSha256 -Path $SampleFilePath
        $expectedSize = (Get-Item -LiteralPath $SampleFilePath).Length

        $stdout = Invoke-KoaAddLibraryRow `
            -DbPath $DbPath `
            -FilePath $SampleFilePath `
            -MetadataJson $metadataJson `
            -StorageRoot $StorageRoot `
            -ImportBatch "local_facts_batch" `
            -Mode "InsertNew"

        $result = ConvertFrom-KoaStdoutJson -Stdout $stdout
        Assert-KoaOperationResultShape -Result $result
        $result.success | Should -BeTrue

        $storedSha256 = Invoke-KoaSqliteScalar `
            -DbPath $DbPath `
            -Sql "SELECT sha256 FROM library_rows WHERE version_uuid = '$($result.version_uuid)'"

        $storedFilesize = Invoke-KoaSqliteScalar `
            -DbPath $DbPath `
            -Sql "SELECT filesize FROM library_rows WHERE version_uuid = '$($result.version_uuid)'"

        $storedFilename = Invoke-KoaSqliteScalar `
            -DbPath $DbPath `
            -Sql "SELECT filename FROM library_rows WHERE version_uuid = '$($result.version_uuid)'"

        $storedOriginalPath = Invoke-KoaSqliteScalar `
            -DbPath $DbPath `
            -Sql "SELECT original_path FROM library_rows WHERE version_uuid = '$($result.version_uuid)'"

        $storedSha256 | Should -Be $expectedSha256
        [int64]$storedFilesize | Should -Be $expectedSize
        $storedFilename | Should -Be (Split-Path -Leaf $SampleFilePath)
        $storedOriginalPath | Should -Be $SampleFilePath
    }

    It "copies the file into media_original when -CopyFile is used" {
        $DbPath = New-KoaInitializedDb -Root $KoaRoot

        $stdout = Invoke-KoaAddLibraryRow `
            -DbPath $DbPath `
            -FilePath $SampleFilePath `
            -MetadataJson $ValidJson `
            -StorageRoot $StorageRoot `
            -ImportBatch "copy_file_batch" `
            -Mode "InsertNew" `
            -CopyFile

        $result = ConvertFrom-KoaStdoutJson -Stdout $stdout
        Assert-KoaOperationResultShape -Result $result
        $result.success | Should -BeTrue

        $storagePath = Invoke-KoaSqliteScalar `
            -DbPath $DbPath `
            -Sql "SELECT storage_path FROM library_rows WHERE version_uuid = '$($result.version_uuid)'"

        $storagePath | Should -Not -BeNullOrEmpty
        Test-Path -LiteralPath $storagePath -PathType Leaf | Should -BeTrue

        Split-Path -Parent $storagePath | Should -Be (Join-Path $StorageRoot "media_original")
        (Get-Content -LiteralPath $storagePath -Raw -Encoding UTF8) | Should -Be (Get-Content -LiteralPath $SampleFilePath -Raw -Encoding UTF8)
    }

    It "keeps reference-only behavior when -CopyFile is omitted" {
        $DbPath = New-KoaInitializedDb -Root $KoaRoot

        $stdout = Invoke-KoaAddLibraryRow `
            -DbPath $DbPath `
            -FilePath $SampleFilePath `
            -MetadataJson $ValidJson `
            -StorageRoot $StorageRoot `
            -ImportBatch "reference_only_batch" `
            -Mode "InsertNew"

        $result = ConvertFrom-KoaStdoutJson -Stdout $stdout
        Assert-KoaOperationResultShape -Result $result
        $result.success | Should -BeTrue

        $storagePath = Invoke-KoaSqliteScalar `
            -DbPath $DbPath `
            -Sql "SELECT storage_path FROM library_rows WHERE version_uuid = '$($result.version_uuid)'"

        $storedFiles = @(Get-ChildItem -LiteralPath (Join-Path $StorageRoot "media_original") -File -ErrorAction SilentlyContinue)

        $storedFiles.Count | Should -Be 0
        $storagePath | Should -BeIn @("", $null, $SampleFilePath)
    }

    It "rejects invalid enum values from ChatGPT metadata" {
        $DbPath = New-KoaInitializedDb -Root $KoaRoot

        $stdout = Invoke-KoaAddLibraryRow `
            -DbPath $DbPath `
            -FilePath $SampleFilePath `
            -MetadataJson $InvalidEnumJson `
            -StorageRoot $StorageRoot `
            -ImportBatch "invalid_enum_batch" `
            -Mode "InsertNew"

        $result = ConvertFrom-KoaStdoutJson -Stdout $stdout
        Assert-KoaOperationResultShape -Result $result

        $result.success | Should -BeFalse
        @($result.errors).Count | Should -BeGreaterThan 0

        $count = Invoke-KoaSqliteScalar `
            -DbPath $DbPath `
            -Sql "SELECT COUNT(*) FROM library_rows"

        [int]$count | Should -Be 0
    }

    It "blocks canonical_validation_state verified without explicit human override" {
        $DbPath = New-KoaInitializedDb -Root $KoaRoot

        $stdout = Invoke-KoaAddLibraryRow `
            -DbPath $DbPath `
            -FilePath $SampleFilePath `
            -MetadataJson $VerifiedBlockedJson `
            -StorageRoot $StorageRoot `
            -ImportBatch "verified_blocked_batch" `
            -Mode "InsertNew"

        $result = ConvertFrom-KoaStdoutJson -Stdout $stdout
        Assert-KoaOperationResultShape -Result $result

        $result.success | Should -BeFalse
        @($result.errors).Count | Should -BeGreaterThan 0

        $count = Invoke-KoaSqliteScalar `
            -DbPath $DbPath `
            -Sql "SELECT COUNT(*) FROM library_rows"

        [int]$count | Should -Be 0
    }

    It "does not insert a row in DryRun mode" {
        $DbPath = New-KoaInitializedDb -Root $KoaRoot

        $stdout = Invoke-KoaAddLibraryRow `
            -DbPath $DbPath `
            -FilePath $SampleFilePath `
            -MetadataJson $ValidJson `
            -StorageRoot $StorageRoot `
            -ImportBatch "dry_run_batch" `
            -Mode "DryRun" `
            -CopyFile

        $result = ConvertFrom-KoaStdoutJson -Stdout $stdout
        Assert-KoaOperationResultShape -Result $result

        $result.success | Should -BeTrue
        $result.result | Should -BeIn @("dry_run", "preview", "validated")

        $count = Invoke-KoaSqliteScalar `
            -DbPath $DbPath `
            -Sql "SELECT COUNT(*) FROM library_rows"

        [int]$count | Should -Be 0

        $storedFiles = @(Get-ChildItem -LiteralPath (Join-Path $StorageRoot "media_original") -File -ErrorAction SilentlyContinue)
        $storedFiles.Count | Should -Be 0
    }

    It "rejects duplicate version_uuid in InsertNew mode" {
        $DbPath = New-KoaInitializedDb -Root $KoaRoot

        $firstStdout = Invoke-KoaAddLibraryRow `
            -DbPath $DbPath `
            -FilePath $SampleFilePath `
            -MetadataJson $ValidJson `
            -StorageRoot $StorageRoot `
            -ImportBatch "duplicate_first_batch" `
            -Mode "InsertNew"

        $first = ConvertFrom-KoaStdoutJson -Stdout $firstStdout
        Assert-KoaOperationResultShape -Result $first
        $first.success | Should -BeTrue

        $metadata = $ValidJson | ConvertFrom-Json
        $metadata | Add-Member -NotePropertyName "version_uuid" -NotePropertyValue $first.version_uuid -Force
        $metadata | Add-Member -NotePropertyName "media_uuid" -NotePropertyValue $first.media_uuid -Force
        $metadataJson = $metadata | ConvertTo-Json -Depth 20 -Compress

        $secondStdout = Invoke-KoaAddLibraryRow `
            -DbPath $DbPath `
            -FilePath $SampleFilePath `
            -MetadataJson $metadataJson `
            -StorageRoot $StorageRoot `
            -ImportBatch "duplicate_second_batch" `
            -Mode "InsertNew"

        $second = ConvertFrom-KoaStdoutJson -Stdout $secondStdout
        Assert-KoaOperationResultShape -Result $second

        $second.success | Should -BeFalse
        @($second.errors).Count | Should -BeGreaterThan 0

        $count = Invoke-KoaSqliteScalar `
            -DbPath $DbPath `
            -Sql "SELECT COUNT(*) FROM library_rows WHERE version_uuid = '$($first.version_uuid)'"

        [int]$count | Should -Be 1
    }

    It "writes chatgpt_intake_log and audit_log on successful insert" {
        $DbPath = New-KoaInitializedDb -Root $KoaRoot

        $stdout = Invoke-KoaAddLibraryRow `
            -DbPath $DbPath `
            -FilePath $SampleFilePath `
            -MetadataJson $ValidJson `
            -StorageRoot $StorageRoot `
            -ImportBatch "logs_batch" `
            -Mode "InsertNew"

        $result = ConvertFrom-KoaStdoutJson -Stdout $stdout
        Assert-KoaOperationResultShape -Result $result
        $result.success | Should -BeTrue

        $intakeLogCount = Invoke-KoaSqliteScalar `
            -DbPath $DbPath `
            -Sql "SELECT COUNT(*) FROM chatgpt_intake_log WHERE version_uuid = '$($result.version_uuid)'"

        $auditLogCount = Invoke-KoaSqliteScalar `
            -DbPath $DbPath `
            -Sql "SELECT COUNT(*) FROM audit_log WHERE entity_uuid = '$($result.version_uuid)' OR after_json LIKE '%$($result.version_uuid)%' OR note LIKE '%$($result.version_uuid)%'"

        [int]$intakeLogCount | Should -BeGreaterOrEqual 1
        [int]$auditLogCount | Should -BeGreaterOrEqual 1
    }
}