# 05_TOOLS/Scan-KoaFiles.ps1
# Médiathèque kOA — Scan files, calculate local facts, log scan results, optionally add missing rows
# PowerShell 7 only. Emits one JSON result to stdout.

#requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $DbPath,

    [Parameter(Mandatory)]
    [string] $ScanRoot,

    [string] $StorageRoot = "",

    [string] $ImportBatch = "",

    [ValidateSet("DryRun", "FactsOnly", "LogOnly", "AddMissing")]
    [string] $Mode = "LogOnly",

    [switch] $Recurse,

    [string[]] $ExcludeDirectoryNames = @(".git", ".svn", "__pycache__", "node_modules"),

    [string[]] $ExcludeExtensions = @(".tmp", ".bak", ".part", ".crdownload")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Operation = "Scan-KoaFiles"

$CommonModulePath = Join-Path $PSScriptRoot "KoaMediatheque.Common.psm1"

if (-not (Test-Path -LiteralPath $CommonModulePath -PathType Leaf)) {
    $fallback = [ordered]@{
        success      = $false
        operation    = $Operation
        result       = "failed"
        entity_type  = "file_scan"
        entity_uuid  = ""
        version_uuid = ""
        media_uuid   = ""
        path         = $ScanRoot
        data         = @{}
        warnings     = @()
        errors       = @(
            [ordered]@{
                code       = "ERR_COMMON_MODULE_NOT_FOUND"
                severity   = "blocking"
                message    = "Common module not found: $CommonModulePath"
                field      = $null
                row_number = $null
                details    = @{}
            }
        )
    }

    [Console]::Out.WriteLine(($fallback | ConvertTo-Json -Depth 20))
    exit 1
}

Import-Module $CommonModulePath -Force

function ConvertTo-LocalHashtable {
    [CmdletBinding()]
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

function Resolve-KoaDefaultStorageRoot {
    [CmdletBinding()]
    param(
        [string] $ExplicitStorageRoot
    )

    if (-not [string]::IsNullOrWhiteSpace($ExplicitStorageRoot)) {
        return $ExplicitStorageRoot
    }

    $rootPath = Resolve-KoaRootPath -StartingPath $PSScriptRoot
    $contentRoot = Resolve-KoaContentRoot -AppRoot $rootPath
    return (Join-Path $contentRoot "02_STORAGE")
}

function Test-KoaExcludedPath {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [System.IO.FileInfo] $File,

        [string[]] $ExcludedDirectoryNames = @(),

        [string[]] $ExcludedExtensions = @()
    )

    $extension = $File.Extension.ToLowerInvariant()

    if ($ExcludedExtensions -contains $extension) {
        return $true
    }

    $directory = $File.Directory

    while ($null -ne $directory) {
        if ($ExcludedDirectoryNames -contains $directory.Name) {
            return $true
        }

        $directory = $directory.Parent
    }

    return $false
}

function Get-KoaFilesToScan {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $Root,

        [switch] $Recursive,

        [string[]] $ExcludedDirectoryNames = @(),

        [string[]] $ExcludedExtensions = @()
    )

    if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
        throw "ScanRoot not found or not a directory: $Root"
    }

    $scanRootItem = Get-Item -LiteralPath $Root

    $files = @(
        Get-ChildItem `
            -LiteralPath $scanRootItem.FullName `
            -File `
            -Recurse:$Recursive `
            -Force |
            Where-Object {
                -not (Test-KoaExcludedPath `
                    -File $_ `
                    -ExcludedDirectoryNames $ExcludedDirectoryNames `
                    -ExcludedExtensions $ExcludedExtensions)
            } |
            Sort-Object FullName
    )

    return @($files)
}

function Get-KoaStorageFileArea {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $FilePath,

        [Parameter(Mandatory)]
        [string] $StorageRoot
    )

    if ([string]::IsNullOrWhiteSpace($StorageRoot)) {
        return "media_original"
    }

    try {
        $fullFilePath = [System.IO.Path]::GetFullPath($FilePath)
        $fullStorageRoot = [System.IO.Path]::GetFullPath($StorageRoot)

        if (-not $fullStorageRoot.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
            $fullStorageRoot = $fullStorageRoot + [System.IO.Path]::DirectorySeparatorChar
        }

        if (-not $fullFilePath.StartsWith($fullStorageRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            return "media_original"
        }

        $relativePath = [System.IO.Path]::GetRelativePath($fullStorageRoot, $fullFilePath)
        $firstSegment = $relativePath.Split(
            [System.IO.Path]::DirectorySeparatorChar,
            [System.IO.Path]::AltDirectorySeparatorChar
        )[0]

        $canonicalAreas = @(
            "media_original",
            "media_preview",
            "media_thumbnail",
            "media_derivative",
            "media_caption",
            "media_transcript",
            "media_attachment",
            "content_review_files",
            "external_work_reference_files",
            "cultural_protocol_files"
        )

        if ($canonicalAreas -contains $firstSegment) {
            return $firstSegment
        }

        return "media_original"
    }
    catch {
        return "media_original"
    }
}

function Test-KoaPathUnderRoot {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $PathValue,

        [Parameter(Mandatory)]
        [string] $RootValue
    )

    if ([string]::IsNullOrWhiteSpace($PathValue) -or [string]::IsNullOrWhiteSpace($RootValue)) {
        return $false
    }

    try {
        $fullPath = [System.IO.Path]::GetFullPath($PathValue)
        $fullRoot = [System.IO.Path]::GetFullPath($RootValue)

        if (-not $fullRoot.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
            $fullRoot = $fullRoot + [System.IO.Path]::DirectorySeparatorChar
        }

        return $fullPath.StartsWith($fullRoot, [System.StringComparison]::OrdinalIgnoreCase)
    }
    catch {
        return $false
    }
}

function Get-KoaExistingRowsBySha256 {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object] $Connection,

        [Parameter(Mandatory)]
        [string] $Sha256
    )

    if ([string]::IsNullOrWhiteSpace($Sha256)) {
        return @()
    }

    return @(
        Invoke-KoaSqliteQuery `
            -Connection $Connection `
            -Sql "SELECT id, media_uuid, version_uuid, title, filename, original_path, storage_path, status FROM library_rows WHERE sha256 = @sha256 ORDER BY id;" `
            -Parameters @{ sha256 = $Sha256 } `
            -ReadOnly
    )
}

function Get-KoaExistingRowsByOriginalPath {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object] $Connection,

        [Parameter(Mandatory)]
        [string] $OriginalPath
    )

    if ([string]::IsNullOrWhiteSpace($OriginalPath)) {
        return @()
    }

    return @(
        Invoke-KoaSqliteQuery `
            -Connection $Connection `
            -Sql "SELECT id, media_uuid, version_uuid, title, filename, original_path, storage_path, status FROM library_rows WHERE original_path = @original_path OR storage_path = @original_path ORDER BY id;" `
            -Parameters @{ original_path = $OriginalPath } `
            -ReadOnly
    )
}

function Get-KoaMediaTypeFromMimeType {
    [CmdletBinding()]
    param(
        [AllowNull()]
        [string] $MimeType,

        [AllowNull()]
        [string] $Extension
    )

    if ([string]::IsNullOrWhiteSpace($MimeType)) {
        $MimeType = ""
    }

    if ([string]::IsNullOrWhiteSpace($Extension)) {
        $Extension = ""
    }

    $mime = $MimeType.ToLowerInvariant()
    $ext = $Extension.TrimStart(".").ToLowerInvariant()

    if ($mime -eq "application/pdf" -or $ext -eq "pdf") {
        return "pdf"
    }

    if ($mime.StartsWith("image/")) {
        return "image"
    }

    if ($mime.StartsWith("audio/")) {
        return "audio"
    }

    if ($mime.StartsWith("video/")) {
        return "video"
    }

    if ($ext -in @("xls", "xlsx", "csv")) {
        return "spreadsheet"
    }

    if ($ext -in @("ppt", "pptx")) {
        return "presentation"
    }

    if ($ext -in @("zip", "7z", "rar")) {
        return "source_package"
    }

    if ($ext -in @("srt", "vtt")) {
        return "caption"
    }

    if ($ext -in @("txt", "md", "doc", "docx", "rtf")) {
        return "document"
    }

    return "document"
}

function New-KoaScannedLibraryRow {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [hashtable] $FileFacts,

        [Parameter(Mandatory)]
        [string] $ImportBatch,

        [Parameter(Mandatory)]
        [string] $FileArea,

        [Parameter(Mandatory)]
        [string] $StorageRoot
    )

    $mediaUuid = New-KoaUuid
    $versionUuid = New-KoaUuid
    $title = [System.IO.Path]::GetFileNameWithoutExtension([string] $FileFacts["filename"])

    $storagePath = $null
    if (Test-KoaPathUnderRoot -PathValue ([string] $FileFacts["original_path"]) -RootValue $StorageRoot) {
        $storagePath = [string] $FileFacts["original_path"]
    }

    return [ordered]@{
        media_uuid                 = $mediaUuid
        version_uuid               = $versionUuid
        title                      = $title
        subtitle                   = $null
        description                = $null
        summary                    = $null

        original_path              = $FileFacts["original_path"]
        storage_path               = $storagePath
        filename                   = $FileFacts["filename"]
        extension                  = $FileFacts["extension"]
        mimetype                   = $FileFacts["mimetype"]
        filesize                   = $FileFacts["filesize"]
        sha256                     = $FileFacts["sha256"]
        filearea                   = $FileArea

        media_type                 = Get-KoaMediaTypeFromMimeType `
            -MimeType ([string] $FileFacts["mimetype"]) `
            -Extension ([string] $FileFacts["extension"])

        language                   = "fr"
        library_scope              = "koa"
        uckk_relevance             = "unknown"
        target_system              = "none"
        target_export_allowed      = 0

        public_state               = "unknown"
        visibility                 = "private"
        access_level               = "private"

        ownership_scope            = "unknown"
        source_type                = "imported"
        source_ownership           = "unknown_source"
        rights_status              = "unknown"
        rights_note                = $null

        restriction_state          = "unknown"
        restriction_reason         = $null
        redaction_required         = 0

        status                     = "draft"
        provenance                 = "imported"
        ai_validation_state        = "ai_uncertain"
        ai_confidence              = $null
        canonical_validation_state = "unverified"
        human_review_required      = 1
        review_queue               = "file_scan"
        review_reason              = "Created from file scan; metadata requires human or ChatGPT intake review."

        collections_json           = "[]"
        tags_json                  = "[]"
        relations_json             = "[]"
        content_flags_json         = "[]"
        audience_suitability       = "unknown"

        export_to_uckk             = "no"
        export_to_public           = "no"
        export_policy_note         = "Scanned row defaults to non-exportable until reviewed."

        import_batch               = $ImportBatch
        notes                      = "Created by Scan-KoaFiles.ps1"
    }
}

function Insert-KoaFileScanLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object] $Connection,

        [Parameter(Mandatory)]
        [string] $ImportBatch,

        [Parameter(Mandatory)]
        [string] $ScanRoot,

        [Parameter(Mandatory)]
        [string] $FilePath,

        [string] $Sha256 = "",

        [Nullable[int64]] $Filesize = $null,

        [string] $MimeType = "",

        [Parameter(Mandatory)]
        [string] $Status,

        [Parameter(Mandatory)]
        [string] $Message
    )

    $sql = @"
INSERT INTO file_scan_log(
    import_batch,
    scan_root,
    file_path,
    sha256,
    filesize,
    mimetype,
    status,
    message,
    created_at
)
VALUES (
    @import_batch,
    @scan_root,
    @file_path,
    @sha256,
    @filesize,
    @mimetype,
    @status,
    @message,
    CURRENT_TIMESTAMP
);
"@

    Invoke-KoaSqliteNonQuery `
        -Connection $Connection `
        -Sql $sql `
        -Parameters @{
            import_batch = $ImportBatch
            scan_root    = $ScanRoot
            file_path    = $FilePath
            sha256       = $Sha256
            filesize     = $Filesize
            mimetype     = $MimeType
            status       = $Status
            message      = $Message
        } | Out-Null
}

function Insert-KoaAuditLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object] $Connection,

        [Parameter(Mandatory)]
        [string] $Action,

        [Parameter(Mandatory)]
        [string] $EntityType,

        [string] $EntityUuid = "",

        [object] $Before = $null,

        [object] $After = $null,

        [string] $Actor = "local_user",

        [string] $Note = ""
    )

    $sql = @"
INSERT INTO audit_log(action, entity_type, entity_uuid, before_json, after_json, actor, note, created_at)
VALUES (
    @action,
    @entity_type,
    @entity_uuid,
    @before_json,
    @after_json,
    @actor,
    @note,
    CURRENT_TIMESTAMP
);
"@

    $beforeJson = $null
    $afterJson = $null

    if ($null -ne $Before) {
        $beforeJson = ($Before | ConvertTo-Json -Depth 100 -Compress)
    }

    if ($null -ne $After) {
        $afterJson = ($After | ConvertTo-Json -Depth 100 -Compress)
    }

    Invoke-KoaSqliteNonQuery `
        -Connection $Connection `
        -Sql $sql `
        -Parameters @{
            action      = $Action
            entity_type = $EntityType
            entity_uuid = $EntityUuid
            before_json = $beforeJson
            after_json  = $afterJson
            actor       = $Actor
            note        = $Note
        } | Out-Null
}

function Insert-KoaLibraryRowFromScan {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object] $Connection,

        [Parameter(Mandatory)]
        [hashtable] $RowData
    )

    $columns = Get-KoaLibraryRowColumns
    $insertData = @{}

    foreach ($column in $columns) {
        if ($RowData.ContainsKey($column)) {
            $insertData[$column] = $RowData[$column]
        }
    }

    $sql = Join-KoaSqlInsert -TableName "library_rows" -Data $insertData

    Invoke-KoaSqliteNonQuery `
        -Connection $Connection `
        -Sql $sql | Out-Null
}

try {
    $warnings = @()
    $errors = @()

    Test-KoaDbPath -DbPath $DbPath -ThrowOnMissing | Out-Null

    if (-not (Test-Path -LiteralPath $ScanRoot -PathType Container)) {
        $result = New-KoaOperationResult `
            -Success $false `
            -Operation $Operation `
            -Result "scan_root_not_found" `
            -EntityType "file_scan" `
            -Path $ScanRoot `
            -Errors @(
                New-KoaMessage `
                    -Code "ERR_FILE_NOT_FOUND" `
                    -Severity "blocking" `
                    -Message "ScanRoot not found or not a directory: $ScanRoot" `
                    -Field "ScanRoot"
            )

        Write-KoaJsonResult -Result $result
        exit 1
    }

    if ([string]::IsNullOrWhiteSpace($ImportBatch)) {
        $ImportBatch = "scan_" + (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
    }

    $scanRootItem = Get-Item -LiteralPath $ScanRoot
    $storageRootResolved = Resolve-KoaDefaultStorageRoot -ExplicitStorageRoot $StorageRoot

    $connection = Open-KoaSqliteConnection -DbPath $DbPath

    $files = Get-KoaFilesToScan `
        -Root $scanRootItem.FullName `
        -Recursive:$Recurse `
        -ExcludedDirectoryNames $ExcludeDirectoryNames `
        -ExcludedExtensions $ExcludeExtensions

    $scanUuid = New-KoaUuid
    $items = @()

    $scannedCount = 0
    $loggedCount = 0
    $insertedCount = 0
    $duplicateCount = 0
    $existingPathCount = 0
    $failedCount = 0
    $skippedCount = 0

    foreach ($file in $files) {
        $itemWarnings = @()
        $itemErrors = @()
        $scanStatus = "scanned"
        $scanMessage = "File scanned."
        $fileFacts = $null
        $duplicatesBySha256 = @()
        $existingByPath = @()
        $insertedRow = $null

        try {
            $fileFacts = ConvertTo-LocalHashtable -Value (Get-KoaFileFacts -FilePath $file.FullName)
            $scannedCount++

            $duplicatesBySha256 = Get-KoaExistingRowsBySha256 `
                -Connection $connection `
                -Sha256 ([string] $fileFacts["sha256"])

            $existingByPath = Get-KoaExistingRowsByOriginalPath `
                -Connection $connection `
                -OriginalPath ([string] $fileFacts["original_path"])

            if ($duplicatesBySha256.Count -gt 0) {
                $duplicateCount++

                $itemWarnings += New-KoaMessage `
                    -Code "WARN_DUPLICATE_SHA256" `
                    -Severity "warning" `
                    -Message "Existing library_rows records have the same sha256." `
                    -Field "sha256" `
                    -Details @{
                        sha256          = $fileFacts["sha256"]
                        duplicate_count = $duplicatesBySha256.Count
                        duplicates      = $duplicatesBySha256
                    }
            }

            if ($existingByPath.Count -gt 0) {
                $existingPathCount++

                $itemWarnings += New-KoaMessage `
                    -Code "WARN_EXISTING_PATH" `
                    -Severity "warning" `
                    -Message "Existing library_rows records already reference this path." `
                    -Field "original_path" `
                    -Details @{
                        original_path = $fileFacts["original_path"]
                        existing      = $existingByPath
                    }
            }

            if ($Mode -eq "FactsOnly" -or $Mode -eq "DryRun") {
                $scanStatus = if ($Mode -eq "DryRun") { "dry_run" } else { "facts_only" }
                $scanMessage = "Facts calculated; no database rows inserted."
            }
            elseif ($Mode -eq "LogOnly") {
                Insert-KoaFileScanLog `
                    -Connection $connection `
                    -ImportBatch $ImportBatch `
                    -ScanRoot $scanRootItem.FullName `
                    -FilePath ([string] $fileFacts["original_path"]) `
                    -Sha256 ([string] $fileFacts["sha256"]) `
                    -Filesize ([int64] $fileFacts["filesize"]) `
                    -MimeType ([string] $fileFacts["mimetype"]) `
                    -Status "scanned" `
                    -Message "File facts logged."

                $loggedCount++
                $scanStatus = "logged"
                $scanMessage = "File facts logged."
            }
            elseif ($Mode -eq "AddMissing") {
                if ($duplicatesBySha256.Count -gt 0 -or $existingByPath.Count -gt 0) {
                    Insert-KoaFileScanLog `
                        -Connection $connection `
                        -ImportBatch $ImportBatch `
                        -ScanRoot $scanRootItem.FullName `
                        -FilePath ([string] $fileFacts["original_path"]) `
                        -Sha256 ([string] $fileFacts["sha256"]) `
                        -Filesize ([int64] $fileFacts["filesize"]) `
                        -MimeType ([string] $fileFacts["mimetype"]) `
                        -Status "skipped_existing" `
                        -Message "Skipped because file already exists by sha256 or path."

                    $loggedCount++
                    $skippedCount++
                    $scanStatus = "skipped_existing"
                    $scanMessage = "Skipped because file already exists by sha256 or path."
                }
                else {
                    $fileArea = Get-KoaStorageFileArea `
                        -FilePath ([string] $fileFacts["original_path"]) `
                        -StorageRoot $storageRootResolved

                    $newRow = ConvertTo-LocalHashtable -Value (
                        New-KoaScannedLibraryRow `
                            -FileFacts $fileFacts `
                            -ImportBatch $ImportBatch `
                            -FileArea $fileArea `
                            -StorageRoot $storageRootResolved
                    )

                    Insert-KoaLibraryRowFromScan `
                        -Connection $connection `
                        -RowData $newRow

                    Insert-KoaFileScanLog `
                        -Connection $connection `
                        -ImportBatch $ImportBatch `
                        -ScanRoot $scanRootItem.FullName `
                        -FilePath ([string] $fileFacts["original_path"]) `
                        -Sha256 ([string] $fileFacts["sha256"]) `
                        -Filesize ([int64] $fileFacts["filesize"]) `
                        -MimeType ([string] $fileFacts["mimetype"]) `
                        -Status "inserted" `
                        -Message "Inserted new draft library_rows record from scan."

                    Insert-KoaAuditLog `
                        -Connection $connection `
                        -Action "library_row_inserted" `
                        -EntityType "library_row" `
                        -EntityUuid ([string] $newRow["version_uuid"]) `
                        -Before $null `
                        -After $newRow `
                        -Actor "local_user" `
                        -Note "Scan-KoaFiles.ps1 ImportBatch=$ImportBatch"

                    $loggedCount++
                    $insertedCount++
                    $insertedRow = $newRow
                    $scanStatus = "inserted"
                    $scanMessage = "Inserted new draft library_rows record from scan."
                }
            }
        }
        catch {
            $failedCount++
            $scanStatus = "failed"
            $scanMessage = $_.Exception.Message

            $itemErrors += New-KoaMessage `
                -Code "ERR_FILE_SCAN_FAILED" `
                -Severity "error" `
                -Message $_.Exception.Message `
                -Field "file_path" `
                -Details @{ file_path = $file.FullName }

            if ($Mode -in @("LogOnly", "AddMissing")) {
                try {
                    Insert-KoaFileScanLog `
                        -Connection $connection `
                        -ImportBatch $ImportBatch `
                        -ScanRoot $scanRootItem.FullName `
                        -FilePath $file.FullName `
                        -Status "failed" `
                        -Message $_.Exception.Message

                    $loggedCount++
                }
                catch {
                    $itemWarnings += New-KoaMessage `
                        -Code "WARN_FILE_SCAN_LOG_FAILED" `
                        -Severity "warning" `
                        -Message "Could not write file_scan_log failure record: $($_.Exception.Message)" `
                        -Field "file_scan_log"
                }
            }
        }

        $warnings += @($itemWarnings)
        $errors += @($itemErrors)

        $items += [ordered]@{
            file_path           = $file.FullName
            status              = $scanStatus
            message             = $scanMessage
            facts               = $fileFacts
            duplicate_count     = $duplicatesBySha256.Count
            duplicates          = $duplicatesBySha256
            existing_path_count = $existingByPath.Count
            existing_by_path    = $existingByPath
            inserted_row        = $insertedRow
            warnings            = @($itemWarnings)
            errors              = @($itemErrors)
        }
    }

    if ($Mode -in @("LogOnly", "AddMissing")) {
        Insert-KoaAuditLog `
            -Connection $connection `
            -Action "file_scanned" `
            -EntityType "file" `
            -EntityUuid $scanUuid `
            -Before $null `
            -After @{
                scan_uuid           = $scanUuid
                db_path             = $DbPath
                scan_root           = $scanRootItem.FullName
                storage_root        = $storageRootResolved
                import_batch        = $ImportBatch
                mode                = $Mode
                recurse             = [bool] $Recurse
                files_total         = $files.Count
                scanned_count       = $scannedCount
                logged_count        = $loggedCount
                inserted_count      = $insertedCount
                duplicate_count     = $duplicateCount
                existing_path_count = $existingPathCount
                skipped_count       = $skippedCount
                failed_count        = $failedCount
            } `
            -Actor "local_user" `
            -Note "Scan-KoaFiles.ps1"
    }

    $blockingErrors = @($errors | Where-Object { $_.severity -eq "blocking" })
    $success = ($blockingErrors.Count -eq 0)

    $resultName = if ($failedCount -gt 0) {
        "scan_completed_with_errors"
    }
    elseif ($Mode -eq "AddMissing") {
        "scan_completed_add_missing"
    }
    elseif ($Mode -eq "LogOnly") {
        "scan_logged"
    }
    elseif ($Mode -eq "FactsOnly") {
        "facts_calculated"
    }
    else {
        "dry_run"
    }

    $result = New-KoaOperationResult `
        -Success $success `
        -Operation $Operation `
        -Result $resultName `
        -EntityType "file_scan" `
        -EntityUuid $scanUuid `
        -Path $scanRootItem.FullName `
        -Data @{
            scan_uuid           = $scanUuid
            db_path             = $DbPath
            scan_root           = $scanRootItem.FullName
            storage_root        = $storageRootResolved
            import_batch        = $ImportBatch
            mode                = $Mode
            recurse             = [bool] $Recurse
            exclude_directories = $ExcludeDirectoryNames
            exclude_extensions  = $ExcludeExtensions
            files_total         = $files.Count
            scanned_count       = $scannedCount
            logged_count        = $loggedCount
            inserted_count      = $insertedCount
            duplicate_count     = $duplicateCount
            existing_path_count = $existingPathCount
            skipped_count       = $skippedCount
            failed_count        = $failedCount
            items               = $items
        } `
        -Warnings $warnings `
        -Errors $errors

    Write-KoaJsonResult -Result $result

    if ($success) {
        exit 0
    }

    exit 1
}
catch {
    $errorResult = New-KoaOperationResult `
        -Success $false `
        -Operation $Operation `
        -Result "failed" `
        -EntityType "file_scan" `
        -Path $ScanRoot `
        -Errors @(
            New-KoaMessage `
                -Code "ERR_SCAN_FILES_FAILED" `
                -Severity "blocking" `
                -Message $_.Exception.Message
        )

    Write-KoaJsonResult -Result $errorResult
    exit 1
}

