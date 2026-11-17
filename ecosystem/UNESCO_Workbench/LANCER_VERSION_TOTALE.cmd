@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
    py -3 "%~dp0EncyKlopedia_UNESCO_Total.pyw"
    exit /b %errorlevel%
)
where python >nul 2>&1
if not errorlevel 1 (
    python "%~dp0EncyKlopedia_UNESCO_Total.pyw"
    exit /b %errorlevel%
)
echo Python 3 est requis pour lancer le Workbench UNESCO.
pause
exit /b 1
