param(
  [ValidateSet('catholic-pilot','intellectuals','both')]
  [string]$Scope = 'catholic-pilot',
  [int]$Threads = 0,
  [switch]$BuildQueryIndex,
  [switch]$CacheVault
)
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $Root 'harvest.ps1') -Scope $Scope -DiscoveryBackend raw -Threads $Threads -BuildQueryIndex:$BuildQueryIndex -CacheVault:$CacheVault -AllowFullScan
exit $LASTEXITCODE
