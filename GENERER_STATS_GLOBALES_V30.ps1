# Générateur statistique en lecture seule. N'importe aucun ZIP et ne crée aucune connaissance canonique.
param(
  [string]$Python = 'C:\Users\rejea\AppData\Local\Programs\Python\Python312\python.exe',
  [string]$Sortie = (Join-Path $env:TEMP 'STATS_GLOBAL_ENCYKLOPEDIA_V30')
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Python)) { throw "Python 3.12 introuvable : $Python" }
$script = Join-Path $PSScriptRoot 'outils_v30\stats_globales_v30.py'
if (-not (Test-Path -LiteralPath $script)) { throw "Fichier absent : $script" }
$repStation = 'D:\EncyKlopedia\30_working\poste_chatgpt_v30'
$repDownloads = Join-Path $HOME 'Downloads'
& $Python $script --sortie $Sortie --repertoires-retours $repDownloads $repStation
if ($LASTEXITCODE -ne 0) { throw "Erreur generateur stats : $LASTEXITCODE" }
Write-Host "`nFichier a envoyer : $(Join-Path $Sortie 'STATS_GLOBAL_ENCYKLOPEDIA_V30.json')"
Write-Host "Tableau de bord : $(Join-Path $Sortie 'TABLEAU_DE_BORD_ENCYKLOPEDIA_V30.html')"
