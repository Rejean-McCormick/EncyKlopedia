[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
try {
    $root = Split-Path -Parent $MyInvocation.MyCommand.Path
    $engine = Join-Path $root 'tools\unesco_pilot\stabiliser_catalogue_import_v28.py'
    $python = 'C:\Users\rejea\AppData\Local\Programs\Python\Python312\python.exe'
    if (-not (Test-Path -LiteralPath $engine -PathType Leaf)) { throw "Moteur de stabilisation manquant : $engine" }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw "Python absent : $python" }
    $running = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" -ErrorAction Stop |
        Where-Object { $_.CommandLine -match 'poste_chatgpt_v30\.py|decouvrir_articles_relies_v28\.py|catalogue_global_v25\.py' })
    if ($running.Count -gt 0) {
        Write-Host 'REFUS : traitement EncyKlopedia actif. Fermer sa console de lancement.' -ForegroundColor Red
        $running | Select-Object ProcessId,Name,CommandLine | Format-Table -Wrap
        exit 2
    }
    Write-Host 'Poste v30 ferme requis. Tests par INSERT + ROLLBACK, sauvegarde avant toute intervention.' -ForegroundColor Cyan
    & $python -I $engine
    if ($LASTEXITCODE -ne 0) { throw "Stabilisation non terminee (code $LASTEXITCODE). Aucun reimport automatique." }
    Write-Host '=== DIAGNOSTIC/STABILISATION TERMINE ===' -ForegroundColor Green
    exit 0
}
catch {
    Write-Host "STABILISATION NON TERMINEE : $($_.Exception.Message)" -ForegroundColor Red
    exit 2
}
