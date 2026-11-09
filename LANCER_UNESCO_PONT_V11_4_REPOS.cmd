@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo UNESCO - PONT DE VALIDATION V11 (4 vrais depots)
echo 41 concepts / 191 decisions / Kristal unique - PRIVE
 echo AUCUN enable-v11 / build-v9 / creation KQ-KP-KA-KS / GitHub
 echo ============================================================
python "%~dp0tools\unesco_pilot\canonical_bridge_v13.py" %*
if errorlevel 1 (
 echo.
 echo ECHEC SECURISE : aucun canon, aucune publication.
 pause
 exit /b 2
)
echo.
echo SUCCES : verifier semantic_stage_v13_bridge sous D:.
echo AUCUNE approbation canonique automatique.
pause
