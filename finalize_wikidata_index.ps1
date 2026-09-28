param(
  [string]$Db = '',
  [string]$TempDir = '',
  [int]$Threads = 0,
  [switch]$SkipOptimize
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $Db) { $Db = Join-Path $Root '30_working\wikidata\wikidata.compact.sqlite' }
if (-not $TempDir) {
  if ($IsWindows) { $TempDir = 'C:\EncyKlopediaTemp' }
  else { $TempDir = Join-Path $Root '90_runtime\temp\sqlite' }
}
New-Item -ItemType Directory $TempDir -Force | Out-Null
$Script = Join-Path $Root '00_system\tools\wikidata-manager\scripts\build_compact_index.py'
$Args = @('-u',$Script,'--db',$Db,'--finalize-only','--temp-dir',$TempDir)
if ($Threads -gt 0) { $Args += @('--threads',"$Threads") }
if ($SkipOptimize) { $Args += '--skip-optimize' }
& python @Args
exit $LASTEXITCODE
