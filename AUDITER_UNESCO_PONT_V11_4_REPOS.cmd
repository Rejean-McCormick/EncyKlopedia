@echo off
setlocal
cd /d "%~dp0"
python "%~dp0tools\unesco_pilot\canonical_bridge_v13.py" --check-only %*
if errorlevel 1 (echo ECHEC SECURISE & pause & exit /b 2)
echo Audit en lecture seule termine.
pause
