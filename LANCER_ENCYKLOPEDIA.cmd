@echo off
setlocal
set "REPO=C:\mycode\EncyKlopedia\EncyKlopedia"
set "SCRIPT=%REPO%\LANCER_POSTE_CHATGPT_V30.ps1"

if not exist "%SCRIPT%" (
    echo ERREUR : lanceur PowerShell introuvable.
    echo %SCRIPT%
    pause
    exit /b 1
)

where pwsh.exe >nul 2>&1
if errorlevel 1 (
    echo ERREUR : PowerShell 7 ^(pwsh.exe^) est introuvable.
    pause
    exit /b 1
)

cd /d "%REPO%"
pwsh.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
set "CODE=%ERRORLEVEL%"
if not "%CODE%"=="0" (
    echo.
    echo EncyKlopedia s'est termine avec le code %CODE%.
    pause
)
endlocal & exit /b %CODE%
