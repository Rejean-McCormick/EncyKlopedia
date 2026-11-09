@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo UNESCO - 191 decisions editoriales prises par ChatGPT
 echo 41 apercus anglais PRIVES, aucune signature ni canon
 echo ============================================================
python "%~dp0tools\unesco_pilot\editorial_advance_v14.py" %*
if errorlevel 1 (
 echo ECHEC SECURISE : aucune modification canonique.
 pause
 exit /b 2
)
echo.
echo SUCCES : semantic_stage_v14_editorial sur D:.
echo Aucune approbation KS/KQ/KP/KA ni publication GitHub.
pause
