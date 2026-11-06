@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>&1
if errorlevel 1 (echo Node.js 22+ requis.&pause&exit /b 2)
if not defined ENCYK_DATA_ROOT set "ENCYK_DATA_ROOT=D:\EncyKlopedia"
if not exist "%ENCYK_DATA_ROOT%\10_sources\lexical\" (
  echo [ERREUR] Racine des donnees introuvable: %ENCYK_DATA_ROOT%
  echo Aucun dossier ne sera cree sur C: ou D:.
  pause
  exit /b 2
)
echo [Code] %CD%
echo [Donnees] %ENCYK_DATA_ROOT%
node tools\dictionary-harvester\cli.mjs layout
if errorlevel 1 (echo [ERREUR] Structure D: non valide.&pause&exit /b 2)
node tools\dictionary-harvester\cli.mjs sources
if errorlevel 1 (echo [ERREUR] Echec du registre.&pause&exit /b 1)
echo.
echo Pour voir les dumps deja sur D:, utiliser :
echo node tools\dictionary-harvester\cli.mjs inventory-existing
echo.
echo Pour INDEXER tous les fichiers existants : Start_Indexation_Dictionnaires.cmd
pause
endlocal
