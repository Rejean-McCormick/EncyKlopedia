@echo off
setlocal
chcp 65001 >nul
echo ============================================================
echo UNESCO V18 - CORRECTIF COMPATIBILITE FRAMEWORK v11
echo Dictionnaire UNESCO NON SIGNE isole dans une COPIE PRIVEE
echo Kit + Framework + Integration Pack (controles officiels)
echo AUCUNE admission KQ/KP/KA/KS, GF ou publication GitHub
echo ============================================================
set "SCRIPT=%~dp0..\..\Kristal\Kristal-Authoring-Kit\tools\unesco_framework_quarantine_v18.py"
python "%SCRIPT%" %*
if errorlevel 1 (
 echo.
 echo ECHEC FERME : source V17 et canon preserves.
 pause
 exit /b 2
)
echo.
echo SUCCES TECHNIQUE : copie privee V18, aucun canon qualifie.
pause
endlocal
