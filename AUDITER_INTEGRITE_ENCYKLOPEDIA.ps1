# AUDIT ENCYKLOPEDIA — lecture seule des fichiers et des bases SQLite
# Utilisation (apres extraction de l'overlay dans la racine du depot) :
# pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\mycode\EncyKlopedia\EncyKlopedia\AUDITER_INTEGRITE_ENCYKLOPEDIA.ps1"
$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot
$data = 'D:\EncyKlopedia'
$scanner = Join-Path $repo 'tools\unesco_pilot\audit_integrite_encyklopedia.py'
if (-not (Test-Path -LiteralPath $scanner -PathType Leaf)) {
    throw "Programme d'audit introuvable : $scanner. Extraire toutes les entrees du ZIP dans la racine du depot."
}
if (-not (Test-Path -LiteralPath $data -PathType Container)) {
    throw "Repertoire de donnees introuvable : $data"
}
$dest = Join-Path ([IO.Path]::GetTempPath()) ('EncyKlopedia_Audit_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $dest -Force | Out-Null
Write-Host "`nAudit de D:\EncyKlopedia et du depot EncyKlopedia" -ForegroundColor Cyan
Write-Host "Les rapports seront enregistres sous : $dest" -ForegroundColor Cyan
Write-Host "Ne pas relancer le poste v30 pendant l'audit." -ForegroundColor Yellow

$py = Get-Command 'py' -ErrorAction SilentlyContinue | Select-Object -First 1
$python = Get-Command 'python' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($py) {
    & $py.Source '-3' $scanner '--data' $data '--repo' $repo '--output' $dest
} elseif ($python) {
    & $python.Source $scanner '--data' $data '--repo' $repo '--output' $dest
} else {
    throw 'Python 3 introuvable (ni py ni python). Aucun scan SQLite effectue.'
}
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Audit incomplet (code Python : $LASTEXITCODE). Voir les messages ci-dessus."
    exit $LASTEXITCODE
}
Write-Host "`nRAPPORT TEXTE : $(Join-Path $dest 'rapport_integrite_encyklopedia.txt')" -ForegroundColor Green
Write-Host "RAPPORT JSON  : $(Join-Path $dest 'rapport_integrite_encyklopedia.json')" -ForegroundColor Green
