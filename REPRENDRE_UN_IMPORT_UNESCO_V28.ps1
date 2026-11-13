[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
try {
  $root = Split-Path -Parent $MyInvocation.MyCommand.Path
  $engine = Join-Path $root 'tools\unesco_pilot\reprendre_import_unesco_v28.py'
  $python = 'C:\Users\rejea\AppData\Local\Programs\Python\Python312\python.exe'
  if (-not (Test-Path -LiteralPath $engine -PathType Leaf)) { throw "Moteur de reprise absent: $engine" }
  if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw "Python absent: $python" }
  $running = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" -ErrorAction Stop | Where-Object { $_.CommandLine -match 'poste_chatgpt_v30\.py' })
  if ($running.Count -gt 0) {
    Write-Host 'REFUS : Le poste v30 semble encore en cours d execution. Fermer sa console de lancement.' -ForegroundColor Red
    $running | Select-Object ProcessId,Name,CommandLine | Format-Table -Wrap
    exit 2
  }
  Write-Host '=== REPRISE CONTROLEE D UN IMPORT UNESCO V28 ===' -ForegroundColor Cyan
  Write-Host 'Le poste v30 doit etre FERME. Sauvegarde avant import. Un seul retour deja valide.'
  & $python -I $engine
  if ($LASTEXITCODE -ne 0) { throw "Reprise v28 refusee (code $LASTEXITCODE); consulter l erreur detaillee ci-dessus" }
  Write-Host 'REPRISE V28 TERMINEE' -ForegroundColor Green
  exit 0
}
catch {
  Write-Host "REPRISE V28 NON TERMINEE : $($_.Exception.Message)" -ForegroundColor Red
  exit 2
}
