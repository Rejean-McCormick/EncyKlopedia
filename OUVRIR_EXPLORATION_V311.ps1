param(
 [int]$Propositions=300,
 [string]$Branche='',
 [string]$Station='D:\EncyKlopedia\30_working\poste_chatgpt_v30\station_v30.sqlite',
 [string]$Python='C:\Users\rejea\AppData\Local\Programs\Python\Python312\python.exe'
)
$ErrorActionPreference='Stop'
$script=Join-Path $PSScriptRoot 'tools\unesco_pilot\ouvrir_exploration_v311.py'
if (-not (Test-Path -LiteralPath $Python)) { throw "Python absent : $Python" }
& $Python $script --station $Station --count $Propositions --branch $Branche
if ($LASTEXITCODE -ne 0) {throw "Exploration refusée : $LASTEXITCODE"}
