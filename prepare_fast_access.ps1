param(
  [int]$Threads = 0,
  [string]$ReverseProperties = 'P50,P170',
  [switch]$Force,
  [switch]$AllowSequentialLocator,
  [switch]$ForceReverseSidecar
)
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Script = Join-Path $Root '00_system\tools\performance\scripts\build_fast_access.py'
$Args = @('-u',$Script,'--root',$Root,'--reverse-properties',$ReverseProperties)
if ($Threads -gt 0) { $Args += @('--threads',"$Threads") }
if ($Force) { $Args += '--force' }
if ($AllowSequentialLocator) { $Args += '--allow-sequential-locator' }
if ($ForceReverseSidecar) { $Args += '--force-reverse-sidecar' }
& python @Args
exit $LASTEXITCODE
