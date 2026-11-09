@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
python "%~dp0tools\unesco_pilot\registry_provenance_v16.py" --check-only %*
if errorlevel 1 (echo AUDIT BLOQUE) else (echo AUDIT INTACT)
pause
