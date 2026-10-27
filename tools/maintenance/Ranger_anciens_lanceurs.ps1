# Move-only, never delete. No recursive scans, no canonical or data edits.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$keep = Join-Path $root 'Konstellation.cmd'
if (-not (Test-Path -LiteralPath $keep -PathType Leaf)) { Write-Host '[ERREUR] Nouveau lanceur absent. Aucun changement.'; exit 1 }
$names = @(
 'Konstellation_Launcher.cmd','Konstellation_Launcher(2).cmd',
 'Launch_My_Kristals.cmd','Launch_My_Kristals(2).cmd',
 'Ouvrir_Kristal_Catho_v10.cmd','Ouvrir_Theophile_demo.cmd',
 'Test_Konstellation.cmd','Update_Biblical_Corpus.cmd',
 'Nettoyage_Konstellation.pyw','GitSink.bat','ZmartZnap.pyw','Launch_MULTiSmartDump.lnk'
)
$existing = @($names | Where-Object {Test-Path -LiteralPath (Join-Path $root $_) -PathType Leaf})
if ($existing.Count -eq 0) {Write-Host 'Aucun ancien lanceur ou outil connu dans la racine.'; exit 0}
Write-Host 'Les fichiers suivants seront DEPLACES vers un dossier de sauvegarde :'
$existing | ForEach-Object { Write-Host ('  '+$_) }
Write-Host 'Aucune suppression. Aucun dossier Kristal touche.'
$answer=Read-Host 'Ecrire OUI pour confirmer'
if ($answer -cne 'OUI') { Write-Host 'Annule.'; exit 0 }
$backup = Join-Path $root ('_anciens_outils_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $backup -Force | Out-Null
foreach($name in $existing){
  Move-Item -LiteralPath (Join-Path $root $name) -Destination (Join-Path $backup $name) -ErrorAction Stop
}
Write-Host ('Sauvegarde creee : '+$backup)
