@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "INDEX=%~dp0..\mediatheque-references\tools\wiki\atlas\index_xml_v21.py"
set "LOT=%~dp0..\mediatheque-references\tools\wiki\atlas\extraire_lots_xml_v21.py"
set "VERIFY=%~dp0tools\unesco_pilot\verifier_overlay_entrepot_v21.py"
where py >nul 2>nul
if errorlevel 1 (set "PY=python") else (set "PY=py -3")
echo ===============================================================
echo UNESCO / ENCYKLOPEDIA V21 - ENTREPOT WIKIPEDIA HAUTE PERFORMANCE
echo ===============================================================
echo XML decompresse D: 109.75 GiB EN LECTURE SEULE.
echo Construction d'un index direct des pages, reprise automatique.
echo Graphe SQL v19, archive bz2, Mediatheque et Kristal INCHANGES.
echo Arret propre avec Ctrl+C et reprise avec CE MEME lanceur.
echo ===============================================================
%PY% "%VERIFY%"
if errorlevel 1 goto :err
%PY% "%INDEX%" preflight
if errorlevel 1 goto :err
%PY% "%INDEX%" index
if errorlevel 1 goto :err
%PY% "%INDEX%" audit --require-complete
if errorlevel 1 goto :err
%PY% "%INDEX%" catalogue
if errorlevel 1 goto :err
%PY% "%LOT%" preflight
if errorlevel 1 goto :err
%PY% "%LOT%" build
if errorlevel 1 goto :err
echo.
echo SUCCES V21. Transmettre atlas_documentaire_v19_LOT_002_CHATGPT_V21.zip.
echo La prochaine execution reutilise l'index; elle ne relit pas les 110 GiB.
pause
exit /b 0
:err
echo.
echo ECHEC OU INTERRUPTION V21. Ne rien effacer : relancer pour reprendre.
echo Pour voir le checkpoint : AUDITER_WIKIPEDIA_ENTREPOT_V21.cmd
pause
exit /b 2
