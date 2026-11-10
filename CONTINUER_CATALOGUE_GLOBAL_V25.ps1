[CmdletBinding()]
param(
  [int]$MaxBatches = 250,
  [int]$BatchSize = 2000,
  [string[]]$Branches = @(),
  [switch]$ReportOnly,
  [string]$SourceDb = 'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite',
  [string]$CatalogueDb = 'D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite',
  [string]$OutputDir = 'D:\EncyKlopedia\30_working\catalogue_global_unesco_wikipedia_v25'
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
try {
  $here=Split-Path -Parent $MyInvocation.MyCommand.Path
  $script=Join-Path $here 'tools\unesco_pilot\catalogue_global_v25.py'
  if (-not (Test-Path -LiteralPath $script -PathType Leaf)) { throw 'Moteur v25 absent' }
  $found=$null
  foreach ($candidate in @(Get-Command -Name 'python.exe' -CommandType Application -All -ErrorAction SilentlyContinue)) {
    $path=[string]$candidate.Source
    if (-not $path -or $path -match '(?i)\\WindowsApps\\' -or -not (Test-Path -LiteralPath $path -PathType Leaf)) {continue}
    try {
      & $path -I -c 'import sys,sqlite3;raise SystemExit(0 if sys.version_info >= (3,11) else 1)' *> $null
      if ($LASTEXITCODE -eq 0) {$found=@{Exe=$path;Prefix=@()};break}
    } catch {}
  }
  if (-not $found) {throw 'Python >= 3.11 non trouve sur PATH'}
  $action=if($ReportOnly){'report'}else{'run'}
  $opts=@('--source-db',$SourceDb,'--catalogue-db',$CatalogueDb,'--output-dir',$OutputDir,'--max-batches',"$MaxBatches",'--batch-size',"$BatchSize")
  $batchBranches=if($Branches.Count -gt 0){$Branches}else{@(Join-Path $here 'tools\unesco_pilot\v25_data\branche_mt110.json')}
  foreach($b in $batchBranches){$opts+=@('--branch',$b)}
  $exe=[string]$found.Exe
  $prefix=@($found.Prefix)
  & $exe @prefix -I $script $action @opts
  if($LASTEXITCODE -ne 0){throw 'Execution v25 refusee'}
  & $exe @prefix -I $script verify --output-dir $OutputDir
  if($LASTEXITCODE -ne 0){throw 'Verification v25 refusee'}
  Write-Host 'V25_REPRISE_OK : consulter LATEST.json pour lecteur et export'
  exit 0
} catch {
  Write-Host "V25_REPRISE_REFUSEE : $($_.Exception.Message)" -ForegroundColor Red
  exit 2
}
