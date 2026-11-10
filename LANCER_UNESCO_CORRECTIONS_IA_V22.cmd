@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (set "PY=python") else (set "PY=py -3")
echo ===============================================================
echo UNESCO V22 - CORRECTIONS EDITORIALES IA / 44 PROPOSITIONS
echo Aucun fichier preexistant remplace; aucune admission canonique.
echo ===============================================================
%PY% "%~dp0tools\unesco_pilot\overlay_ia_v22.py" apply
if errorlevel 1 (
  echo ECHEC / REFUS - aucune canonisation. Lire le message ci-dessus.
) else (
  echo REUSSITE - resultat dans D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41\semantic_stage_v22_revue_ia
)
pause
