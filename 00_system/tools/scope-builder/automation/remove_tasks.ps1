$ErrorActionPreference = 'SilentlyContinue'
Unregister-ScheduledTask -TaskName 'EncyKlopedia-AutoScope' -Confirm:$false
Unregister-ScheduledTask -TaskName 'EncyKlopedia-Maintenance' -Confirm:$false
Write-Host 'EncyKlopedia scheduled tasks removed.'
