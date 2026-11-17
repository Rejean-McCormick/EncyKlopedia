# 05_TOOLS/Backup-KoaMediathequeDb.ps1
# Médiathèque kOA — Backup SQLite database
# PowerShell 7 only. Emits exactly one JSON result to stdout.

#requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $DbPath,

    [Parameter(Mandatory)]
    [string] $BackupDir,

    [string] $Reason = "manual"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Operation = "Backup-KoaMediathequeDb"

function New-KoaLocalUuid {
    return [guid]::NewGuid().ToString()
}

function Get-KoaLocalTimestamp {
    return [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function New-KoaLocalMessage {
    param(
        [Parameter(Mandatory)]
        [string] $Code,

        [Parameter(Mandatory)]
        [ValidateSet("info", "warning", "error", "blocking")]
        [string] $Severity,

        [Parameter(Mandatory)]
        [string] $Message,

        [AllowNull()]
        [string] $Field = $null,

        [AllowNull()]
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

function New-KoaLocalResult {
    param(
        [Parameter(Mandatory)]
        [bool] $Success,

        [Parameter(Mandatory)]
        [string] $Result,

        [string] $EntityType = "backup",

        [string] $EntityUuid = "",

        [string] $Path = "",

        [hashtable] $Data = @{},

        [object[]] $Warnings = @(),

        [object[]] $Errors = @()
    )

    return [ordered]@{
        success      = $Success
        operation    = $Operation
        result       = $Result
        entity_type  = $EntityType
        entity_uuid  = $EntityUuid
        version_uuid = ""
        media_uuid   = ""
        path         = $Path
        data         = $Data
        warnings     = @($Warnings)
        errors       = @($Errors)
    }
}

function Write-KoaLocalJsonResult {
    param(
        [Parameter(Mandatory)]
        [object] $Result
    )

    [Console]::Out.WriteLine(($Result | ConvertTo-Json -Depth 100 -Compress))
}

function ConvertTo-KoaSafeReason {
    param(
        [AllowNull()]
        [string] $Value
    )

    $text = ""

    if ($null -ne $Value) {
        $text = $Value.Trim()
    }

    if ([string]::IsNullOrWhiteSpace($text)) {
        $text = "manual"
    }

    $text = $text.ToLowerInvariant()
    $text = $text -replace "[^a-z0-9]+", "_"
    $text = $text -replace "_+", "_"
    $text = $text.Trim("_")

    if ([string]::IsNullOrWhiteSpace($text)) {
        return "manual"
    }

    return $text
}

function Get-KoaBackupPath {
    param(
        [Parameter(Mandatory)]
        [string] $TargetDir,

        [Parameter(Mandatory)]
        [string] $SafeReason
    )

    $timestamp = [DateTime]::UtcNow.ToString("yyyyMMdd_HHmmss")
    $baseName = "koa_mediatheque_${timestamp}_${SafeReason}"
    $candidate = Join-Path $TargetDir "$baseName.sqlite"

    if (-not (Test-Path -LiteralPath $candidate)) {
        return $candidate
    }

    for ($index = 1; $index -le 999; $index++) {
        $suffix = "{0:D2}" -f $index
        $candidate = Join-Path $TargetDir "${baseName}_${suffix}.sqlite"

        if (-not (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }

    throw "Unable to generate unique backup filename in: $TargetDir"
}

function Get-KoaLocalSha256 {
    param(
        [Parameter(Mandatory)]
        [string] $FilePath
    )

    if (-not (Test-Path -LiteralPath $FilePath -PathType Leaf)) {
        throw "Cannot hash missing file: $FilePath"
    }

    $stream = [System.IO.File]::OpenRead($FilePath)
    $sha = $null

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

function Get-KoaPythonCommand {
    foreach ($candidate in @("python", "python3", "py")) {
        try {
            $output = & $candidate --version 2>&1

            if ($LASTEXITCODE -eq 0 -and $output) {
                return $candidate
            }
        }
        catch {
            continue
        }
    }

    return $null
}

function Invoke-KoaPythonNoStdout {
    param(
        [Parameter(Mandatory)]
        [string] $Code,

        [string[]] $Arguments = @()
    )

    $python = Get-KoaPythonCommand

    if ([string]::IsNullOrWhiteSpace($python)) {
        throw "Python was not found."
    }

    $tempScript = Join-Path ([System.IO.Path]::GetTempPath()) (
        "koa_backup_" + [guid]::NewGuid().ToString("N") + ".py"
    )

    try {
        $Code | Set-Content -LiteralPath $tempScript -Encoding UTF8

        $output = & $python $tempScript @Arguments 2>&1
        $exitCode = $LASTEXITCODE

        if ($exitCode -ne 0) {
            $text = ($output | Out-String).Trim()
            throw "Python helper failed with exit code $exitCode. Output: $text"
        }
    }
    finally {
        if (Test-Path -LiteralPath $tempScript -PathType Leaf) {
            Remove-Item -LiteralPath $tempScript -Force -ErrorAction SilentlyContinue
        }
    }
}

function Add-KoaBackupAuditLog {
    param(
        [Parameter(Mandatory)]
        [string] $DatabasePath,

        [Parameter(Mandatory)]
        [string] $BackupUuid,

        [Parameter(Mandatory)]
        [hashtable] $BackupPayload,

        [Parameter(Mandatory)]
        [string] $SafeReason
    )

    $payloadJson = $BackupPayload | ConvertTo-Json -Depth 100 -Compress
    $payloadBase64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($payloadJson))

    $code = @'
from __future__ import annotations

import base64
import json
import sqlite3
import sys
from pathlib import Path

db_path = Path(sys.argv[1])
backup_uuid = sys.argv[2]
payload = json.loads(base64.b64decode(sys.argv[3]).decode("utf-8"))
reason = sys.argv[4]

connection = sqlite3.connect(str(db_path))

try:
    has_audit_log = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'audit_log' LIMIT 1"
    ).fetchone()

    if not has_audit_log:
        sys.exit(0)

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
            "backup_created",
            "backup",
            backup_uuid,
            None,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            "local_user",
            f"Backup-KoaMediathequeDb.ps1 Reason={reason}",
        ),
    )

    connection.commit()
finally:
    connection.close()
'@

    Invoke-KoaPythonNoStdout `
        -Code $code `
        -Arguments @(
            $DatabasePath,
            $BackupUuid,
            $payloadBase64,
            $SafeReason
        )
}

try {
    if ([string]::IsNullOrWhiteSpace($BackupDir)) {
        $result = New-KoaLocalResult `
            -Success $false `
            -Result "backup_dir_required" `
            -Path $BackupDir `
            -Errors @(
                New-KoaLocalMessage `
                    -Code "ERR_REQUIRED_FIELD" `
                    -Severity "blocking" `
                    -Message "BackupDir is required." `
                    -Field "BackupDir"
            )

        Write-KoaLocalJsonResult -Result $result
        exit 1
    }

    if ([string]::IsNullOrWhiteSpace($DbPath)) {
        $result = New-KoaLocalResult `
            -Success $false `
            -Result "db_path_required" `
            -Path $DbPath `
            -Errors @(
                New-KoaLocalMessage `
                    -Code "ERR_REQUIRED_FIELD" `
                    -Severity "blocking" `
                    -Message "DbPath is required." `
                    -Field "DbPath"
            )

        Write-KoaLocalJsonResult -Result $result
        exit 1
    }

    $resolvedDbPath = [System.IO.Path]::GetFullPath($DbPath)
    $resolvedBackupDir = [System.IO.Path]::GetFullPath($BackupDir)
    $safeReason = ConvertTo-KoaSafeReason -Value $Reason

    if (-not (Test-Path -LiteralPath $resolvedDbPath -PathType Leaf)) {
        $result = New-KoaLocalResult `
            -Success $false `
            -Result "db_not_found" `
            -Path $resolvedDbPath `
            -Errors @(
                New-KoaLocalMessage `
                    -Code "ERR_DB_NOT_FOUND" `
                    -Severity "blocking" `
                    -Message "SQLite database not found: $resolvedDbPath" `
                    -Field "DbPath"
            )

        Write-KoaLocalJsonResult -Result $result
        exit 1
    }

    if (-not (Test-Path -LiteralPath $resolvedBackupDir -PathType Container)) {
        New-Item -ItemType Directory -Path $resolvedBackupDir -Force | Out-Null
    }

    $backupUuid = New-KoaLocalUuid

    $backupPath = Get-KoaBackupPath `
        -TargetDir $resolvedBackupDir `
        -SafeReason $safeReason

    Copy-Item `
        -LiteralPath $resolvedDbPath `
        -Destination $backupPath `
        -Force

    if (-not (Test-Path -LiteralPath $backupPath -PathType Leaf)) {
        $result = New-KoaLocalResult `
            -Success $false `
            -Result "backup_failed" `
            -EntityUuid $backupUuid `
            -Path $resolvedBackupDir `
            -Errors @(
                New-KoaLocalMessage `
                    -Code "ERR_BACKUP_FAILED" `
                    -Severity "blocking" `
                    -Message "Backup copy did not create the expected file." `
                    -Field "backup_path" `
                    -Details @{ backup_path = $backupPath }
            )

        Write-KoaLocalJsonResult -Result $result
        exit 1
    }

    $backupItem = Get-Item -LiteralPath $backupPath
    $backupSha256 = Get-KoaLocalSha256 -FilePath $backupItem.FullName

    $backupPayload = @{
        backup_uuid   = $backupUuid
        db_path       = $resolvedDbPath
        backup_dir    = $resolvedBackupDir
        backup_path   = $backupItem.FullName
        backup_sha256 = $backupSha256
        filesize      = [int64] $backupItem.Length
        reason        = $safeReason
        created_at    = Get-KoaLocalTimestamp
    }

    $warnings = @(
        New-KoaLocalMessage `
            -Code "INFO_BACKUP_CREATED" `
            -Severity "info" `
            -Message "Backup created successfully." `
            -Field "backup_path" `
            -Details @{ backup_path = $backupItem.FullName }
    )

    $errors = @()

    try {
        Add-KoaBackupAuditLog `
            -DatabasePath $resolvedDbPath `
            -BackupUuid $backupUuid `
            -BackupPayload $backupPayload `
            -SafeReason $safeReason
    }
    catch {
        $warnings += New-KoaLocalMessage `
            -Code "WARN_AUDIT_LOG_FAILED" `
            -Severity "warning" `
            -Message "Backup was created but audit_log could not be written: $($_.Exception.Message)" `
            -Field "audit_log"
    }

    $result = New-KoaLocalResult `
        -Success $true `
        -Result "created_by_copy" `
        -EntityUuid $backupUuid `
        -Path $backupItem.FullName `
        -Data $backupPayload `
        -Warnings $warnings `
        -Errors $errors

    Write-KoaLocalJsonResult -Result $result
    exit 0
}
catch {
    $result = New-KoaLocalResult `
        -Success $false `
        -Result "failed" `
        -Path $BackupDir `
        -Errors @(
            New-KoaLocalMessage `
                -Code "ERR_BACKUP_FAILED" `
                -Severity "blocking" `
                -Message $_.Exception.Message
        )

    Write-KoaLocalJsonResult -Result $result
    exit 1
}