@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "TOOL=%~dp0..\mediatheque-references\tools\wiki\atlas\atlas_wikipedia.py"
if not exist "%TOOL%" (
  echo ERREUR : atlas absent : "%TOOL%"
  pause
  exit /b 2
)
where py >nul 2>nul
if errorlevel 1 (set "PY=python") else (set "PY=py -3")
echo ================================================================
echo UNESCO - ATLAS LOCAL WIKIPEDIA EN / LOTS POUR CHATGPT [v19]
echo Graphe documentaire prive : SQLite D: en lecture seule
echo AUCUN reimport SQL, aucune publication, aucun nouveau KQ/KA/KS
echo ================================================================
%PY% "%~dp0tools\unesco_pilot\verifier_overlay_atlas_v19.py" "%~dp0..\.."
if errorlevel 1 goto :err
%PY% "%TOOL%" build
if errorlevel 1 goto :err
%PY% "%TOOL%" audit
if errorlevel 1 goto :err
%PY% "%TOOL%" index-zip
if errorlevel 1 goto :err
%PY% "%TOOL%" pack --limit 100
if errorlevel 1 goto :err
 echo.
 echo SUCCES. Envoyer en premier le ZIP *_INDEX_POUR_CHATGPT.zip.
 echo Le ZIP *_LOT_001_CHATGPT.zip contient les textes deja extraits.
 echo La selection des autres pages se fera a partir de l'atlas.
 pause
exit /b 0
:err
 echo.
 echo ECHEC : verifier les messages ci-dessus. Aucune base modifiee.
 pause
exit /b 2
