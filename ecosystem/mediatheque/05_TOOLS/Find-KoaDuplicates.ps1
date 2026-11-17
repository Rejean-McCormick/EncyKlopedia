# 05_TOOLS/Find-KoaDuplicates.ps1
# Médiathèque kOA — Find duplicate library_rows records by sha256
# PowerShell 7 only. Emits one JSON result to stdout.

#requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $DbPath,

    [Parameter(Mandatory)]
    [string] $Sha256,

    [switch] $IncludeDeletedSoft
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Operation = "Find-KoaDuplicates"

$CommonModulePath = Join-Path $PSScriptRoot "KoaMediatheque.Common.psm1"

if (-not (Test-Path -LiteralPath $CommonModulePath -PathType Leaf)) {
    $fallback = [ordered]@{
        success      = $false
        operation    = $Operation
        result       = "failed"
        entity_type  = "library_row"
        entity_uuid  = ""
        version_uuid = ""
        media_uuid   = ""
        path         = $DbPath
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

function Normalize-KoaSha256Input {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $Value
    )

    $normalized = $Value.Trim().ToLowerInvariant()

    if ($normalized -notmatch "^[a-f0-9]{64}$") {
        throw "Sha256 must be a 64-character lowercase or uppercase hexadecimal SHA-256 hash."
    }

    return $normalized
}

function Get-KoaRowsBySha256 {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object] $Connection,

        [Parameter(Mandatory)]
        [string] $Sha256Value,

        [switch] $IncludeDeleted
    )

    $where = "sha256 = @sha256"

    if (-not $IncludeDeleted) {
        $where = "$where AND status <> 'deleted_soft'"
    }

    $sql = @"
SELECT
    id,
    media_uuid,
    version_uuid,
    title,
    subtitle,
    filename,
    extension,
    mimetype,
    filesize,
    sha256,
    original_path,
    storage_path,
    filearea,
    media_type,
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
    status,
    provenance,
    ai_validation_state,
    canonical_validation_state,
    human_review_required,
    audience_suitability,
    export_to_uckk,
    export_to_public,
    import_batch,
    created_at,
    updated_at
FROM library_rows
WHERE $where
ORDER BY media_uuid, version_uuid, id;
"@

    return @(
        Invoke-KoaSqliteQuery `
            -Connection $Connection `
            -Sql $sql `
            -Parameters @{ sha256 = $Sha256Value } `
            -ReadOnly
    )
}

function Group-KoaDuplicateRows {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object[]] $Rows
    )

    if ($Rows.Count -eq 0) {
        return @()
    }

    $rowsByMediaUuid = @{}

    foreach ($row in $Rows) {
        $mediaUuid = [string] $row.media_uuid

        if ([string]::IsNullOrWhiteSpace($mediaUuid)) {
            $mediaUuid = "_missing_media_uuid"
        }

        if (-not $rowsByMediaUuid.ContainsKey($mediaUuid)) {
            $rowsByMediaUuid[$mediaUuid] = @()
        }

        $rowsByMediaUuid[$mediaUuid] = @($rowsByMediaUuid[$mediaUuid]) + $row
    }

    $groups = @()

    foreach ($mediaUuid in ($rowsByMediaUuid.Keys | Sort-Object)) {
        $groupRows = @($rowsByMediaUuid[$mediaUuid])

        $groups += [ordered]@{
            media_uuid = $mediaUuid
            row_count  = $groupRows.Count
            rows       = $groupRows
        }
    }

    return @($groups)
}

function Get-KoaDuplicateAssessment {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object[]] $Rows
    )

    if ($Rows.Count -eq 0) {
        return [ordered]@{
            duplicate_state = "no_rows"
            is_duplicate    = $false
            explanation     = "No library_rows record has this sha256."
        }
    }

    if ($Rows.Count -eq 1) {
        return [ordered]@{
            duplicate_state = "single_row"
            is_duplicate    = $false
            explanation     = "Exactly one library_rows record has this sha256."
        }
    }

    $mediaUuids = @(
        $Rows |
            ForEach-Object { [string] $_.media_uuid } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
            Sort-Object -Unique
    )

    $versionUuids = @(
        $Rows |
            ForEach-Object { [string] $_.version_uuid } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
            Sort-Object -Unique
    )

    $sameMediaUuid = ($mediaUuids.Count -eq 1)

    return [ordered]@{
        duplicate_state        = if ($sameMediaUuid) { "same_media_multiple_versions" } else { "cross_media_duplicate" }
        is_duplicate           = $true
        explanation            = if ($sameMediaUuid) {
            "Multiple rows share the same sha256 and media_uuid; this may be duplicate versioning or a repeated import."
        }
        else {
            "Multiple rows share the same sha256 across different media_uuid values; this is likely an exact file duplicate."
        }
        media_uuid_count       = $mediaUuids.Count
        version_uuid_count     = $versionUuids.Count
        media_uuids            = $mediaUuids
        version_uuids          = $versionUuids
    }
}

try {
    $warnings = @()
    $errors = @()

    Test-KoaDbPath -DbPath $DbPath -ThrowOnMissing | Out-Null

    $normalizedSha256 = Normalize-KoaSha256Input -Value $Sha256
    $connection = Open-KoaSqliteConnection -DbPath $DbPath

    $rows = Get-KoaRowsBySha256 `
        -Connection $connection `
        -Sha256Value $normalizedSha256 `
        -IncludeDeleted:$IncludeDeletedSoft

    $assessment = Get-KoaDuplicateAssessment -Rows $rows
    $groups = Group-KoaDuplicateRows -Rows $rows

    if ($assessment.is_duplicate) {
        $warnings += New-KoaMessage `
            -Code "WARN_DUPLICATE_SHA256" `
            -Severity "warning" `
            -Message "Multiple library_rows records have the same sha256." `
            -Field "sha256" `
            -Details @{
                sha256    = $normalizedSha256
                row_count = $rows.Count
            }
    }

    $resultName = if ($assessment.is_duplicate) {
        "duplicates_found"
    }
    elseif ($rows.Count -eq 1) {
        "no_duplicates"
    }
    else {
        "no_rows"
    }

    $firstVersionUuid = ""
    $firstMediaUuid = ""

    if ($rows.Count -gt 0) {
        $firstVersionUuid = [string] $rows[0].version_uuid
        $firstMediaUuid = [string] $rows[0].media_uuid
    }

    $result = New-KoaOperationResult `
        -Success $true `
        -Operation $Operation `
        -Result $resultName `
        -EntityType "library_row" `
        -EntityUuid $normalizedSha256 `
        -VersionUuid $firstVersionUuid `
        -MediaUuid $firstMediaUuid `
        -Path $DbPath `
        -Data @{
            db_path              = $DbPath
            sha256               = $normalizedSha256
            include_deleted_soft = [bool] $IncludeDeletedSoft
            row_count            = $rows.Count
            assessment           = $assessment
            groups               = $groups
            rows                 = $rows
        } `
        -Warnings $warnings `
        -Errors @()

    Write-KoaJsonResult -Result $result
    exit 0
}
catch {
    $errorResult = New-KoaOperationResult `
        -Success $false `
        -Operation $Operation `
        -Result "failed" `
        -EntityType "library_row" `
        -EntityUuid $Sha256 `
        -Path $DbPath `
        -Errors @(
            New-KoaMessage `
                -Code "ERR_FIND_DUPLICATES_FAILED" `
                -Severity "blocking" `
                -Message $_.Exception.Message
        )

    Write-KoaJsonResult -Result $errorResult
    exit 1
}