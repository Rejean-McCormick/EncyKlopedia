param(
 [ValidateSet('tout','catalogue','decouverte')][string]$Action='tout',
 [int]$LotsCatalogue=25,
 [int]$Graines=3000,
 [string]$Python='C:\Users\rejea\AppData\Local\Programs\Python\Python312\python.exe'
)
$ErrorActionPreference='Stop'
$script=Join-Path $PSScriptRoot 'tools\unesco_pilot\piloter_branches_v311.py'
if (-not (Test-Path -LiteralPath $Python)) { throw "Python absent : $Python" }
& $Python $script $Action --max-batches $LotsCatalogue --max-seeds $Graines
if ($LASTEXITCODE -ne 0) {throw "Pilote multibranches refusé : $LASTEXITCODE"}
