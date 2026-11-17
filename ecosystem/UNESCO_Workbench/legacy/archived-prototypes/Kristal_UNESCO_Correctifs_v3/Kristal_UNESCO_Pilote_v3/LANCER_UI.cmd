@echo off
setlocal
cd /d "%~dp0"
rem Le diagnostic 2026-11-03 a confirme Python 3.12 sur cette machine.
set "PYW12=%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
if exist "%PYW12%" (
  start "" "%PYW12%" "%~dp0Pilote_Kristal_UNESCO.pyw"
  exit /b 0
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3.12 "%~dp0Pilote_Kristal_UNESCO.pyw"
  if not errorlevel 1 exit /b 0
)
where python >nul 2>nul
if not errorlevel 1 (
  python "%~dp0Pilote_Kristal_UNESCO.pyw"
  exit /b %errorlevel%
)
echo Python 3.12 introuvable. Verifier l'installation Python/Tkinter.
pause
exit /b 1
