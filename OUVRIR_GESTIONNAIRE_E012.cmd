@echo off
setlocal
cd /d "%~dp0"
py -3 -B gestionnaire_e012\manager.py gui
if errorlevel 1 pause
