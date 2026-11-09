@echo off
setlocal
cd /d "%~dp0"
where pyw >nul 2>&1
if %errorlevel%==0 (start "" pyw -3 "%~dp0Qualifier_Dictionnaires_diK_UI.pyw" & exit /b 0)
where pythonw >nul 2>&1
if %errorlevel%==0 (start "" pythonw "%~dp0Qualifier_Dictionnaires_diK_UI.pyw" & exit /b 0)
echo Python 3 avec tkinter introuvable.
pause
exit /b 1
