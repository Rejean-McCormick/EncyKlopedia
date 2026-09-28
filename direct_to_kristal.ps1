param(
  [ValidateSet('catholic-pilot','intellectuals','both')]
  [string]$Scope = 'catholic-pilot',
  [string]$KristalRoot = '',
  [string]$IKRoot = '',
  [int]$Threads = 0
)
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $Root 'harvest_to_kristal.ps1') -Scope $Scope -DiscoveryBackend raw -KristalRoot $KristalRoot -IKRoot $IKRoot -Threads $Threads -AllowFullScan
exit $LASTEXITCODE
