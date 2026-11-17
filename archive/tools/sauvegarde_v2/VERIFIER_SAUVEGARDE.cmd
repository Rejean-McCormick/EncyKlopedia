@echo off
setlocal
chcp 65001 >nul
set "BASE=%~dp0"
where pwsh.exe >nul 2>&1
if errorlevel 1 (
  echo ERREUR : PowerShell 7 introuvable.
  pause
  exit /b 2
)
pwsh.exe -NoProfile -ExecutionPolicy Bypass -File "%BASE%MENU_SAUVEGARDE.ps1" -Verifier
set "CODE=%ERRORLEVEL%"
pause
endlocal & exit /b %CODE%
