#requires -Version 7.0
<#
.SYNOPSIS
Starts the Médiathèque kOA Streamlit GUI.

.DESCRIPTION
Bootstrap launcher for the local Médiathèque kOA GUI.

Responsibilities:
- Resolve the project root.
- Verify Python is available.
- Create .venv if missing.
- Install/update GUI requirements when needed.
- Verify the Streamlit app entrypoint exists.
- Launch Streamlit against 06_GUI/koa_mediatheque_gui/app.py.

This script does not initialize the SQLite database and does not write
business records. Database/schema operations belong to 05_TOOLS scripts.
#>

[CmdletBinding()]
param(
    [string]$RootPath = "",

    [string]$ContentPath = "",

    [string]$PythonCommand = "python",

    [string]$HostName = "",

    [int]$Port = 0,

    [switch]$NoInstall,

    [switch]$ForceInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-KoaInfo {
    param([string]$Message)
    Write-Host "[kOA] $Message" -ForegroundColor Cyan
}

function Write-KoaWarn {
    param([string]$Message)
    Write-Host "[kOA] WARNING: $Message" -ForegroundColor Yellow
}

function Write-KoaError {
    param([string]$Message)
    Write-Host "[kOA] ERROR: $Message" -ForegroundColor Red
}

function Resolve-KoaRoot {
    param([string]$CandidateRoot)

    if (-not [string]::IsNullOrWhiteSpace($CandidateRoot)) {
        $resolved = Resolve-Path -LiteralPath $CandidateRoot -ErrorAction Stop
        return $resolved.Path
    }

    $scriptDir = Split-Path -Parent $PSCommandPath
    return (Resolve-Path -LiteralPath $scriptDir -ErrorAction Stop).Path
}

function Resolve-KoaContentRoot {
    param(
        [string]$AppRoot,
        [string]$CandidateContent
    )

    if (-not [string]::IsNullOrWhiteSpace($CandidateContent)) {
        return [System.IO.Path]::GetFullPath($CandidateContent)
    }

    if (-not [string]::IsNullOrWhiteSpace($env:KOA_CONTENT_ROOT)) {
        return [System.IO.Path]::GetFullPath($env:KOA_CONTENT_ROOT)
    }

    return [System.IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $AppRoot) "content"))
}

function Test-KoaPython {
    param([string]$Command)

    try {
        $versionOutput = & $Command --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Python returned exit code $LASTEXITCODE"
        }

        Write-KoaInfo "Python detected: $versionOutput"
    }
    catch {
        throw "Python was not found using command '$Command'. Install Python >= 3.11 or pass -PythonCommand."
    }
}

function Get-KoaVenvPython {
    param([string]$Root)

    if ($IsWindows) {
        return Join-Path $Root ".venv\Scripts\python.exe"
    }

    return Join-Path $Root ".venv/bin/python"
}

function Get-KoaVenvStreamlit {
    param([string]$Root)

    if ($IsWindows) {
        return Join-Path $Root ".venv\Scripts\streamlit.exe"
    }

    return Join-Path $Root ".venv/bin/streamlit"
}

function Initialize-KoaVenv {
    param(
        [string]$Root,
        [string]$Command
    )

    $venvDir = Join-Path $Root ".venv"
    $venvPython = Get-KoaVenvPython -Root $Root

    if (Test-Path -LiteralPath $venvPython) {
        Write-KoaInfo "Virtual environment found: .venv"
        return
    }

    Write-KoaInfo "Creating virtual environment: .venv"
    & $Command -m venv $venvDir

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create virtual environment at '$venvDir'."
    }

    if (-not (Test-Path -LiteralPath $venvPython)) {
        throw "Virtual environment was created but Python executable was not found at '$venvPython'."
    }
}

function Install-KoaRequirements {
    param(
        [string]$Root,
        [switch]$Force
    )

    $venvPython = Get-KoaVenvPython -Root $Root
    $rootRequirements = Join-Path $Root "requirements.txt"
    $guiRequirements = Join-Path $Root "06_GUI\koa_mediatheque_gui\requirements.txt"
    $stampFile = Join-Path $Root ".venv\.koa_requirements_installed"

    if (-not (Test-Path -LiteralPath $rootRequirements)) {
        throw "Missing root requirements file: $rootRequirements"
    }

    if (-not (Test-Path -LiteralPath $guiRequirements)) {
        throw "Missing GUI requirements file: $guiRequirements"
    }

    if ((Test-Path -LiteralPath $stampFile) -and -not $Force) {
        Write-KoaInfo "Requirements already installed. Use -ForceInstall to reinstall."
        return
    }

    Write-KoaInfo "Upgrading pip"
    & $venvPython -m pip install --upgrade pip

    if ($LASTEXITCODE -ne 0) {
        throw "pip upgrade failed."
    }

    Write-KoaInfo "Installing root requirements"
    & $venvPython -m pip install -r $rootRequirements

    if ($LASTEXITCODE -ne 0) {
        throw "Root requirements installation failed."
    }

    Write-KoaInfo "Installing GUI requirements"
    & $venvPython -m pip install -r $guiRequirements

    if ($LASTEXITCODE -ne 0) {
        throw "GUI requirements installation failed."
    }

    "installed_at=$(Get-Date -Format o)" | Set-Content -LiteralPath $stampFile -Encoding UTF8
}

function Read-KoaEnvFile {
    param([string]$EnvPath)

    $values = @{}

    if (-not (Test-Path -LiteralPath $EnvPath)) {
        return $values
    }

    $lines = Get-Content -LiteralPath $EnvPath -Encoding UTF8

    foreach ($line in $lines) {
        $trimmed = $line.Trim()

        if ([string]::IsNullOrWhiteSpace($trimmed)) {
            continue
        }

        if ($trimmed.StartsWith("#")) {
            continue
        }

        $parts = $trimmed.Split("=", 2)

        if ($parts.Count -ne 2) {
            continue
        }

        $key = $parts[0].Trim()
        $value = $parts[1].Trim().Trim('"').Trim("'")

        if (-not [string]::IsNullOrWhiteSpace($key)) {
            $values[$key] = $value
        }
    }

    return $values
}

function Resolve-KoaSetting {
    param(
        [hashtable]$EnvValues,
        [string]$Name,
        [string]$DefaultValue
    )

    $processValue = [Environment]::GetEnvironmentVariable($Name, "Process")

    if (-not [string]::IsNullOrWhiteSpace($processValue)) {
        return $processValue
    }

    if ($EnvValues.ContainsKey($Name)) {
        return $EnvValues[$Name]
    }

    return $DefaultValue
}

try {
    $root = Resolve-KoaRoot -CandidateRoot $RootPath
    $contentRoot = Resolve-KoaContentRoot -AppRoot $root -CandidateContent $ContentPath
    Set-Location -LiteralPath $root

    Write-KoaInfo "Project root: $root"
    Write-KoaInfo "Content root: $contentRoot"

    $appPath = Join-Path $root "06_GUI\koa_mediatheque_gui\app.py"
    $guiDir = Join-Path $root "06_GUI\koa_mediatheque_gui"
    $envPath = Join-Path $root ".env"

    if (-not (Test-Path -LiteralPath $guiDir)) {
        throw "Missing GUI directory: $guiDir"
    }

    if (-not (Test-Path -LiteralPath $appPath)) {
        throw "Missing Streamlit app entrypoint: $appPath"
    }

    Test-KoaPython -Command $PythonCommand
    Initialize-KoaVenv -Root $root -Command $PythonCommand

    if ($NoInstall) {
        Write-KoaWarn "Skipping dependency installation because -NoInstall was provided."
    }
    else {
        Install-KoaRequirements -Root $root -Force:$ForceInstall
    }

    $streamlitExe = Get-KoaVenvStreamlit -Root $root
    $venvPython = Get-KoaVenvPython -Root $root

    if (-not (Test-Path -LiteralPath $streamlitExe)) {
        Write-KoaWarn "Streamlit executable not found directly; using python -m streamlit."
    }

    $envValues = Read-KoaEnvFile -EnvPath $envPath

    $resolvedHost = if ($HostName) {
        $HostName
    }
    else {
        Resolve-KoaSetting -EnvValues $envValues -Name "KOA_STREAMLIT_HOST" -DefaultValue "localhost"
    }

    $resolvedPort = if ($Port -gt 0) {
        $Port
    }
    else {
        [int](Resolve-KoaSetting -EnvValues $envValues -Name "KOA_STREAMLIT_PORT" -DefaultValue "8501")
    }

    $headless = Resolve-KoaSetting -EnvValues $envValues -Name "KOA_STREAMLIT_HEADLESS" -DefaultValue "true"

    $env:KOA_ROOT = $root
    $env:KOA_APP_ROOT = $root
    $env:KOA_CONTENT_ROOT = $contentRoot

    if (-not (Test-Path -LiteralPath $contentRoot -PathType Container)) {
        New-Item -ItemType Directory -Path $contentRoot -Force | Out-Null
    }

    if ([string]::IsNullOrWhiteSpace($env:KOA_DB_PATH)) {
        $env:KOA_DB_PATH = Join-Path $contentRoot "01_DB/koa_mediatheque.sqlite"
    }
    if ([string]::IsNullOrWhiteSpace($env:KOA_STORAGE_ROOT)) {
        $env:KOA_STORAGE_ROOT = Join-Path $contentRoot "02_STORAGE"
    }
    if ([string]::IsNullOrWhiteSpace($env:KOA_IMPORTS_ROOT)) {
        $env:KOA_IMPORTS_ROOT = Join-Path $contentRoot "03_IMPORTS"
    }
    if ([string]::IsNullOrWhiteSpace($env:KOA_EXPORTS_ROOT)) {
        $env:KOA_EXPORTS_ROOT = Join-Path $contentRoot "04_EXPORTS"
    }
    if ([string]::IsNullOrWhiteSpace($env:KOA_BACKUPS_ROOT)) {
        $env:KOA_BACKUPS_ROOT = Join-Path $contentRoot "07_BACKUPS"
    }
    if ([string]::IsNullOrWhiteSpace($env:KOA_LOGS_ROOT)) {
        $env:KOA_LOGS_ROOT = Join-Path $contentRoot "08_LOGS"
    }

    Write-KoaInfo "Starting Streamlit"
    Write-KoaInfo "App: $root"
    Write-KoaInfo "Content: $contentRoot"
    Write-KoaInfo "URL: http://$resolvedHost`:$resolvedPort"

    Push-Location $contentRoot
    try {
        if (Test-Path -LiteralPath $streamlitExe) {
            & $streamlitExe run $appPath `
                --server.address $resolvedHost `
                --server.port $resolvedPort `
                --server.headless $headless
        }
        else {
            & $venvPython -m streamlit run $appPath `
                --server.address $resolvedHost `
                --server.port $resolvedPort `
                --server.headless $headless
        }
    }
    finally {
        Pop-Location
    }

    exit $LASTEXITCODE
}
catch {
    Write-KoaError $_.Exception.Message
    exit 1
}