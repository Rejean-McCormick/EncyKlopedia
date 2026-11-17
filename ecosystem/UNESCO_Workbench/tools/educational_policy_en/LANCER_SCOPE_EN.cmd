@echo off
setlocal
cd /d "%~dp0"
where pyw >nul 2>&1
if %ERRORLEVEL% EQU 0 (
 start "" pyw -3 "%~dp0Scope_Encyclopedia_EN.pyw"
) else (
 start "" pythonw "%~dp0Scope_Encyclopedia_EN.pyw"
)
