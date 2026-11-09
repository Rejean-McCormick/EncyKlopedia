@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if "%~1"=="" (
  python "%~dp0tools\unesco_pilot\workspace_readiness_v15.py" --check-only
) else (
  python "%~dp0tools\unesco_pilot\workspace_readiness_v15.py" --check-only --existing-workspace "%~1"
)
if errorlevel 1 echo AUDIT REFUSE - aucun fichier ecrase.
pause
