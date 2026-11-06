@echo off
setlocal
cd /d "%~dp0"
where pyw >nul 2>&1
if %errorlevel% equ 0 (
    start "" pyw -3 "%~dp0Enrichir_Dictionnaires_diK_UI.pyw"
) else (
    where pythonw >nul 2>&1
    if %errorlevel% equ 0 (
        start "" pythonw "%~dp0Enrichir_Dictionnaires_diK_UI.pyw"
    ) else (
        py -3 "%~dp0Enrichir_Dictionnaires_diK_UI.pyw"
    )
)
endlocal
