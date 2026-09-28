param([switch]$TryBzip2)
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Script = Join-Path $Root '00_system\tools\performance\scripts\install_fast_deps.py'
$Args = @('-u',$Script)
if ($TryBzip2) { $Args += '--try-bzip2' }
& python @Args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& python -u (Join-Path $Root '00_system\tools\performance\scripts\fast_status.py') --root $Root
