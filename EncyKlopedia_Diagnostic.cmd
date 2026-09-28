@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0diagnose.ps1" (
  echo [ERREUR] diagnose.ps1 introuvable dans %~dp0
  pause
  exit /b 1
)
pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0diagnose.ps1"
if errorlevel 1 (
  echo [ERREUR] Le diagnostic a echoue.
  pause
  exit /b 1
)
if exist "%~dp000_system\config\environment.json" start "" notepad.exe "%~dp000_system\config\environment.json"
exit /b 0
