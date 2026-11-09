@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo UNESCO V16 - recherche registre v11 et preuves locales
 echo 41 concepts, v15 conservee, aucun canon ni GitHub
 echo ============================================================
python "%~dp0tools\unesco_pilot\registry_provenance_v16.py" %*
if errorlevel 1 (
 echo ECHEC : aucun fichier canonique ni publication modifies.
) else (
 echo SUCCES : voir semantic_stage_v16_identites_preuves sur D:.
)
pause
