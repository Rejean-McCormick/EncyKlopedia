@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>&1
if errorlevel 1 (echo Node.js 22+ requis.&pause&exit /b 2)
node tools\dictionary-harvester\verify-overlay.mjs
if errorlevel 1 (echo Erreur integrite overlay.&pause&exit /b 1)
call npm run verify
if errorlevel 1 (echo Erreur tests.&pause&exit /b 1)
if not defined ENCYK_DATA_ROOT set "ENCYK_DATA_ROOT=D:\EncyKlopedia"
node tools\dictionary-harvester\cli.mjs layout
if errorlevel 1 (echo [ATTENTION] Arborescence D: indisponible.&pause&exit /b 2)
where py >nul 2>&1
if not errorlevel 1 (
  py -3 -m unittest discover -s tests -p test_lexical_indexer.py -q
) else (
  where python >nul 2>&1
  if errorlevel 1 (echo [ERREUR] Python 3.10+ requis.&pause&exit /b 2)
  python -m unittest discover -s tests -p test_lexical_indexer.py -q
)
if errorlevel 1 (echo [ERREUR] Tests d'indexation echoues.&pause&exit /b 1)
echo OK: code sur C:, donnees sur D:; indexation candidate verifiee.
pause
endlocal
