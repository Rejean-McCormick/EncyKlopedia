@echo off
setlocal
cd /d "%~dp0"
echo ===================================
echo   Diagnostic gestionnaire Spek
echo ===================================
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "%~dp0Spek_Template_Manager.pyw" --diagnostic
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    python "%~dp0Spek_Template_Manager.pyw" --diagnostic
  ) else (
    echo ERREUR : Python introuvable.
  )
)
echo.
echo Journal : %%LOCALAPPDATA%%\Spek\TemplateManager\launcher-errors.log
pause
