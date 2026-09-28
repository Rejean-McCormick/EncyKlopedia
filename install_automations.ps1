param(
  [ValidateSet('catholic-pilot','intellectuals')]
  [string]$Scope = 'catholic-pilot',
  [switch]$IncludeIntellectuals,
  [switch]$Force
)
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Script = Join-Path $Root '00_system\tools\scope-builder\automation\install_tasks.ps1'
& pwsh -NoProfile -ExecutionPolicy Bypass -File $Script -Scope $Scope -IncludeIntellectuals:$IncludeIntellectuals -Force:$Force
exit $LASTEXITCODE
