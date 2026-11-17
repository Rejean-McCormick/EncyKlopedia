@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
  py -3 EncyKlopedia.pyw
) else (
  python EncyKlopedia.pyw
)
if errorlevel 1 (
  echo EncyKlopedia n'a pas pu demarrer. Verifier Python 3.10+ et tkinter.
  pause
)
endlocal
