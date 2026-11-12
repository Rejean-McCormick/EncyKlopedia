[CmdletBinding()]
param(
  [ValidateRange(0,100000)][int]$MaxBatches = 5000,
  [ValidateRange(10,5000)][int]$BatchSize = 2000,
  [switch]$PreflightOnly,
  [switch]$VerifyOnly,
  [string]$ReviewedBridges = '',
  [string]$SourceDb = 'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite',
  [string]$CatalogueDb = 'D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite',
  [string]$OutputDir = 'D:\EncyKlopedia\30_working\catalogue_global_unesco_wikipedia_v25'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
try {
  if ($PreflightOnly -and $VerifyOnly) { throw 'PreflightOnly et VerifyOnly sont incompatibles' }
  $here = Split-Path -Parent $MyInvocation.MyCommand.Path
  $engine = Join-Path $here 'tools\unesco_pilot\integrer_ponts_revus_v26.py'
  $branch = Join-Path $here 'tools\unesco_pilot\v25_data\branche_mt110.json'
  if (-not $ReviewedBridges) {
    $ReviewedBridges = Join-Path $here 'tools\unesco_pilot\v26_data\PONTS_REVUS_V26_c1126b2f88bb.csv'
  }
  foreach ($p in @($engine, $branch, $ReviewedBridges)) {
    if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { throw "Fichier requis absent : $p" }
  }
  $python = $null
  foreach ($candidate in @(Get-Command -Name 'python.exe' -CommandType Application -All -ErrorAction SilentlyContinue)) {
    $path = [string]$candidate.Source
    if ([string]::IsNullOrWhiteSpace($path) -or $path -like '*\WindowsApps\*') { continue }
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
    try {
      & $path -I -c 'import sys,sqlite3; raise SystemExit(0 if sys.version_info >= (3,11) else 1)' 2>$null
      if ($LASTEXITCODE -eq 0) { $python = $path; break }
    } catch {}
  }
  if (-not $python) { throw 'Python 3.11+ introuvable sur PATH' }

  $common = @('--source-db', $SourceDb, '--catalogue-db', $CatalogueDb, '--output-dir', $OutputDir,
              '--branch', $branch, '--reviewed-bridges', $ReviewedBridges,
              '--max-batches', "$MaxBatches", '--batch-size', "$BatchSize")
  Write-Host "Ponts V26 : Python choisi : $python"
  if ($VerifyOnly) {
    & $python -I $engine verify @common
    if ($LASTEXITCODE -ne 0) { throw 'Verification du catalogue refusee' }
    Write-Host 'V26_PONTS_VERIFY_OK'
    exit 0
  }
  Write-Host 'Ponts V26 : precontrole lecture seule ...'
  & $python -I $engine preflight @common
  if ($LASTEXITCODE -ne 0) { throw 'Precontrole des ponts refuse' }
  if ($PreflightOnly) { Write-Host 'V26_PONTS_PREFLIGHT_OK'; exit 0 }
  Write-Host 'Ponts V26 : integration incrémentale et traitement des categories ...'
  & $python -I $engine apply @common
  if ($LASTEXITCODE -ne 0) { throw 'Integration des ponts refusee' }
  Write-Host 'Ponts V26 : verification du nouveau snapshot ...'
  & $python -I $engine verify @common
  if ($LASTEXITCODE -ne 0) { throw 'Verification de sortie refusee' }
  Write-Host 'V26_PONTS_INTEGRATION_OK'
  exit 0
} catch {
  Write-Host "V26_PONTS_REFUS : $($_.Exception.Message)" -ForegroundColor Red
  exit 2
}
