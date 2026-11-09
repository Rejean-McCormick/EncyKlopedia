@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "TOOL=%~dp0..\mediatheque-references\tools\wiki\atlas\extraire_lots_v20.py"
if not exist "%TOOL%" (
 echo ECHEC - module de l'extraction UNESCO V20 absent: "%TOOL%"
 pause
 exit /b 2
)
where py >nul 2>nul
if errorlevel 1 (set "PY=python") else (set "PY=py -3")
echo ==================================================================
echo UNESCO V20 - EXTRACTION DU LOT 002 / 25 ARTICLES WIKIPEDIA EN
echo ==================================================================
echo Source XML D: LECTURE SEULE; base Wikipedia SQL LECTURE SEULE.
echo Si index multistream absent : reconstruction LOCALE et REPRENABLE.
echo Aucun KS, KQ, KP, KA canonique, ni publication GitHub.
echo ==================================================================
%PY% "%~dp0tools\unesco_pilot\verifier_overlay_extraction_v20.py"
if errorlevel 1 goto :err
%PY% "%TOOL%" preflight %*
if errorlevel 1 goto :err
%PY% "%TOOL%" build %*
if errorlevel 1 goto :err
echo.
echo SUCCES : transmettre atlas_documentaire_v19_LOT_002_CHATGPT.zip.
echo Les 25 wikitexts doivent figurer dans le ZIP ; aucune publication.
pause
exit /b 0
:err
echo.
echo Le lot n'est PAS complet. Si un checkpoint existe, relancer ce lanceur.
echo Si le XML est introuvable, voir le diagnostic ou preciser --xml "CHEMIN".
pause
exit /b 2
