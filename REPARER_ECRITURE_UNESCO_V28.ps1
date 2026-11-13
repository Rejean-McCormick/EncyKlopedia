[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$script = Join-Path $repo 'tools\unesco_pilot\reparer_ecriture_catalogue_v25.py'
$catalogue = 'D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite'
$backup = 'D:\EncyKlopedia\30_working\SAUVEGARDE_CATALOGUE_V25_RESTAURE'

Write-Host "`n=== REPRISE IMPORT UNESCO V28 : CONTROLE DU CATALOGUE ===" -ForegroundColor Cyan
if (-not (Test-Path -LiteralPath $script -PathType Leaf)) { throw "Script de reparation absent : $script" }
if (-not (Test-Path -LiteralPath $catalogue -PathType Leaf)) { throw "Catalogue v25 absent : $catalogue" }

# Avoid repairing a live SQLite database. Database content and v30 state never reset.
$running = @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
    ($_.CommandLine -match 'poste_chatgpt_v30\.py|decouvrir_articles_relies_v28\.py') -and
    ($_.ProcessId -ne $PID)
})
if ($running.Count -gt 0) {
    Write-Host 'REFUS : un moteur EncyKlopedia v30/v28 est encore actif. Ferme la fenetre du poste v30 avant de lancer cette commande.' -ForegroundColor Yellow
    $running | Select-Object ProcessId, Name, CommandLine | Format-Table -AutoSize -Wrap
    exit 2
}

Write-Host "`n=== ATTRIBUTS DES FICHIERS V25 ===" -ForegroundColor Cyan
foreach ($suffix in @('', '-wal', '-shm')) {
    $p = $catalogue + $suffix
    if (Test-Path -LiteralPath $p -PathType Leaf) {
        $f = Get-Item -LiteralPath $p -Force
        Write-Host "$($f.Name) / $($f.Length) octets / LectureSeule=$($f.IsReadOnly)"
        & icacls $p
    }
}

$python = $null
foreach ($candidate in @(Get-Command -Name python.exe -CommandType Application -All -ErrorAction SilentlyContinue)) {
    $path = [string]$candidate.Source
    if (-not $path -or $path -match '\\WindowsApps\\') { continue }
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
    try {
        & $path -I -c 'import sqlite3,sys;raise SystemExit(0 if sys.version_info >= (3,11) else 1)' *> $null
        if ($LASTEXITCODE -eq 0) { $python = $path; break }
    } catch { }
}
if (-not $python) { throw 'Python 3.11+ introuvable; reparation non executee' }
Write-Host "`nPython : $python" -ForegroundColor Cyan
& $python -I $script --catalogue $catalogue --backup-root $backup
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nFIN : aucun changement du catalogue si la reparation n'a pas ete confirmee. Voir le diagnostic ci-dessus." -ForegroundColor Yellow
    exit $LASTEXITCODE
}
Write-Host "`nFIN : diagnostic/reparation termine. Aucune base de travail v27/v28/v30 n'a ete reinitialisee." -ForegroundColor Green
exit 0
