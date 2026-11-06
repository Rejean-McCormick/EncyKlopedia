@echo off
setlocal
cd /d "%~dp0"
if not defined ENCYK_DATA_ROOT set "ENCYK_DATA_ROOT=D:\EncyKlopedia"
if not exist "%ENCYK_DATA_ROOT%\10_sources\lexical\" (
  echo [ERREUR] Donnees lexicales absentes sur D: : %ENCYK_DATA_ROOT%
  pause
  exit /b 2
)
where node >nul 2>&1
if errorlevel 1 (echo [ERREUR] Node.js 22+ requis.&pause&exit /b 2)
echo =====================================================
echo    ENCYKLOPEDIA - INDEXATION LEXICALE C: / D:
echo =====================================================
echo [Code] %CD%
echo [Donnees] %ENCYK_DATA_ROOT%
echo [Sources] Kaikki + UniMorph + Wikidata Lexemes
node tools\dictionary-harvester\cli.mjs index-plan
if errorlevel 1 (echo [ERREUR] Plan impossible.&pause&exit /b 2)
echo.
echo Debut/reprise de l'indexation automatique locale.
echo Utiliser Ctrl+C pour interrompre : le dernier checkpoint est garde.
node tools\dictionary-harvester\cli.mjs index-run
set "EXIT_CODE=%ERRORLEVEL%"
echo.
echo Pour consulter le rapport :
echo %ENCYK_DATA_ROOT%\30_working\lexical\harvester\index-v1\latest.json
node tools\dictionary-harvester\cli.mjs index-status
if not "%EXIT_CODE%"=="0" echo [ATTENTION] Traitement partiel, en erreur ou sources modifiees. Voir sources.csv.
pause
exit /b %EXIT_CODE%
