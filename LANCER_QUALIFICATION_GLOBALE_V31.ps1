param(
  [switch]$Tout,
  [int]$Articles = 100000,
  [int]$Lot = 2000,
  [int]$Categories = 18,
  [string]$Branches = 'C:\mycode\EncyKlopedia\EncyKlopedia\tools\unesco_pilot\v25_data',
  [string]$Source = 'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite',
  [string]$Sortie = 'D:\EncyKlopedia\30_working\qualification_multibranche_v31\qualification_multibranche_v31.sqlite',
  [string]$Python = 'C:\Users\rejea\AppData\Local\Programs\Python\Python312\python.exe'
)
$ErrorActionPreference='Stop'
$script=Join-Path $PSScriptRoot 'tools\unesco_pilot\qualification_globale_v31.py'
if (-not (Test-Path -LiteralPath $script)) { throw "Qualification V31 absente : $script" }
if (-not (Test-Path -LiteralPath $Python)) { throw "Python absent : $Python" }
if (-not (Test-Path -LiteralPath $Branches)) { throw "Répertoire de branches absent : $Branches" }
if ($Articles -lt 1 -or $Lot -lt 1) { throw 'Articles et Lot doivent être positifs.' }
do {
  $raw=& $Python $script --source $Source --output $Sortie --branches $Branches --batch-size $Lot --max-articles $Articles --categories-per-article $Categories | Out-String
  if ($LASTEXITCODE -ne 0) { throw "Echec de qualification V31 : $raw" }
  $report=$raw | ConvertFrom-Json
  Write-Host ("Qualification : {0} profils cumulés | {1} associations proposées | dernier page_id {2}" -f $report.totals.profiles, $report.totals.suggestions, $report.cursor_page_id)
  if ($report.batch.pages_processed -eq 0 -and -not $report.source_exhausted) { throw 'Aucun progrès observé dans le scan.' }
} while ($Tout -and -not $report.source_exhausted)
Write-Host "Cache de qualification : $Sortie"
