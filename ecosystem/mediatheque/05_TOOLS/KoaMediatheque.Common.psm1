# 05_TOOLS/KoaMediatheque.Common.psm1
# Médiathèque kOA — Common PowerShell 7 helpers
# Contract: stdout JSON, SQLite source of truth, local recalculation of technical file facts.

Set-StrictMode -Version Latest

$script:KoaAppPublicName = "Médiathèque kOA"
$script:KoaAppShortName = "kOA"
$script:KoaAppTechnicalName = "koa-mediatheque"
$script:KoaAppComponent = "koa_mediatheque"
$script:KoaDbFilename = "koa_mediatheque.sqlite"

$script:KoaCanonicalStorageAreas = @(
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

$script:KoaMediaStatusValues = @(
    "draft",
    "submitted",
    "active",
    "restricted",
    "superseded",
    "archived",
    "deleted_soft"
)

$script:KoaCanonicalValidationValues = @(
    "unverified",
    "human_reviewed",
    "verified",
    "contested",
    "invalidated",
    "archived"
)

$script:KoaLocalAiValidationValues = @(
    "ai_validated",
    "ai_classified_needs_review",
    "ai_uncertain",
    "ai_rejected"
)

$script:KoaVisibilityValues = @(
    "private",
    "user",
    "group",
    "course",
    "cohort",
    "program",
    "institution",
    "public",
    "restricted",
    "restricted_integrity",
    "restricted_cultural"
)

$script:KoaPublicStateValues = @(
    "public",
    "non_public",
    "private",
    "restricted",
    "confidential",
    "unknown"
)

$script:KoaAccessLevelValues = @(
    "private",
    "limited",
    "internal",
    "public",
    "restricted",
    "confidential",
    "unknown"
)

$script:KoaLibraryScopeValues = @(
    "koa"
)

$script:KoaUckkRelevanceValues = @(
    "uckk_core",
    "uckk_related",
    "uckk_reference",
    "not_uckk",
    "unknown"
)

$script:KoaTargetSystemValues = @(
    "none",
    "uckkarchive",
    "other"
)

$script:KoaExportDecisionValues = @(
    "yes",
    "no",
    "maybe",
    "review_required"
)

$script:KoaMediaTypeValues = @(
    "document",
    "pdf",
    "image",
    "audio",
    "video",
    "transcript",
    "spreadsheet",
    "presentation",
    "source_package",
    "external_reference",
    "other"
)

$script:KoaSourceTypeValues = @(
    "produced_by_uckk",
    "submitted_to_uckk",
    "imported",
    "external_reference_only",
    "licensed_external",
    "public_domain",
    "fair_use_reference",
    "restricted_reference",
    "unknown"
)

$script:KoaSourceOwnershipValues = @(
    "uckk_created",
    "uckk_commissioned",
    "member_submitted",
    "partner_submitted",
    "external_reference",
    "third_party_copyright",
    "public_domain",
    "open_license",
    "unknown_source"
)

$script:KoaOwnershipScopeValues = @(
    "uckk_owned",
    "koa_owned",
    "personal",
    "third_party",
    "public_domain",
    "open_license",
    "unknown"
)

$script:KoaRightsStatusValues = @(
    "owned",
    "licensed",
    "open_license",
    "public_domain",
    "fair_use_reference",
    "third_party",
    "unknown"
)

$script:KoaRestrictionStateValues = @(
    "none",
    "possible",
    "restricted",
    "confidential",
    "cultural",
    "integrity",
    "privacy",
    "copyright",
    "unknown"
)

$script:KoaAudienceSuitabilityValues = @(
    "general",
    "guided",
    "mature",
    "restricted",
    "restricted_cultural",
    "restricted_integrity",
    "staff_only",
    "unknown"
)

$script:KoaRelationTypeValues = @(
    "belongs_to_collection",
    "is_derivative_of",
    "is_translation_of",
    "is_excerpt_of",
    "is_source_for",
    "replaces",
    "references",
    "duplicates",
    "references_external_work",
    "contains_content_marker",
    "related_to"
)

$script:KoaXlsxActionValues = @(
    "update",
    "ignore",
    "archive",
    "new"
)

$script:KoaExportTypeValues = @(
    "xlsx_inventory",
    "koa_manifest",
    "uckkarchive_candidate",
    "public_review_package",
    "backup_snapshot"
)

$script:KoaProtectedTechnicalFields = @(
    "media_uuid",
    "version_uuid",
    "filename",
    "original_path",
    "storage_path",
    "sha256",
    "filesize",
    "mimetype",
    "updated_at"
)

$script:KoaJsonArrayFields = @(
    "collections",
    "tags",
    "relations",
    "content_flags"
)

$script:KoaSqliteJsonTextFields = @(
    "collections_json",
    "tags_json",
    "relations_json",
    "content_flags_json"
)

$script:KoaMetadataEnumFields = @{
    "status"                     = $script:KoaMediaStatusValues
    "media_status"               = $script:KoaMediaStatusValues
    "canonical_validation_state" = $script:KoaCanonicalValidationValues
    "ai_validation_state"        = $script:KoaLocalAiValidationValues
    "visibility"                 = $script:KoaVisibilityValues
    "public_state"               = $script:KoaPublicStateValues
    "access_level"               = $script:KoaAccessLevelValues
    "library_scope"              = $script:KoaLibraryScopeValues
    "uckk_relevance"             = $script:KoaUckkRelevanceValues
    "target_system"              = $script:KoaTargetSystemValues
    "export_to_uckk"             = $script:KoaExportDecisionValues
    "export_to_public"           = $script:KoaExportDecisionValues
    "media_type"                 = $script:KoaMediaTypeValues
    "source_type"                = $script:KoaSourceTypeValues
    "source_ownership"           = $script:KoaSourceOwnershipValues
    "ownership_scope"            = $script:KoaOwnershipScopeValues
    "rights_status"              = $script:KoaRightsStatusValues
    "restriction_state"          = $script:KoaRestrictionStateValues
    "audience_suitability"       = $script:KoaAudienceSuitabilityValues
}

$script:KoaMimeTypesByExtension = @{
    ".txt"  = "text/plain"
    ".md"   = "text/markdown"
    ".json" = "application/json"
    ".csv"  = "text/csv"
    ".xml"  = "application/xml"
    ".html" = "text/html"
    ".htm"  = "text/html"

    ".pdf"  = "application/pdf"
    ".doc"  = "application/msword"
    ".docx" = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ".xls"  = "application/vnd.ms-excel"
    ".xlsx" = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ".ppt"  = "application/vnd.ms-powerpoint"
    ".pptx" = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    ".jpg"  = "image/jpeg"
    ".jpeg" = "image/jpeg"
    ".png"  = "image/png"
    ".gif"  = "image/gif"
    ".webp" = "image/webp"
    ".svg"  = "image/svg+xml"
    ".tif"  = "image/tiff"
    ".tiff" = "image/tiff"

    ".mp3"  = "audio/mpeg"
    ".wav"  = "audio/wav"
    ".flac" = "audio/flac"
    ".m4a"  = "audio/mp4"
    ".ogg"  = "audio/ogg"

    ".mp4"  = "video/mp4"
    ".mov"  = "video/quicktime"
    ".avi"  = "video/x-msvideo"
    ".mkv"  = "video/x-matroska"
    ".webm" = "video/webm"

    ".zip"  = "application/zip"
    ".7z"   = "application/x-7z-compressed"
    ".rar"  = "application/vnd.rar"
}

function Get-KoaTimestamp {
    [CmdletBinding()]
    param()

    return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function New-KoaUuid {
    [CmdletBinding()]
    param()

    return ([guid]::NewGuid().ToString())
}

function New-KoaMessage {
    [CmdletBinding()]
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

function New-KoaOperationResult {
    [CmdletBinding()]
    param(
        [bool] $Success = $false,

        [string] $Operation = "",

        [string] $Result = "",

        [string] $EntityType = "",

        [string] $EntityUuid = "",

        [string] $VersionUuid = "",

        [string] $MediaUuid = "",

        [string] $Path = "",

        [object] $Data = @{},

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

function ConvertTo-KoaJsonResult {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [object] $InputObject,

        [int] $Depth = 20
    )

    process {
        return ($InputObject | ConvertTo-Json -Depth $Depth -Compress:$false)
    }
}

function Write-KoaJsonResult {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object] $Result,

        [int] $Depth = 20
    )

    $json = $Result | ConvertTo-Json -Depth $Depth -Compress:$false
    [Console]::Out.WriteLine($json)
}

function ConvertFrom-KoaJsonText {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [AllowEmptyString()]
        [string] $JsonText
    )

    if ([string]::IsNullOrWhiteSpace($JsonText)) {
        throw "JSON text is empty."
    }

    try {
        return ($JsonText | ConvertFrom-Json -Depth 100)
    }
    catch {
        throw "Invalid JSON: $($_.Exception.Message)"
    }
}

function Resolve-KoaRootPath {
    [CmdletBinding()]
    param(
        [string] $StartingPath = (Get-Location).Path,

        [switch] $Require
    )

    $resolved = Resolve-Path -LiteralPath $StartingPath -ErrorAction SilentlyContinue
    if (-not $resolved) {
        if ($Require) {
            throw "Starting path not found: $StartingPath"
        }
        return $StartingPath
    }

    $currentItem = Get-Item -LiteralPath $resolved.Path
    if (-not $currentItem.PSIsContainer) {
        $currentItem = $currentItem.Directory
    }

    while ($null -ne $currentItem) {
        $hasTools = Test-Path -LiteralPath (Join-Path $currentItem.FullName "05_TOOLS")
        $hasGui = Test-Path -LiteralPath (Join-Path $currentItem.FullName "06_GUI")
        $hasProject = Test-Path -LiteralPath (Join-Path $currentItem.FullName "pyproject.toml")
        $nameMatches = ($currentItem.Name -in @("KOA_MEDIATHEQUE", "mediatheque"))

        if (($hasTools -and $hasGui -and $hasProject) -or $nameMatches) {
            return $currentItem.FullName
        }

        $currentItem = $currentItem.Parent
    }

    if ($Require) {
        throw "Could not resolve KOA_MEDIATHEQUE root from: $StartingPath"
    }

    return (Get-Location).Path
}


function Resolve-KoaContentRoot {
    [CmdletBinding()]
    param(
        [string] $AppRoot = (Resolve-KoaRootPath -StartingPath $PSScriptRoot -Require),
        [string] $ContentPath = ""
    )

    if (-not [string]::IsNullOrWhiteSpace($ContentPath)) {
        return [System.IO.Path]::GetFullPath($ContentPath)
    }
    if (-not [string]::IsNullOrWhiteSpace($env:KOA_CONTENT_ROOT)) {
        return [System.IO.Path]::GetFullPath($env:KOA_CONTENT_ROOT)
    }
    return [System.IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $AppRoot) "content"))
}

function Test-KoaDbPath {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $DbPath,

        [switch] $ThrowOnMissing
    )

    $exists = Test-Path -LiteralPath $DbPath -PathType Leaf

    if (-not $exists -and $ThrowOnMissing) {
        throw "SQLite database not found: $DbPath"
    }

    return $exists
}

function Get-KoaSqliteCommand {
    [CmdletBinding()]
    param()

    $command = Get-Command "sqlite3" -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "sqlite3 CLI was not found in PATH. Install SQLite command-line tools or add sqlite3 to PATH."
    }

    return $command.Source
}

function Open-KoaSqliteConnection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $DbPath,

        [switch] $Create
    )

    $sqlite = Get-KoaSqliteCommand

    $parent = Split-Path -Parent $DbPath
    if (-not [string]::IsNullOrWhiteSpace($parent) -and -not (Test-Path -LiteralPath $parent)) {
        if ($Create) {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }
        else {
            throw "Database directory does not exist: $parent"
        }
    }

    if (-not (Test-Path -LiteralPath $DbPath)) {
        if ($Create) {
            & $sqlite $DbPath "PRAGMA user_version;" | Out-Null
        }
        else {
            throw "SQLite database not found: $DbPath"
        }
    }

    return [pscustomobject]@{
        provider       = "sqlite3"
        db_path        = (Resolve-Path -LiteralPath $DbPath).Path
        sqlite_command = $sqlite
        opened_at      = Get-KoaTimestamp
    }
}

function ConvertTo-KoaSqlLiteral {
    [CmdletBinding()]
    param(
        [AllowNull()]
        [object] $Value
    )

    if ($null -eq $Value) {
        return "NULL"
    }

    if ($Value -is [System.DBNull]) {
        return "NULL"
    }

    if ($Value -is [bool]) {
        if ($Value) {
            return "1"
        }
        return "0"
    }

    if ($Value -is [byte] -or
        $Value -is [int16] -or
        $Value -is [int32] -or
        $Value -is [int64] -or
        $Value -is [single] -or
        $Value -is [double] -or
        $Value -is [decimal]) {
        return ([string]::Format([System.Globalization.CultureInfo]::InvariantCulture, "{0}", $Value))
    }

    if ($Value -is [datetime]) {
        $Value = $Value.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    }
    elseif ($Value -is [array] -or $Value -is [hashtable] -or $Value.PSObject.TypeNames -contains "System.Management.Automation.PSCustomObject") {
        $Value = ($Value | ConvertTo-Json -Depth 50 -Compress)
    }

    $stringValue = [string] $Value
    $escaped = $stringValue.Replace("'", "''")
    return "'$escaped'"
}

function Expand-KoaSqlParameters {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $Sql,

        [hashtable] $Parameters = @{}
    )

    if ($null -eq $Parameters -or $Parameters.Count -eq 0) {
        return $Sql
    }

    $expanded = $Sql

    foreach ($key in $Parameters.Keys) {
        if ($key -notmatch "^[A-Za-z_][A-Za-z0-9_]*$") {
            throw "Invalid SQL parameter name: $key"
        }

        $literal = ConvertTo-KoaSqlLiteral -Value $Parameters[$key]
        $pattern = "(?<![A-Za-z0-9_])@$([regex]::Escape($key))(?![A-Za-z0-9_])"
        $expanded = [regex]::Replace($expanded, $pattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $literal })
    }

    return $expanded
}

function Invoke-KoaSqliteNonQuery {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object] $Connection,

        [Parameter(Mandatory)]
        [string] $Sql,

        [hashtable] $Parameters = @{}
    )

    $expandedSql = Expand-KoaSqlParameters -Sql $Sql -Parameters $Parameters
    $sqlite = $Connection.sqlite_command
    $dbPath = $Connection.db_path

    $fullSql = @"
PRAGMA foreign_keys = ON;
$expandedSql
"@

    $output = & $sqlite $dbPath $fullSql 2>&1
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        throw "SQLite non-query failed: $($output -join "`n")"
    }

    return New-KoaOperationResult `
        -Success $true `
        -Operation "Invoke-KoaSqliteNonQuery" `
        -Result "executed" `
        -Data @{ output = @($output) }
}

function Invoke-KoaSqliteQuery {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object] $Connection,

        [Parameter(Mandatory)]
        [string] $Sql,

        [hashtable] $Parameters = @{},

        [switch] $ReadOnly
    )

    $expandedSql = Expand-KoaSqlParameters -Sql $Sql -Parameters $Parameters
    $sqlite = $Connection.sqlite_command
    $dbPath = $Connection.db_path

    $args = @()
    if ($ReadOnly) {
        $args += "-readonly"
    }

    $args += "-json"
    $args += $dbPath
    $args += $expandedSql

    $output = & $sqlite @args 2>&1
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        throw "SQLite query failed: $($output -join "`n")"
    }

    $jsonText = ($output -join "`n").Trim()

    if ([string]::IsNullOrWhiteSpace($jsonText)) {
        return @()
    }

    try {
        $parsed = $jsonText | ConvertFrom-Json -Depth 100
        if ($null -eq $parsed) {
            return @()
        }

        if ($parsed -is [array]) {
            return @($parsed)
        }

        return @($parsed)
    }
    catch {
        throw "SQLite returned invalid JSON: $($_.Exception.Message). Raw output: $jsonText"
    }
}

function Invoke-KoaSqliteScalar {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object] $Connection,

        [Parameter(Mandatory)]
        [string] $Sql,

        [hashtable] $Parameters = @{},

        [string] $ColumnName = "value"
    )

    $rows = Invoke-KoaSqliteQuery -Connection $Connection -Sql $Sql -Parameters $Parameters -ReadOnly
    if ($rows.Count -eq 0) {
        return $null
    }

    $row = $rows[0]
    if ($row.PSObject.Properties.Name -contains $ColumnName) {
        return $row.$ColumnName
    }

    $firstProperty = $row.PSObject.Properties | Select-Object -First 1
    if ($null -eq $firstProperty) {
        return $null
    }

    return $firstProperty.Value
}

function Get-KoaSha256 {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $FilePath
    )

    if (-not (Test-Path -LiteralPath $FilePath -PathType Leaf)) {
        throw "File not found: $FilePath"
    }

    $hash = Get-FileHash -LiteralPath $FilePath -Algorithm SHA256
    return $hash.Hash.ToLowerInvariant()
}

function Get-KoaMimeType {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $FilePath
    )

    $extension = [System.IO.Path]::GetExtension($FilePath).ToLowerInvariant()

    if ($script:KoaMimeTypesByExtension.ContainsKey($extension)) {
        return $script:KoaMimeTypesByExtension[$extension]
    }

    return "application/octet-stream"
}

function Get-KoaFileFacts {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $FilePath
    )

    if (-not (Test-Path -LiteralPath $FilePath -PathType Leaf)) {
        throw "File not found: $FilePath"
    }

    $item = Get-Item -LiteralPath $FilePath
    $extensionWithDot = [System.IO.Path]::GetExtension($item.Name)
    $extension = $extensionWithDot.TrimStart(".").ToLowerInvariant()

    return [ordered]@{
        original_path = $item.FullName
        filename      = $item.Name
        extension     = $extension
        mimetype      = Get-KoaMimeType -FilePath $item.FullName
        filesize      = [int64] $item.Length
        sha256        = Get-KoaSha256 -FilePath $item.FullName
    }
}

function Test-KoaAllowedValue {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $FieldName,

        [AllowNull()]
        [object] $Value,

        [Parameter(Mandatory)]
        [string[]] $AllowedValues,

        [switch] $AllowNullOrEmpty
    )

    if ($null -eq $Value -or [string]::IsNullOrWhiteSpace([string] $Value)) {
        return [bool] $AllowNullOrEmpty
    }

    return ($AllowedValues -contains ([string] $Value))
}

function Get-KoaEnumValuesForField {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $FieldName
    )

    if ($script:KoaMetadataEnumFields.ContainsKey($FieldName)) {
        return [string[]] $script:KoaMetadataEnumFields[$FieldName]
    }

    return @()
}

function ConvertTo-KoaNormalizedMetadata {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object] $Metadata
    )

    $normalized = [ordered]@{}

    foreach ($property in $Metadata.PSObject.Properties) {
        $name = $property.Name
        $value = $property.Value

        if ($null -eq $value) {
            $normalized[$name] = $null
            continue
        }

        if ($value -is [string]) {
            $normalized[$name] = $value.Trim()
            continue
        }

        $normalized[$name] = $value
    }

    if (-not $normalized.Contains("library_scope")) {
        $normalized["library_scope"] = "koa"
    }

    if (-not $normalized.Contains("canonical_validation_state")) {
        $normalized["canonical_validation_state"] = "unverified"
    }

    if (-not $normalized.Contains("ai_validation_state")) {
        $normalized["ai_validation_state"] = "ai_uncertain"
    }

    if (-not $normalized.Contains("target_system")) {
        $normalized["target_system"] = "none"
    }

    if (-not $normalized.Contains("target_export_allowed")) {
        $normalized["target_export_allowed"] = 0
    }

    if (-not $normalized.Contains("public_state")) {
        $normalized["public_state"] = "unknown"
    }

    if (-not $normalized.Contains("visibility")) {
        $normalized["visibility"] = "private"
    }

    if (-not $normalized.Contains("access_level")) {
        $normalized["access_level"] = "private"
    }

    if (-not $normalized.Contains("source_type")) {
        $normalized["source_type"] = "unknown"
    }

    if (-not $normalized.Contains("source_ownership")) {
        $normalized["source_ownership"] = "unknown_source"
    }

    if (-not $normalized.Contains("ownership_scope")) {
        $normalized["ownership_scope"] = "unknown"
    }

    if (-not $normalized.Contains("rights_status")) {
        $normalized["rights_status"] = "unknown"
    }

    if (-not $normalized.Contains("restriction_state")) {
        $normalized["restriction_state"] = "none"
    }

    if (-not $normalized.Contains("audience_suitability")) {
        $normalized["audience_suitability"] = "unknown"
    }

    if (-not $normalized.Contains("export_to_uckk")) {
        $normalized["export_to_uckk"] = "no"
    }

    if (-not $normalized.Contains("export_to_public")) {
        $normalized["export_to_public"] = "no"
    }

    if (-not $normalized.Contains("media_type")) {
        $normalized["media_type"] = "document"
    }

    if (-not $normalized.Contains("status")) {
        $normalized["status"] = "active"
    }

    foreach ($jsonArrayField in $script:KoaJsonArrayFields) {
        if (-not $normalized.Contains($jsonArrayField)) {
            $normalized[$jsonArrayField] = @()
        }
    }

    return $normalized
}

function Test-KoaMetadataJson {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $MetadataJson,

        [switch] $AllowHumanVerifiedOverride
    )

    $warnings = @()
    $errors = @()
    $normalized = $null

    try {
        $metadata = ConvertFrom-KoaJsonText -JsonText $MetadataJson
        $normalized = ConvertTo-KoaNormalizedMetadata -Metadata $metadata
    }
    catch {
        $errors += New-KoaMessage `
            -Code "ERR_JSON_PARSE" `
            -Severity "blocking" `
            -Message $_.Exception.Message

        return [ordered]@{
            is_valid        = $false
            is_blocked      = $true
            normalized_data = @{}
            warnings        = @($warnings)
            errors          = @($errors)
        }
    }

    if (-not $normalized.Contains("title") -or [string]::IsNullOrWhiteSpace([string] $normalized["title"])) {
        $errors += New-KoaMessage `
            -Code "ERR_REQUIRED_FIELD" `
            -Severity "blocking" `
            -Message "Required field is missing: title" `
            -Field "title"
    }

    foreach ($fieldName in $script:KoaMetadataEnumFields.Keys) {
        if (-not $normalized.Contains($fieldName)) {
            continue
        }

        $value = $normalized[$fieldName]
        if ($null -eq $value -or [string]::IsNullOrWhiteSpace([string] $value)) {
            continue
        }

        $allowedValues = [string[]] $script:KoaMetadataEnumFields[$fieldName]
        if ($allowedValues -notcontains ([string] $value)) {
            $errors += New-KoaMessage `
                -Code "ERR_INVALID_ENUM" `
                -Severity "blocking" `
                -Message "Invalid value '$value' for field '$fieldName'." `
                -Field $fieldName `
                -Details @{ allowed_values = $allowedValues }
        }
    }

    if ($normalized.Contains("canonical_validation_state") -and
        $normalized["canonical_validation_state"] -eq "verified" -and
        -not $AllowHumanVerifiedOverride) {
        $errors += New-KoaMessage `
            -Code "ERR_BLOCKED_VERIFIED" `
            -Severity "blocking" `
            -Message "AI or imported metadata cannot set canonical_validation_state to verified without explicit human override." `
            -Field "canonical_validation_state"
    }

    if ($normalized.Contains("export_to_public") -and
        $normalized["export_to_public"] -eq "yes" -and
        $normalized.Contains("public_state") -and
        $normalized["public_state"] -ne "public") {
        $errors += New-KoaMessage `
            -Code "ERR_BLOCKED_PUBLIC_EXPORT" `
            -Severity "blocking" `
            -Message "export_to_public cannot be yes unless public_state is public." `
            -Field "export_to_public"
    }

    if ($normalized.Contains("export_to_uckk") -and
        $normalized["export_to_uckk"] -eq "yes" -and
        $normalized.Contains("uckk_relevance") -and
        $normalized["uckk_relevance"] -eq "not_uckk") {
        $errors += New-KoaMessage `
            -Code "ERR_BLOCKED_UCKK_EXPORT" `
            -Severity "blocking" `
            -Message "export_to_uckk cannot be yes when uckk_relevance is not_uckk." `
            -Field "export_to_uckk"
    }

    if ($normalized.Contains("rights_status") -and $normalized["rights_status"] -eq "unknown") {
        $warnings += New-KoaMessage `
            -Code "WARN_UNKNOWN_RIGHTS" `
            -Severity "warning" `
            -Message "rights_status is unknown; human review is required before export." `
            -Field "rights_status"
        $normalized["human_review_required"] = 1
    }

    if ($normalized.Contains("source_type") -and $normalized["source_type"] -eq "unknown") {
        $warnings += New-KoaMessage `
            -Code "WARN_UNKNOWN_SOURCE" `
            -Severity "warning" `
            -Message "source_type is unknown; human review is required before export." `
            -Field "source_type"
        $normalized["human_review_required"] = 1
    }

    if ($normalized.Contains("visibility") -and
        ([string] $normalized["visibility"]).StartsWith("restricted")) {
        $warnings += New-KoaMessage `
            -Code "WARN_RESTRICTED_CONTENT" `
            -Severity "warning" `
            -Message "Visibility is restricted; export and access require review." `
            -Field "visibility"
        $normalized["human_review_required"] = 1
    }

    foreach ($jsonArrayField in $script:KoaJsonArrayFields) {
        if (-not $normalized.Contains($jsonArrayField)) {
            continue
        }

        $value = $normalized[$jsonArrayField]
        if ($null -eq $value) {
            $normalized[$jsonArrayField] = @()
            continue
        }

        if ($value -is [string]) {
            if ([string]::IsNullOrWhiteSpace($value)) {
                $normalized[$jsonArrayField] = @()
            }
            else {
                $normalized[$jsonArrayField] = @(
                    $value.Split(";") |
                        ForEach-Object { $_.Trim() } |
                        Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
                )
            }
            continue
        }

        if (-not ($value -is [array])) {
            $errors += New-KoaMessage `
                -Code "ERR_INVALID_TYPE" `
                -Severity "blocking" `
                -Message "Field '$jsonArrayField' must be an array or semicolon-separated string." `
                -Field $jsonArrayField
        }
    }

    $isBlocked = ($errors | Where-Object { $_.severity -eq "blocking" }).Count -gt 0
    $isValid = ($errors.Count -eq 0)

    return [ordered]@{
        is_valid        = $isValid
        is_blocked      = $isBlocked
        normalized_data = $normalized
        warnings        = @($warnings)
        errors          = @($errors)
    }
}

function ConvertTo-KoaJsonArrayText {
    [CmdletBinding()]
    param(
        [AllowNull()]
        [object] $Value
    )

    if ($null -eq $Value) {
        return "[]"
    }

    if ($Value -is [string]) {
        if ([string]::IsNullOrWhiteSpace($Value)) {
            return "[]"
        }

        $items = @(
            $Value.Split(";") |
                ForEach-Object { $_.Trim() } |
                Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
        )

        return ($items | ConvertTo-Json -Depth 20 -Compress)
    }

    if ($Value -is [array]) {
        return ($Value | ConvertTo-Json -Depth 20 -Compress)
    }

    return (@($Value) | ConvertTo-Json -Depth 20 -Compress)
}

function ConvertFrom-KoaJsonArrayText {
    [CmdletBinding()]
    param(
        [AllowNull()]
        [string] $JsonText
    )

    if ([string]::IsNullOrWhiteSpace($JsonText)) {
        return @()
    }

    try {
        $value = $JsonText | ConvertFrom-Json -Depth 50
        if ($null -eq $value) {
            return @()
        }
        return @($value)
    }
    catch {
        return @()
    }
}

function ConvertTo-KoaSafeFilenamePart {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $Value,

        [string] $Fallback = "value"
    )

    $clean = $Value.Trim().ToLowerInvariant()
    $clean = $clean -replace "[^a-z0-9_-]+", "_"
    $clean = $clean -replace "_+", "_"
    $clean = $clean.Trim("_")

    if ([string]::IsNullOrWhiteSpace($clean)) {
        return $Fallback
    }

    return $clean
}

function Backup-KoaDatabase {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $DbPath,

        [Parameter(Mandatory)]
        [string] $BackupDir,

        [Parameter(Mandatory)]
        [string] $Reason
    )

    $operation = "Backup-KoaDatabase"

    try {
        Test-KoaDbPath -DbPath $DbPath -ThrowOnMissing | Out-Null

        if (-not (Test-Path -LiteralPath $BackupDir)) {
            New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
        }

        $timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
        $safeReason = ConvertTo-KoaSafeFilenamePart -Value $Reason -Fallback "backup"
        $backupName = "koa_mediatheque_${timestamp}_${safeReason}.sqlite"
        $backupPath = Join-Path $BackupDir $backupName

        Copy-Item -LiteralPath $DbPath -Destination $backupPath -Force

        $walPath = "$DbPath-wal"
        $shmPath = "$DbPath-shm"

        if (Test-Path -LiteralPath $walPath) {
            Copy-Item -LiteralPath $walPath -Destination "$backupPath-wal" -Force
        }

        if (Test-Path -LiteralPath $shmPath) {
            Copy-Item -LiteralPath $shmPath -Destination "$backupPath-shm" -Force
        }

        return New-KoaOperationResult `
            -Success $true `
            -Operation $operation `
            -Result "backup_created" `
            -EntityType "backup" `
            -Path $backupPath `
            -Data @{
                db_path     = $DbPath
                backup_path = $backupPath
                reason      = $Reason
                created_at  = Get-KoaTimestamp
            }
    }
    catch {
        return New-KoaOperationResult `
            -Success $false `
            -Operation $operation `
            -Result "failed" `
            -EntityType "backup" `
            -Errors @(
                New-KoaMessage `
                    -Code "ERR_BACKUP_FAILED" `
                    -Severity "blocking" `
                    -Message $_.Exception.Message
            )
    }
}

function Get-KoaLibraryRowColumnDefaults {
    [CmdletBinding()]
    param()

    return [ordered]@{
        subtitle                   = $null
        description                = $null
        summary                    = $null
        storage_path               = $null
        extension                  = $null
        mimetype                   = $null
        filesize                   = $null
        sha256                     = $null
        filearea                   = "media_original"
        media_type                 = "document"
        language                   = "fr"
        library_scope              = "koa"
        uckk_relevance             = "unknown"
        target_system              = "none"
        target_export_allowed      = 0
        public_state               = "unknown"
        visibility                 = "private"
        access_level               = "private"
        ownership_scope            = "unknown"
        source_type                = "unknown"
        source_ownership           = "unknown_source"
        rights_status              = "unknown"
        rights_note                = $null
        restriction_state          = "none"
        restriction_reason         = $null
        redaction_required         = 0
        status                     = "active"
        provenance                 = "ai_assisted"
        ai_validation_state        = "ai_uncertain"
        ai_confidence              = $null
        canonical_validation_state = "unverified"
        human_review_required      = 0
        review_queue               = $null
        review_reason              = $null
        collections_json           = "[]"
        tags_json                  = "[]"
        relations_json             = "[]"
        content_flags_json         = "[]"
        audience_suitability       = "unknown"
        export_to_uckk             = "no"
        export_to_public           = "no"
        export_policy_note         = $null
        import_batch               = $null
        notes                      = $null
    }
}

function Get-KoaLibraryRowColumns {
    [CmdletBinding()]
    param()

    return @(
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
        "notes"
    )
}

function ConvertTo-KoaLibraryRowData {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [hashtable] $Metadata,

        [Parameter(Mandatory)]
        [hashtable] $FileFacts,

        [string] $StoragePath = $null,

        [string] $ImportBatch = $null
    )

    $defaults = Get-KoaLibraryRowColumnDefaults
    $row = [ordered]@{}

    foreach ($key in $defaults.Keys) {
        $row[$key] = $defaults[$key]
    }

    foreach ($key in $Metadata.Keys) {
        if ($key -in @("collections", "tags", "relations", "content_flags")) {
            continue
        }

        if ($key -in @("filename", "extension", "mimetype", "filesize", "sha256", "original_path", "storage_path")) {
            continue
        }

        $row[$key] = $Metadata[$key]
    }

    $row["media_uuid"] = if ($Metadata.ContainsKey("media_uuid") -and -not [string]::IsNullOrWhiteSpace([string] $Metadata["media_uuid"])) { [string] $Metadata["media_uuid"] } else { New-KoaUuid }
    $row["version_uuid"] = if ($Metadata.ContainsKey("version_uuid") -and -not [string]::IsNullOrWhiteSpace([string] $Metadata["version_uuid"])) { [string] $Metadata["version_uuid"] } else { New-KoaUuid }

    $row["original_path"] = $FileFacts["original_path"]
    $row["filename"] = $FileFacts["filename"]
    $row["extension"] = $FileFacts["extension"]
    $row["mimetype"] = $FileFacts["mimetype"]
    $row["filesize"] = $FileFacts["filesize"]
    $row["sha256"] = $FileFacts["sha256"]
    $row["storage_path"] = $StoragePath
    $row["import_batch"] = $ImportBatch

    $row["collections_json"] = if ($Metadata.ContainsKey("collections")) { ConvertTo-KoaJsonArrayText -Value $Metadata["collections"] } else { "[]" }
    $row["tags_json"] = if ($Metadata.ContainsKey("tags")) { ConvertTo-KoaJsonArrayText -Value $Metadata["tags"] } else { "[]" }
    $row["relations_json"] = if ($Metadata.ContainsKey("relations")) { ConvertTo-KoaJsonArrayText -Value $Metadata["relations"] } else { "[]" }
    $row["content_flags_json"] = if ($Metadata.ContainsKey("content_flags")) { ConvertTo-KoaJsonArrayText -Value $Metadata["content_flags"] } else { "[]" }

    if ($row["rights_status"] -eq "unknown" -or $row["source_type"] -eq "unknown") {
        $row["human_review_required"] = 1
    }

    return $row
}

function Convert-KoaObjectToHashtable {
    [CmdletBinding()]
    param(
        [AllowNull()]
        [object] $InputObject
    )

    if ($null -eq $InputObject) {
        return @{}
    }

    if ($InputObject -is [hashtable]) {
        return $InputObject
    }

    $hash = @{}
    foreach ($property in $InputObject.PSObject.Properties) {
        $hash[$property.Name] = $property.Value
    }

    return $hash
}

function Join-KoaSqlInsert {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $TableName,

        [Parameter(Mandatory)]
        [hashtable] $Data
    )

    $columns = @($Data.Keys)
    $columnSql = ($columns | ForEach-Object { '"' + $_ + '"' }) -join ", "
    $valueSql = ($columns | ForEach-Object { ConvertTo-KoaSqlLiteral -Value $Data[$_] }) -join ", "

    return "INSERT INTO `"$TableName`" ($columnSql) VALUES ($valueSql);"
}

function Join-KoaSqlUpdate {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $TableName,

        [Parameter(Mandatory)]
        [hashtable] $Data,

        [Parameter(Mandatory)]
        [string] $WhereSql
    )

    $assignments = @()

    foreach ($key in $Data.Keys) {
        $assignments += ('"' + $key + '" = ' + (ConvertTo-KoaSqlLiteral -Value $Data[$key]))
    }

    $assignmentSql = $assignments -join ", "
    return "UPDATE `"$TableName`" SET $assignmentSql WHERE $WhereSql;"
}

function Write-KoaUnhandledError {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $Operation,

        [Parameter(Mandatory)]
        [System.Management.Automation.ErrorRecord] $ErrorRecord
    )

    $result = New-KoaOperationResult `
        -Success $false `
        -Operation $Operation `
        -Result "failed" `
        -Errors @(
            New-KoaMessage `
                -Code "ERR_UNHANDLED" `
                -Severity "blocking" `
                -Message $ErrorRecord.Exception.Message
        )

    Write-KoaJsonResult -Result $result
}

Set-Alias -Name Normalize-KoaMetadataObject -Value ConvertTo-KoaNormalizedMetadata

Export-ModuleMember -Function `
    Get-KoaTimestamp, `
    New-KoaUuid, `
    New-KoaMessage, `
    New-KoaOperationResult, `
    ConvertTo-KoaJsonResult, `
    Write-KoaJsonResult, `
    ConvertFrom-KoaJsonText, `
    Resolve-KoaRootPath, `
    Resolve-KoaContentRoot, `
    Test-KoaDbPath, `
    Get-KoaSqliteCommand, `
    Open-KoaSqliteConnection, `
    ConvertTo-KoaSqlLiteral, `
    Expand-KoaSqlParameters, `
    Invoke-KoaSqliteNonQuery, `
    Invoke-KoaSqliteQuery, `
    Invoke-KoaSqliteScalar, `
    Get-KoaSha256, `
    Get-KoaMimeType, `
    Get-KoaFileFacts, `
    Test-KoaAllowedValue, `
    Get-KoaEnumValuesForField, `
    ConvertTo-KoaNormalizedMetadata, `
    Test-KoaMetadataJson, `
    ConvertTo-KoaJsonArrayText, `
    ConvertFrom-KoaJsonArrayText, `
    ConvertTo-KoaSafeFilenamePart, `
    Backup-KoaDatabase, `
    Get-KoaLibraryRowColumnDefaults, `
    Get-KoaLibraryRowColumns, `
    ConvertTo-KoaLibraryRowData, `
    Convert-KoaObjectToHashtable, `
    Join-KoaSqlInsert, `
    Join-KoaSqlUpdate, `
    Write-KoaUnhandledError

Export-ModuleMember -Alias Normalize-KoaMetadataObject
