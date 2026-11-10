@echo off
setlocal
set "SCRIPT=%~dp0tools\unesco_pilot\overlay_probatoire_v23.py"
python -I "%SCRIPT%" verify
if errorlevel 1 exit /b 2
echo V23_AUDIT_OK
exit /b 0
