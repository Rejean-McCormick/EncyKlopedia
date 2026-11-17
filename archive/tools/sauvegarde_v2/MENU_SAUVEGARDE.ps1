param([switch]$Verifier)
$ErrorActionPreference = 'Stop'
$engine = Join-Path $PSScriptRoot 'encyk_sauvegarde.py'
function Get-Python311 {
    foreach ($candidate in @('python.exe', 'python3.exe')) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        $path=[string]$cmd.Source
        if ($path -match 'WindowsApps') { continue }
        try {
            & $path -I -c 'import sys,sqlite3;raise SystemExit(0 if sys.version_info >= (3,11) else 1)' 2>$null
            if ($LASTEXITCODE -eq 0) { return $path }
        } catch { continue }
    }
    # Chemin Python 3.12 connu dans la station, sans l'imposer a tous.
    $known=Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
    if (Test-Path -LiteralPath $known -PathType Leaf) { return $known }
    throw 'Python 3.11+ introuvable.'
}
try {
    $python = Get-Python311
    if ($Verifier) {
        $folder = (Read-Host 'Dossier ENCYK_RESULTATS_... a verifier').Trim('"')
        & $python -I $engine verify --backup-dir $folder
        exit $LASTEXITCODE
    }
    Write-Host ''
    Write-Host '========== ENCYKLOPEDIA - SAUVEGARDE DES RESULTATS v3 ==========' -ForegroundColor Cyan
    Write-Host '1 : Resultats (bases SQLite uniquement, recommande)'
    Write-Host '2 : Resultats + inventaire des categories derive (volume plus grand)'
    Write-Host '3 : Precontrole seul, sans creer de copie'
    $choice = Read-Host 'Choix [1]'
    if (-not $choice) { $choice='1' }
    if ($choice -notin @('1','2','3')) { throw 'Choix invalide.' }
    $source = Read-Host 'Racine des donnees [D:\EncyKlopedia]'
    if (-not $source) { $source='D:\EncyKlopedia' }
    $out = Read-Host 'Destination [D:\EncyKlopedia_SAUVEGARDES]'
    if (-not $out) { $out='D:\EncyKlopedia_SAUVEGARDES' }
    $argv = @('--data-root',$source,'--destination',$out)
    if ($choice -eq '2') { $argv += '--avec-index-derive' }
    if ($choice -eq '3') {
        & $python -I $engine preflight @argv
        exit $LASTEXITCODE
    }
    Write-Host ''
    Write-Host 'FERMER COMPLETEMENT la station et tous les producteurs/importateurs.' -ForegroundColor Yellow
    Write-Host 'L outil n inclut NI code, NI pack, NI retour, NI XML, NI fichier de travail.'
    $confirm = Read-Host 'Confirmer leur fermeture en tapant OUI'
    if ($confirm -cne 'OUI') { throw 'Operation annulee.' }
    & $python -I $engine backup @argv --station-fermee
    exit $LASTEXITCODE
} catch {
    Write-Host "SAUVEGARDE REFUSEE : $($_.Exception.Message)" -ForegroundColor Red
    exit 2
}
