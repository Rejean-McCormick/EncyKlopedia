$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Script = Join-Path $Root '00_system\tools\scope-builder\automation\remove_tasks.ps1'
& pwsh -NoProfile -ExecutionPolicy Bypass -File $Script
exit $LASTEXITCODE
