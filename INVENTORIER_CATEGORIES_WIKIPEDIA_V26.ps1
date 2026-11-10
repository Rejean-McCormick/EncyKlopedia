[CmdletBinding()]
param(
  [ValidateRange(1,5000000)][int]$MaxRows = 200000,
  [ValidateRange(1,20000)][int]$BatchSize = 5000,
  [string]$SourceDb = 'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite',
  [string]$InventoryDb = 'D:\EncyKlopedia\80_search_indexes\EncyKlopedia\inventaire_categories_wikipedia_v26.sqlite',
  [string]$OutputDir = 'D:\EncyKlopedia\30_working\inventaire_categories_wikipedia_v26',
  [string]$ConceptsFile = '',
  [switch]$StatusOnly,
  [switch]$ScanOnly,
  [switch]$ExportOnly,
  [string]$QueriesFile = '',
  [string]$DecisionsFile = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

try {
  $here = Split-Path -Parent $MyInvocation.MyCommand.Path
  $engine = Join-Path $here 'tools\unesco_pilot\inventaire_categories_v26.py'
  if (-not (Test-Path -LiteralPath $engine -PathType Leaf)) {
    throw 'Moteur Python V26 absent dans le depot.'
  }

  # Selectionner un seul mode explicite; sinon inventorier puis exporter.
  $modes = @()
  if ($StatusOnly) { $modes += 'status' }
  if ($ScanOnly) { $modes += 'scan' }
  if ($ExportOnly) { $modes += 'export' }
  if (-not [string]::IsNullOrWhiteSpace($QueriesFile)) { $modes += 'probe' }
  if (-not [string]::IsNullOrWhiteSpace($DecisionsFile)) { $modes += 'import-decisions' }
  if ($modes.Count -gt 1) {
    throw 'Modes incompatibles : utiliser un seul parmi StatusOnly, ScanOnly, ExportOnly, QueriesFile ou DecisionsFile.'
  }
  $action = if ($modes.Count -eq 1) { $modes[0] } else { 'scan-export' }

  if (-not $ConceptsFile) {
    $ConceptsFile = Join-Path $here 'tools\unesco_pilot\v25_data\unesco_2026_educational_policy.json'
  }
  if ($action -in @('scan-export','export','import-decisions')) {
    if (-not (Test-Path -LiteralPath $ConceptsFile -PathType Leaf)) {
      throw "Reference UNESCO introuvable : $ConceptsFile"
    }
  }
  if ($action -eq 'probe' -and -not (Test-Path -LiteralPath $QueriesFile -PathType Leaf)) {
    throw "Fichier de requetes introuvable : $QueriesFile"
  }
  if ($action -eq 'import-decisions' -and -not (Test-Path -LiteralPath $DecisionsFile -PathType Leaf)) {
    throw "Fichier de decisions introuvable : $DecisionsFile"
  }

  # IMPORTANT : filtrage WindowsApps par wildcard, jamais par regex mal echappee.
  # Get-Command -All retourne plusieurs executables ; en choisir un seul apres test.
  $python = $null
  foreach ($candidate in @(Get-Command -Name 'python.exe' -CommandType Application -All -ErrorAction SilentlyContinue)) {
    $path = [string]$candidate.Source
    if ([string]::IsNullOrWhiteSpace($path)) { continue }
    if ($path -like '*\WindowsApps\*') { continue }
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
    try {
      & $path -I -c 'import sys,sqlite3; db=sqlite3.connect(":memory:"); db.execute("CREATE VIRTUAL TABLE _v26_probe USING fts5(text)"); db.close(); raise SystemExit(0 if sys.version_info >= (3,11) else 1)' 2>$null
      if ($LASTEXITCODE -eq 0) {
        $python = $path
        break
      }
    } catch {
      # Essayer le candidat Python suivant, sans exposer une fausse reussite.
    }
  }
  if (-not $python) {
    throw 'Python >= 3.11 avec SQLite FTS5 introuvable sur PATH.'
  }

  $cliArgs = @('-I', $engine, $action,
    '--source-db', $SourceDb, '--inventory-db', $InventoryDb,
    '--output-dir', $OutputDir, '--max-rows', "$MaxRows", '--batch-size', "$BatchSize")
  if ($action -in @('scan-export','export','import-decisions')) { $cliArgs += @('--concepts', $ConceptsFile) }
  if ($action -eq 'probe') { $cliArgs += @('--queries-file', $QueriesFile) }
  if ($action -eq 'import-decisions') { $cliArgs += @('--decisions', $DecisionsFile) }

  Write-Host "V26 : Python choisi : $python"
  Write-Host "V26 : action $action ; base Wikipedia en LECTURE SEULE"
  & $python @cliArgs
  if ($LASTEXITCODE -ne 0) { throw "Moteur V26 en echec (code $LASTEXITCODE)" }
  Write-Host "V26_INVENTAIRE_OK : action $action terminee."
  exit 0
} catch {
  Write-Host "V26_INVENTAIRE_REFUS : $($_.Exception.Message)" -ForegroundColor Red
  exit 2
}
