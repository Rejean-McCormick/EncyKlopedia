param([int]$Entities = 250000,[int]$Threads = 0)
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Script = Join-Path $Root '00_system\tools\performance\scripts\benchmark_dump.py'
$Args = @('-u',$Script,'--root',$Root,'--entities',"$Entities")
if ($Threads -gt 0) { $Args += @('--threads',"$Threads") }
& python @Args
exit $LASTEXITCODE
