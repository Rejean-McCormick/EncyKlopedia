@echo off
setlocal
set "HERE=%~dp0"
set "CAMPAIGN=%~1"
if "%CAMPAIGN%"=="" set "CAMPAIGN=quick"
if "%~2"=="" (
  python -B "%HERE%levelupdiag.py" run "%CAMPAIGN%"
) else (
  python -B "%HERE%levelupdiag.py" --target "%~2" run "%CAMPAIGN%"
)
exit /b %ERRORLEVEL%
