@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0run_manager.pyw" (
  echo [ERREUR] run_manager.pyw introuvable dans %~dp0
  pause
  exit /b 1
)
start "" "%~dp0run_manager.pyw"
exit /b 0
