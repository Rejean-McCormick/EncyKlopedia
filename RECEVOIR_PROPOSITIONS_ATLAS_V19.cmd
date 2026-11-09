@echo off
setlocal
set "TOOL=%~dp0tools\unesco_pilot\recevoir_lots_atlas_v19.py"
where py >nul 2>nul
if errorlevel 1 (set "PY=python") else (set "PY=py -3")
if "%~2"=="" (
 echo Usage : RECEVOIR_PROPOSITIONS_ATLAS_V19.cmd "C:\lot.zip" "C:\propositions_chatgpt.json"
 pause
 exit /b 2
)
%PY% "%TOOL%" intake --batch "%~1" --proposals "%~2"
if errorlevel 1 (echo RECEPTION REFUSEE : provenance incoherente) else (echo Candidats conserves en dossier prive.)
pause
