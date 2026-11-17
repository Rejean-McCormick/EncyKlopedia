@echo off
setlocal
cd /d "%~dp0"
py -3.12 -c "import tkinter" >nul 2>&1
if %errorlevel%==0 (
    py -3.12 Pilote_UNESCO_GF.pyw
) else (
    pythonw Pilote_UNESCO_GF.pyw
)
endlocal
