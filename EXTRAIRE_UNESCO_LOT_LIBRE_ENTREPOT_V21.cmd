@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "LOT=%~dp0..\mediatheque-references\tools\wiki\atlas\extraire_lots_xml_v21.py"
if "%~2"=="" (
 echo UTILISATION : %~nx0 "C:\chemin\selection_003.csv" "D:\chemin\LOT_003_CHATGPT.zip"
 echo La selection doit contenir 1 a 100 pages deja presentes dans l'atlas v19.
 exit /b 2
)
where py >nul 2>nul
if errorlevel 1 (set "PY=python") else (set "PY=py -3")
%PY% "%~dp0tools\unesco_pilot\verifier_overlay_entrepot_v21.py"
if errorlevel 1 goto :err
%PY% "%LOT%" preflight --future-lot --selection "%~1" --output "%~2"
if errorlevel 1 goto :err
%PY% "%LOT%" build --future-lot --selection "%~1" --output "%~2"
if errorlevel 1 goto :err
echo SUCCES : nouveau lot prive cree sans canon.
exit /b 0
:err
echo ECHEC : aucun lot valide publie.
exit /b 2
