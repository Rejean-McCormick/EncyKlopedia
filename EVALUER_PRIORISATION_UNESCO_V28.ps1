# Mode diagnostic uniquement : aucun pack modifié, aucun candidat supprimé, aucune tâche invalidée.
param(
  [string]$Chemin = 'D:\EncyKlopedia\30_working\poste_chatgpt_v30',
  [string]$Sortie = (Join-Path $env:TEMP 'PRIORISATION_UNESCO_V28'),
  [string]$Python = 'C:\Users\rejea\AppData\Local\Programs\Python\Python312\python.exe'
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Python)) { throw "Python 3.12 introuvable : $Python" }
if (-not (Test-Path -LiteralPath $Chemin)) { throw "ZIP ou dossier introuvable : $Chemin" }
$script = Join-Path $PSScriptRoot 'outils_v30\priorisation_unesco_v28.py'
if ([System.IO.Path]::GetExtension($Chemin) -ieq '.csv') {
  & $Python $script --csv $Chemin --sortie $Sortie
} else {
  & $Python $script --packs $Chemin --sortie $Sortie
}
if ($LASTEXITCODE -ne 0) { throw "Analyse terminee avec erreurs ($LASTEXITCODE), voir rapport : $Sortie" }
Write-Host "`nPriorites : $(Join-Path $Sortie 'PRIORITES_CANDIDATS_V28.csv')"
