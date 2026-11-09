@echo off
setlocal
set "INDEX=D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41\semantic_stage_v17_integrated_product\reader_en\index.html"
if not exist "%INDEX%" (
 echo Produit V17 non encore construit. Lancer LANCER_UNESCO_PRODUIT_INTEGRE_V17.cmd.
 pause
 exit /b 2
)
start "" "%INDEX%"
ENDLOCAL
