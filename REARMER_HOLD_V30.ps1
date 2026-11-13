# EncyKlopedia v30 — Reprogrammer seulement les HOLD et les revues tout-HOLD.
[CmdletBinding()]
param([switch]$Apercu,[switch]$SansRelancer)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
try {
    $root = Split-Path -Parent $PSCommandPath
    $script = Join-Path $root 'REARMER_HOLD_V30.py'
    if (-not (Test-Path -LiteralPath $script -PathType Leaf)) {throw 'Fichier REARMER_HOLD_V30.py absent.'}
    # No database changes while the UI process is running.
    $running = @(Get-CimInstance -ClassName Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" |
        Where-Object { $_.CommandLine -match 'poste_chatgpt_v30\.py' })
    if ($running.Count -gt 0) {
        throw 'Fermer d abord le poste ChatGPT v30 et sa console PowerShell. Processus Python v30 encore actif.'
    }
    $python = $null
    foreach ($cmd in @(Get-Command python.exe -CommandType Application -All -ErrorAction SilentlyContinue)) {
        $candidate = [string]$cmd.Source
        if (-not $candidate -or $candidate -like '*\WindowsApps\*') {continue}
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {continue}
        try {
            & $candidate -I -c 'import sys, sqlite3; raise SystemExit(0 if sys.version_info >= (3,11) else 1)' *> $null
            if ($LASTEXITCODE -eq 0) {$python = $candidate;break}
        } catch {}
    }
    if (-not $python) { throw 'Python 3.11+ introuvable.' }
    Write-Host 'ENCYKLOPEDIA V30 : REARMEMENT DES HOLD UNIQUEMENT' -ForegroundColor Cyan
    $params = @($script)
    if ($Apercu) {$params += '--preview'}
    & $python -I @params
    if ($LASTEXITCODE -ne 0) { throw 'Le reset a ete refuse. Aucun nouveau demarrage.' }
    if ($Apercu) {return}
    Write-Host 'HOLD rearme. Les anciennes revues et retours sont conserves en historique.' -ForegroundColor Green
    $contexte = Join-Path $root 'tools\unesco_pilot\contexte_revue_unesco_v28.py'
    if (-not (Test-Path -LiteralPath $contexte -PathType Leaf)) {
        Write-Warning 'Enrichissement UNESCO introuvable : installer d abord le correctif Packs enrichis avant de retélécharger.'
    }
    if (-not $SansRelancer) {
        Write-Host 'Redemarrage du poste v30...' -ForegroundColor Cyan
        & (Join-Path $root 'LANCER_POSTE_CHATGPT_V30.ps1')
        if ($LASTEXITCODE -ne 0) {throw 'Lancement du poste v30 refuse.'}
    }
} catch {
    Write-Host "REARMEMENT_REFUSE : $($_.Exception.Message)" -ForegroundColor Red
    exit 2
}
