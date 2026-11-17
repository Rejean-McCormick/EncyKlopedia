@echo off
setlocal
cd /d "%~dp0"
set "PYW12=%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
if exist "%PYW12%" (
  start "" "%PYW12%" "%~dp0Diagnostic_Kristal_UNESCO_UI_v3.pyw"
  exit /b 0
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3.12 "%~dp0Diagnostic_Kristal_UNESCO_UI_v3.pyw"
  if not errorlevel 1 exit /b 0
)
python "%~dp0Diagnostic_Kristal_UNESCO_UI_v3.pyw"
