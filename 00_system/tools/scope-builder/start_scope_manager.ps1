$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
Start-Process -FilePath "pythonw.exe" -ArgumentList @((Join-Path $Here 'run_scope_manager.pyw'))
