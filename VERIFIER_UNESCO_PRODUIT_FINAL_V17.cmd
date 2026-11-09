@echo off
setlocal
chcp 65001 >nul
echo UNESCO V17 - Verifier les portes obligatoires de produit final.
python "%~dp0tools\unesco_pilot\final_product_pipeline_v17.py" --require-final %*
if errorlevel 1 (echo Aucune publication; controles de qualification requis. & pause & exit /b 2)
pause
ENDLOCAL
