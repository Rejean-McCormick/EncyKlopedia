# EncyKlopedia — installation explicite d'une tâche planifiée, utilisateur courant.
# PowerShell 5.1. Ne touche pas aux bases, preuves, tâches ou fichiers de production.
# Placez ce PS1 et AUDIT_AUTOMATIQUE_BRANCHE_V312.pyw côte à côte.
param(
    [string]$Heure = '07:00',
    [string]$Branche = 'unesco.mt1.10',
    [string]$DossierRapports = "$env:USERPROFILE\Documents\EncyKlopedia_Audits",
    [switch]$Desinstaller
)
$ErrorActionPreference = 'Stop'
$taskName = 'EncyKlopedia_Audit_Branche_V312'
if ($Desinstaller) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Tache $taskName supprimee. Les rapports et les bases restent inchanges."
    exit 0
}
if ($Heure -notmatch '^(?:[01][0-9]|2[0-3]):[0-5][0-9]$') {
    throw 'Utiliser -Heure HH:mm (exemple 07:00).'
}
$pyw = Join-Path $PSScriptRoot 'AUDIT_AUTOMATIQUE_BRANCHE_V312.pyw'
if (-not (Test-Path -LiteralPath $pyw -PathType Leaf)) {
    throw "Application absente : $pyw"
}
$pythonCommand = Get-Command 'python.exe' -ErrorAction Stop
$pythonw = Join-Path (Split-Path -Parent $pythonCommand.Source) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonw -PathType Leaf)) {
    throw "pythonw.exe introuvable : $pythonw"
}
$arguments = '"' + $pyw + '" --once --branch "' + $Branche + '" --output "' + $DossierRapports + '"'
$action = New-ScheduledTaskAction -Execute $pythonw -Argument $arguments -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -Daily -At $Heure
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
    -Description 'Diagnostic UNESCO v31.2 en lecture seule, resultats JSON/CSV locaux' -Force | Out-Null
Write-Host "Tache planifiee installee : $taskName, chaque jour a $Heure."
Write-Host "Rapports dans : $DossierRapports"
Write-Host 'Pour annuler : .\ACTIVER_AUDIT_QUOTIDIEN_V312.ps1 -Desinstaller'
