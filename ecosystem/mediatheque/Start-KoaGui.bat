@echo off
setlocal

rem Médiathèque kOA — Windows launcher wrapper
rem This file launches Start-KoaGui.ps1 with PowerShell 7 when available.

set "KOA_ROOT=%~dp0"
set "KOA_PS1=%KOA_ROOT%Start-KoaGui.ps1"

if not exist "%KOA_PS1%" (
    echo [kOA] ERROR: Missing launcher script:
    echo %KOA_PS1%
    pause
    exit /b 1
)

where pwsh >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%KOA_PS1%"
    set "KOA_EXIT=%ERRORLEVEL%"
    if not "%KOA_EXIT%"=="0" pause
    exit /b %KOA_EXIT%
)

where powershell >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [kOA] WARNING: PowerShell 7 executable 'pwsh' was not found.
    echo [kOA] WARNING: Falling back to Windows PowerShell. PowerShell 7 is required by contract.
    powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%KOA_PS1%"
    set "KOA_EXIT=%ERRORLEVEL%"
    if not "%KOA_EXIT%"=="0" pause
    exit /b %KOA_EXIT%
)

echo [kOA] ERROR: No PowerShell executable found.
echo [kOA] Install PowerShell 7, then run this file again.
pause
exit /b 1