@echo off
setlocal
chcp 65001 >nul
echo UNESCO V18 - AUDIT SANS ECRITURE
set "SCRIPT=%~dp0..\..\Kristal\Kristal-Authoring-Kit\tools\unesco_framework_quarantine_v18.py"
python "%SCRIPT%" --audit %*
if errorlevel 1 (
 echo AUDIT ECHEC : ne pas publier.
 pause
 exit /b 2
)
echo AUDIT REUSSI : structure privee uniquement.
pause
endlocal
