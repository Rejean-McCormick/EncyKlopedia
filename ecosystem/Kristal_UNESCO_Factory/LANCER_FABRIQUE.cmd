@echo off
setlocal
cd /d "%~dp0"
for %%I in ("%~dp0..") do set "KRISTAL_ROOT=%%~fI"
rem Si la venv UNESCO existe, lancer directement la GUI avec cet environnement.
rem Le module runtime_bootstrap vérifie rdflib et se répare automatiquement si nécessaire.
if exist "%KRISTAL_ROOT%\.venv-unesco\Scripts\pythonw.exe" (
  start "" /B "%KRISTAL_ROOT%\.venv-unesco\Scripts\pythonw.exe" "%~dp0Fabrique_UNESCO.pyw"
  exit /b 0
)
if exist "%~dp0.venv\Scripts\pythonw.exe" (
  start "" /B "%~dp0.venv\Scripts\pythonw.exe" "%~dp0Fabrique_UNESCO.pyw"
  exit /b 0
)
where py >nul 2>&1
if not errorlevel 1 (
  py -3 "%~dp0Fabrique_UNESCO.pyw"
  exit /b
)
where python >nul 2>&1
if not errorlevel 1 (
  python "%~dp0Fabrique_UNESCO.pyw"
  exit /b
)
echo Aucun interpreteur Python disponible. Installer Python 3 pour Windows.
pause
exit /b 1
