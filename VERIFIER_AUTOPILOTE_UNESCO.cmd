@echo off
setlocal
cd /d "%~dp0"
py -3 "%~dp0tools\unesco_pilot\automated_local_pilot.py" status
pause
