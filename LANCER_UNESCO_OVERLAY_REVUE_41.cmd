@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo UNESCO - OVERLAY de code EncyKlopedia + Kristalizer
echo 41 concepts, 85 recommandations, aucun canon ni GitHub
echo ============================================================
python "%~dp0tools\unesco_pilot\review_global_overlay_v12.py"
if errorlevel 1 goto :failure
python "C:\mycode\Kristal\Kristalizer\tools\unesco_global_review_gate.py"
if errorlevel 1 goto :failure
echo.
echo SUCCES : revue raccordee aux deux depots. Admission canonique BLOQUEE.
pause
exit /b 0
:failure
echo.
echo ECHEC SECURISE : rien de canonique n'a ete cree ou publie.
pause
exit /b 1
