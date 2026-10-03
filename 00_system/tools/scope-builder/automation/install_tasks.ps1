param(
  [string]$Scope = 'catholic-pilot',
  [switch]$IncludeIntellectuals,
  [int]$PollSeconds = 120,
  [switch]$Force
)
$ErrorActionPreference = 'Stop'
$Tool = Split-Path -Parent $PSScriptRoot
$Root = (Resolve-Path (Join-Path $Tool '..\..\..')).Path
$Scripts = Join-Path $Tool 'scripts'
$Python = (Get-Command python).Source

$ScopeArgs = "--scope $Scope"
if ($IncludeIntellectuals) { $ScopeArgs += ' --scope intellectuals' }

$watchCmd = "`"$Python`" `"$(Join-Path $Scripts 'watch_then_run.py')`" --root `"$Root`" $ScopeArgs --through handoff --poll-seconds $PollSeconds"
$maintCmd = "`"$Python`" `"$(Join-Path $Scripts '09_maintenance.py')`" --root `"$Root`" --min-free-gib 50"

$watchAction = New-ScheduledTaskAction -Execute 'pwsh.exe' -Argument "-NoProfile -WindowStyle Hidden -Command $watchCmd"
$watchTrigger = New-ScheduledTaskTrigger -AtLogOn
$maintAction = New-ScheduledTaskAction -Execute 'pwsh.exe' -Argument "-NoProfile -WindowStyle Hidden -Command $maintCmd"
$maintTrigger = New-ScheduledTaskTrigger -Daily -At 9:00AM

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'EncyKlopedia-AutoScope' -Action $watchAction -Trigger $watchTrigger -Settings $settings -Description 'Builds selected lossless project scope(s) when inputs change; uses global index only if available.' -Force:$Force | Out-Null
Register-ScheduledTask -TaskName 'EncyKlopedia-Maintenance' -Action $maintAction -Trigger $maintTrigger -Settings $settings -Description 'Daily disk/status check for EncyKlopedia.' -Force:$Force | Out-Null
Write-Host 'Installed: EncyKlopedia-AutoScope, EncyKlopedia-Maintenance'
Write-Host 'Automation stops at the Mediatheque source-evidence handoff; it does not invoke DaaT or Kristal.'
