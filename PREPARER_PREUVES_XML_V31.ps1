param(
  [string]$Dump = 'D:\EncyKlopedia\30_working\wikipedia_en_uncompressed\enwiki-latest-pages-articles-multistream.xml',
  [string]$Stage = 'D:\EncyKlopedia\30_working\decouverte_articles_relies_v28\DECOUVERTE_ARTICLES_RELIES_V28.sqlite',
  [string]$Cache = 'D:\EncyKlopedia\30_working\preuves_xml_cibles_v31\PREUVES_XML_CIBLES_V31.sqlite',
  [int]$MaxCaracteres = 100000,
  [string]$Python = 'C:\Users\rejea\AppData\Local\Programs\Python\Python312\python.exe'
)
$ErrorActionPreference='Stop'
$script=Join-Path $PSScriptRoot 'tools\unesco_pilot\preuves_xml_v31.py'
if (-not (Test-Path -LiteralPath $Python)) { throw "Python introuvable : $Python" }
& $Python $script --xml $Dump --stage $Stage --cache $Cache --text-chars $MaxCaracteres
if ($LASTEXITCODE -ne 0) { throw "Préparation XML V31 échouée : $LASTEXITCODE" }
Write-Host "Les ZIPs UNESCO futurs disposent maintenant du cache XML, sous réserve de la révision de chaque article."
