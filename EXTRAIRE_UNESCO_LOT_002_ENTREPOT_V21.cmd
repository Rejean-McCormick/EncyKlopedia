@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "LOT=%~dp0..\mediatheque-references\tools\wiki\atlas\extraire_lots_xml_v21.py"
where py >nul 2>nul
if errorlevel 1 (set "PY=python") else (set "PY=py -3")
%PY% "%~dp0tools\unesco_pilot\verifier_overlay_entrepot_v21.py"
if errorlevel 1 goto :err
%PY% "%LOT%" preflight
if errorlevel 1 goto :err
%PY% "%LOT%" build
if errorlevel 1 goto :err
echo SUCCES : ZIP UNESCO LOT 002 V21 disponible.
pause
exit /b 0
:err
echo ECHEC : index V21 complet ou atlas V19 manquant.
pause
exit /b 2
