param(
  [ValidateSet('catholic-pilot','intellectuals','both')]
  [string]$Scope = 'catholic-pilot',
  [ValidateSet('auto','index','fast','raw')]
  [string]$DiscoveryBackend = 'auto',
  [int]$Threads = 0,
  [switch]$PrepareFastAccess,
  [switch]$BuildQueryIndex,
  [switch]$CacheVault,
  [switch]$AllowFullScan,
  [ValidateSet('resolve','discover','freeze','evidence','index','identities','handoff')]
  [string]$Through = 'handoff'
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Script = Join-Path $Root '00_system\tools\scope-builder\scripts\run_scope_pipeline.py'
$Args = @('-u', $Script, '--root', $Root, '--through', $Through, '--discovery-backend', $DiscoveryBackend)
if ($Scope -eq 'both') { $Args += @('--scope','catholic-pilot','--scope','intellectuals') }
else { $Args += @('--scope',$Scope) }
if ($Threads -gt 0) { $Args += @('--threads',"$Threads") }
if ($PrepareFastAccess) { $Args += '--prepare-fast-access' }
if ($BuildQueryIndex) { $Args += '--build-query-index' }
if ($CacheVault) { $Args += '--cache-vault' }
if ($AllowFullScan) { $Args += '--allow-full-scan' }
& python @Args
exit $LASTEXITCODE
