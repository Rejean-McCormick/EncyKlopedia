@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Spek - Local Preview

if not exist "%~dp0scripts\launch_spek.py" goto missing_helper
where python >nul 2>nul
if errorlevel 1 goto missing_python

python "%~dp0scripts\launch_spek.py" %*
set "SPEK_EXIT=%ERRORLEVEL%"
if not "%SPEK_EXIT%"=="0" pause
exit /b %SPEK_EXIT%

:missing_helper
echo [ERROR] Missing scripts\launch_spek.py
 echo Extract both files from the launcher ZIP into the Spek project root.
pause
exit /b 1

:missing_python
echo [ERROR] Python is not available in PATH.
echo Install Python or start the launcher from a Python-enabled terminal.
pause
exit /b 1
