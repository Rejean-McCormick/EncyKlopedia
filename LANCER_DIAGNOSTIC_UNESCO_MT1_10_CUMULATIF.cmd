@echo off
setlocal
set "ROOT=%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python Launcher ^(py^) requis.
  pause
  exit /b 2
)
py -3 "%ROOT%tools\unesco_pilot\cumulative_preflight.py" --root "C:\mycode"
set "RC=%ERRORLEVEL%"
echo.
echo Diagnostic termine. Code: %RC%
pause
exit /b %RC%
