[CmdletBinding()]
param(
  [ValidateSet('Packs','Import','Status','Export','VerifyPack')]
  [string]$Action = 'Packs',
  [int]$MaxPacks = 5,
  [int]$MaxArticles = 120,
  [int]$TargetWords = 400000,
  [int]$TargetBytes = 62914560,
  [string]$CataloguePath = 'D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite',
  [string]$XmlPath = 'D:\EncyKlopedia\30_working\wikipedia_en_uncompressed\enwiki-latest-pages-articles-multistream.xml',
  [string]$IndexPath = 'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en_direct_pages_v21.sqlite',
  [string]$WorkRoot = 'D:\EncyKlopedia\30_working\production_kristals_v27',
  [string]$Pack = '',
  [string]$Delta = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
try {
  $root = Split-Path -Parent $MyInvocation.MyCommand.Path
  $engine = Join-Path $root 'tools\unesco_pilot\production_kristals_v27.py'
  if (-not (Test-Path -LiteralPath $engine -PathType Leaf)) {throw 'Moteur v27 absent du depot'}

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
  Write-Host "V27 : Python $python ; action $Action"
  $arguments = @('--work',$WorkRoot)
  switch ($Action) {
    'Packs' {
      $arguments += @('--catalogue',$CataloguePath,'--xml',$XmlPath,'--index',$IndexPath,
                      '--max-packs',"$MaxPacks",'--max-articles',"$MaxArticles",
                      '--target-words',"$TargetWords",'--target-bytes',"$TargetBytes")
      $cmd = 'packs'
    }
    'Import' {
      if (-not $Pack -or -not $Delta) {throw 'Import : preciser -Pack et -Delta'}
      $arguments += @('--pack',$Pack,'--delta',$Delta)
      $cmd = 'import'
    }
    'VerifyPack' {
      if (-not $Pack) {throw 'VerifyPack : preciser -Pack'}
      $arguments += @('--pack',$Pack)
      $cmd = 'verify-pack'
    }
    'Status' {$cmd='status'}
    'Export' {$cmd='export'}
  }
  & $python -I $engine $cmd @arguments
  if ($LASTEXITCODE -ne 0) {throw "Le moteur v27 a refuse l'action $Action"}
  Write-Host 'V27_ACTION_OK'
  exit 0
} catch {
  Write-Host "V27_ACTION_REFUSEE : $($_.Exception.Message)" -ForegroundColor Red
  exit 2
}
