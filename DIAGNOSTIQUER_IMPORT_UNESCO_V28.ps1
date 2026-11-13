[CmdletBinding()]
param(
  [string]$TaskId = 'v28_ac43a56fc32867_530dee66'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$script = Join-Path $root 'tools\unesco_pilot\diagnostiquer_import_v28_sur_copie.py'
$python = 'C:\Users\rejea\AppData\Local\Programs\Python\Python312\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw "Python absent : $python" }
if (-not (Test-Path -LiteralPath $script -PathType Leaf)) { throw "Script diagnostic absent : $script" }
Write-Host "`n=== DIAGNOSTIC IMPORT UNESCO V28 (COPIE ISOLEE) ===" -ForegroundColor Cyan
Write-Host 'Fermer le poste v30 avant de continuer. Aucun import dans le catalogue original.'
& $python -I $script --task-id $TaskId
if ($LASTEXITCODE -ne 0) { throw "Diagnostic en erreur (code $LASTEXITCODE). Voir les messages ci-dessus." }
