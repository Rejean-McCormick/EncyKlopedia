$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$App = Join-Path $Root '00_system\tools\scope-builder\run_scope_manager.pyw'
Start-Process -FilePath 'pythonw.exe' -ArgumentList @($App) -WorkingDirectory $Root
