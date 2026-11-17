@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 "Pilote_Kristal_UNESCO.pyw"
    exit /b %errorlevel%
)
where python >nul 2>nul
if not errorlevel 1 (
    python "Pilote_Kristal_UNESCO.pyw"
    exit /b %errorlevel%
)
echo Python 3 non detecte. Installer Python 3 ou associer .pyw a pythonw.exe.
pause
