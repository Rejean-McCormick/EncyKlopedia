$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Py = Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $Py) {
  $Py = Get-Command py.exe -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($Py) { & $Py.Source -3w (Join-Path $Root "run_manager.pyw"); exit $LASTEXITCODE }
  throw "Python 3 introuvable. Lance diagnostics\diag_environment.ps1 pour voir les outils détectés."
}
& $Py.Source (Join-Path $Root "run_manager.pyw")
