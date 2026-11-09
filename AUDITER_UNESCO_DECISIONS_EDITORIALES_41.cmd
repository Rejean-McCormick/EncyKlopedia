@echo off
setlocal
cd /d "%~dp0"
python "%~dp0tools\unesco_pilot\editorial_advance_v14.py" --check-only %*
if errorlevel 1 (
 echo ECHEC SECURISE.
 pause
 exit /b 2
)
pause
