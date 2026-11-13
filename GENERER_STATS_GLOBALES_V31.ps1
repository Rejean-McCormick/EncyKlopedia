param(
  [string]$Sortie = (Join-Path $HOME 'Downloads\STATS_GLOBALES_ENCYKLOPEDIA_V31'),
  [string]$Python = 'C:\Users\rejea\AppData\Local\Programs\Python\Python312\python.exe'
)
$ErrorActionPreference='Stop'
$script=Join-Path $PSScriptRoot 'tools\unesco_pilot\statistiques_globales_v31.py'
if (-not (Test-Path -LiteralPath $Python)) { throw "Python introuvable : $Python" }
& $Python $script --sortie $Sortie --avec-historique-v30
if ($LASTEXITCODE -ne 0) { throw "Génération statistiques V31 échouée : $LASTEXITCODE" }
Write-Host "Rapport JSON : $(Join-Path $Sortie 'STATS_GLOBALES_ENCYKLOPEDIA_V31.json')"
Write-Host "Tableau HTML : $(Join-Path $Sortie 'TABLEAU_DE_BORD_ENCYKLOPEDIA_V31.html')"
