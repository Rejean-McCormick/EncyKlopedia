@echo off
setlocal
where py >nul 2>nul
if errorlevel 1 (set "PY=python") else (set "PY=py -3")
%PY% "%~dp0tools\unesco_pilot\verifier_overlay_atlas_v19.py" "%~dp0..\.."
if errorlevel 1 (echo ERREUR INTEGRITE - Ne pas lancer l'atlas) else (echo Fichiers overlay conformes)
pause
