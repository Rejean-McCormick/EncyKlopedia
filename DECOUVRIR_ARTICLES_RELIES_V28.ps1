[CmdletBinding()]
param(
  [ValidateSet('Preflight','Discover','Export','Apply','Status')]
  [string]$Action = 'Discover',
  [int]$MaxSeeds = 1000,
  [int]$MaxLinksPerSeed = 160,
  [int]$MaxSeedCategories = 35,
  [int]$MaxCategoriesPerConcept = 3,
  [int]$MaxCategorySize = 250,
  [int]$MaxNeighborsPerCategory = 45,
  [int]$MaxSubcategories = 3,
  [int]$MaxExport = 1500,
  [string]$DecisionsFile = '',
  [switch]$DryRun,
  [string]$CataloguePath = 'D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite',
  [string]$SourceDb = 'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite',
  [string]$XmlPath = 'D:\EncyKlopedia\30_working\wikipedia_en_uncompressed\enwiki-latest-pages-articles-multistream.xml',
  [string]$IndexPath = 'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en_direct_pages_v21.sqlite',
  [string]$WorkRoot = 'D:\EncyKlopedia\30_working\decouverte_articles_relies_v28',
  [string]$CatalogueOutput = 'D:\EncyKlopedia\30_working\catalogue_global_unesco_wikipedia_v25',
  [string]$BranchManifest = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
try {
  $root = Split-Path -Parent $MyInvocation.MyCommand.Path
  $engine = Join-Path $root 'tools\unesco_pilot\decouvrir_articles_relies_v28.py'
  if (-not (Test-Path -LiteralPath $engine -PathType Leaf)) {throw 'Moteur v28 absent du depot'}
  if (-not $BranchManifest) {$BranchManifest = Join-Path $root 'tools\unesco_pilot\v25_data\branche_mt110.json'}
  $python = $null
  foreach ($candidate in @(Get-Command -Name python.exe -CommandType Application -All -ErrorAction SilentlyContinue)) {
    $path = [string]$candidate.Source
    if (-not $path -or $path.IndexOf('\WindowsApps\',[StringComparison]::OrdinalIgnoreCase) -ge 0) {continue}
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {continue}
    try {
      & $path -I -c 'import sys,sqlite3;raise SystemExit(0 if sys.version_info >= (3,11) else 1)' *> $null
      if ($LASTEXITCODE -eq 0) {$python = $path; break}
    } catch {}
  }
  if (-not $python) {throw 'Python 3.11+ requis; python.exe introuvable sur PATH'}
  $arguments = @('--source-db',$SourceDb,'--catalogue-db',$CataloguePath,
                 '--index',$IndexPath,'--xml',$XmlPath,'--branch',$BranchManifest,
                 '--work',$WorkRoot,'--catalogue-output',$CatalogueOutput,
                 '--max-seeds',"$MaxSeeds",'--max-links-per-seed',"$MaxLinksPerSeed",
                 '--max-seed-categories',"$MaxSeedCategories",
                 '--max-categories-per-concept',"$MaxCategoriesPerConcept",
                 '--max-category-size',"$MaxCategorySize",
                 '--max-neighbors-per-category',"$MaxNeighborsPerCategory",
                 '--max-subcategories',"$MaxSubcategories",'--max-export',"$MaxExport")
  if ($Action -eq 'Apply') {
    if (-not $DecisionsFile) {throw 'Apply exige -DecisionsFile <chemin CSV>'}
    $arguments += @('--decisions',$DecisionsFile)
    if ($DryRun) {$arguments += '--dry-run'}
  }
  Write-Host "V28 : Python $python ; action $Action"
  $cmd = $Action.ToLowerInvariant()
  & $python -I $engine $cmd @arguments
  if ($LASTEXITCODE -ne 0) {throw "Le moteur v28 a refuse l'action $Action"}
  Write-Host 'V28_ACTION_OK'
  exit 0
} catch {
  Write-Host "V28_ACTION_REFUSEE : $($_.Exception.Message)" -ForegroundColor Red
  exit 2
}
