# Simulation de priorisation + taille adaptative des FUTURS lots UNESCO v28.
# ATTENTION : n'importe pas et ne remplace AUCUNE tache existante.
param(
  [string]$Chemin = 'D:\EncyKlopedia\30_working\poste_chatgpt_v30',
  [string]$Contextes = '',
  [string]$Sortie = (Join-Path $env:TEMP 'PLAN_PACKS_UNESCO_V28'),
  [string]$Configuration = '',
  [string]$Python = 'C:\Users\rejea\AppData\Local\Programs\Python\Python312\python.exe'
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw "Python introuvable : $Python" }
if (-not (Test-Path -LiteralPath $Chemin)) { throw "Entree introuvable : $Chemin" }
$script = Join-Path $PSScriptRoot 'outils_v30\planifier_packs_unesco_v28.py'
$arg = @($script,'--sortie',$Sortie)
if ([System.IO.Path]::GetExtension($Chemin) -ieq '.csv') {
    $arg += @('--csv',$Chemin)
    if ($Contextes) { $arg += @('--contextes',$Contextes) }
} else {
    if ($Contextes) { throw '-Contextes ne s utilise qu avec un CSV pre-generation.' }
    $arg += @('--packs',$Chemin)
}
if ($Configuration) { $arg += @('--configuration',$Configuration) }
& $Python @arg
if ($LASTEXITCODE -ne 0) { throw "La planification a echoue (code $LASTEXITCODE)" }
Write-Host "Plan cree : $(Join-Path $Sortie 'PLAN_PACKS_UNESCO_V28.csv')"
Write-Host 'NOTE: Aucun pack de la station n a ete modifie. Le producteur v28 n est pas encore branche.'
