# EncyKlopedia v30 — Centre de production local. Lancement Windows, sans installation de dependances.
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
try {
    $root = Split-Path -Parent $PSCommandPath
    $engine = Join-Path $root 'tools\unesco_pilot\poste_chatgpt_v30.py'
    if (-not (Test-Path -LiteralPath $engine -PathType Leaf)) { throw 'Overlay v30 incomplet : moteur absent.' }
    $python = $null
    foreach ($candidate in @(Get-Command python.exe -CommandType Application -All -ErrorAction SilentlyContinue)) {
        $path = [string]$candidate.Source
        if (-not $path -or $path.IndexOf('\WindowsApps\',[StringComparison]::OrdinalIgnoreCase) -ge 0) { continue }
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
        try {
            & $path -I -c 'import sys,sqlite3;raise SystemExit(0 if sys.version_info >= (3,11) else 1)' *> $null
            if ($LASTEXITCODE -eq 0) { $python = $path; break }
        } catch {}
    }
    if (-not $python) { throw 'Python 3.11+ est requis. Python.exe non trouve.' }
    Write-Host 'EncyKlopedia v30 : centre de production local x10.' -ForegroundColor Cyan
    Write-Host 'Le navigateur sera ouvert sur 127.0.0.1. Garder cette fenetre PowerShell ouverte.'
    Write-Host 'Anciennes bases v27, v28 et catalogue conservees.'
    & $python -I $engine --repo $root
    if ($LASTEXITCODE -ne 0) { throw 'L interface v30 a retourne une erreur.' }
} catch {
    Write-Host "POSTE_CHATGPT_V30_REFUSE : $($_.Exception.Message)" -ForegroundColor Red
    exit 2
}
