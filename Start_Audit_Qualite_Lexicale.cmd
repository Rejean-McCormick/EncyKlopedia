@echo off
setlocal
cd /d "%~dp0"
where pyw >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" pyw -3 "%~dp0Audit_Qualite_Lexicale_UI.pyw"
    exit /b 0
)
where pythonw >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" pythonw "%~dp0Audit_Qualite_Lexicale_UI.pyw"
    exit /b 0
)
echo Python avec Tkinter requis. Installer Python 3.10+ et reessayer.
pause
exit /b 1
