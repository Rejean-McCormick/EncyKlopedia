@echo off
setlocal
set "SCRIPT=%~dp0tools\unesco_pilot\overlay_probatoire_v23.py"
echo ===============================================
echo UNESCO V23 - ARCHIVAGE DE SOURCES PRIVEES
 echo Les copies HTTP ne valent pas validation juridique.
echo Des URLs peuvent refuser le telechargement.
echo ===============================================
python -I "%SCRIPT%" capture
if errorlevel 1 (echo V23_CAPTURE_ERREUR & exit /b 2)
echo V23_CAPTURE_TERMINEE_VOIR_NOMBRE_DE_SUCCES
exit /b 0
