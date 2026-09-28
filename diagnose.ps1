$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Diag = Join-Path $Root '00_system\tools\wikidata-manager\diagnostics\diag_environment.ps1'
$Out = Join-Path $Root '00_system\config\environment.json'
pwsh -NoProfile -ExecutionPolicy Bypass -File $Diag -OutputPath $Out
