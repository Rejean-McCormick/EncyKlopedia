@echo off
setlocal
chcp 65001 >nul
echo ============================================================
echo UNESCO V17 - GROSSE PASSE DU PRODUIT INTEGRE PRIVE
echo Workbench 41 KQ provisoires + 85 textes + lecteur 41 pages
echo Kit v11, GF, preuves, admission C1-C4 : controles reels
echo AUCUNE canonisation implicite, aucune publication GitHub
echo ============================================================
set "SCRIPT=%~dp0tools\unesco_pilot\final_product_pipeline_v17.py"
python "%SCRIPT%" %*
if errorlevel 1 (
 echo.
 echo BLOQUE : aucune sortie canonique ni publication effectuee.
 pause
 exit /b 2
)
echo.
echo SUCCES : produit prive pret. Voir reader_en\index.html dans le dossier V17 sur D:.
pause
ENDLOCAL
