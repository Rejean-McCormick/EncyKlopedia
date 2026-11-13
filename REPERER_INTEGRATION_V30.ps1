# Diagnostic de l'emplacement où la présélection doit être connectée au générateur v28.
param(
  [string]$Depot = 'C:\mycode\EncyKlopedia\EncyKlopedia',
  [string]$Sortie = (Join-Path $env:TEMP 'POINTS_INSERTION_V30.txt'),
  [string]$Python = 'C:\Users\rejea\AppData\Local\Programs\Python\Python312\python.exe'
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Python)) { throw "Python introuvable : $Python" }
$script = Join-Path $PSScriptRoot 'outils_v30\reperer_integration_v30.py'
& $Python $script --repo $Depot --sortie $Sortie
if ($LASTEXITCODE -ne 0) { throw "Erreur diagnostic : $LASTEXITCODE" }
Write-Host "Fichier a transmettre pour integration exacte : $Sortie"
