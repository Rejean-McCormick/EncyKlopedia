@echo off
setlocal
set "SCRIPT=%~dp0tools\unesco_pilot\overlay_probatoire_v23.py"
if not exist "%SCRIPT%" (echo ERREUR : moteur v23 introuvable & exit /b 2)
echo ===============================================
echo UNESCO V23 - CORRECTIONS PROBATOIRES PRIVEES
echo Aucun Kristal canonique ni publication.
echo ===============================================
python -I "%SCRIPT%" preflight
if errorlevel 1 (echo V23_PRECONTROLE_REFUSE & exit /b 2)
python -I "%SCRIPT%" apply
if errorlevel 1 (echo V23_APPLICATION_REFUSEE & exit /b 2)
python -I "%SCRIPT%" verify
if errorlevel 1 (echo V23_VERIFICATION_REFUSEE & exit /b 2)
echo V23_APPLICATION_ET_CONTROLE_OK
exit /b 0
