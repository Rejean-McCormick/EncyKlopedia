@echo off
setlocal
set "TOOL=%~dp0..\mediatheque-references\tools\wiki\atlas\atlas_wikipedia.py"
where py >nul 2>nul
if errorlevel 1 (set "PY=python") else (set "PY=py -3")
echo Cree un nouveau lot selon la selection CSV de l'atlas.
echo Si l'index multistream existe, tente l'extraction sans scanner tout le XML.
echo IMPORTANT : pour un deuxieme lot, utiliser --output avec un NOUVEAU nom.
%PY% "%TOOL%" pack --limit 100 --try-multistream %*
if errorlevel 1 (echo EXTRACTION PARTIELLE OU LOT DIFFERENT : voir diagnostic) else (echo LOT PREPARE)
pause
