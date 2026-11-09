@echo off
setlocal
chcp 65001 >nul
echo UNESCO V17 - Audit du produit prive existant, aucune ecriture.
python "%~dp0tools\unesco_pilot\final_product_pipeline_v17.py" --check-only %*
if errorlevel 1 (pause & exit /b 2)
pause
ENDLOCAL
