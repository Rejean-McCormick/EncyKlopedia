@echo off
setlocal
cd /d "%~dp0"
where pyw.exe >nul 2>nul
if %errorlevel%==0 (
    start "" pyw.exe -3 "%~dp0Concilier_Dictionnaires_diK_UI.pyw"
) else (
    where pythonw.exe >nul 2>nul
    if %errorlevel%==0 (
        start "" pythonw.exe "%~dp0Concilier_Dictionnaires_diK_UI.pyw"
    ) else (
        echo Python 3 avec Tkinter est requis.
        pause
    )
)
