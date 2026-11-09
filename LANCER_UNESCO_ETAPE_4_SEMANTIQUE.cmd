@echo off
setlocal
chcp 65001 >nul
set "PY=py"
where py >nul 2>nul
if errorlevel 1 set "PY=python"
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
echo.
echo ============================================================
echo UNESCO Educational Policy - ETAPE 4: candidats semantiques
echo Base: 41 dossiers deja extraits ; PAS de nouveau scan XML
echo Zero KQ/KA/KS canonique ; zero publication GitHub
echo ============================================================
echo.
if /i "%PY%"=="py" (
  py -3 "%~dp0tools\unesco_pilot\lot4_preflight.py" --root "%ROOT%"
) else (
  python "%~dp0tools\unesco_pilot\lot4_preflight.py" --root "%ROOT%"
)
if errorlevel 1 goto fail
if /i "%PY%"=="py" (
  py -3 "%~dp0tools\unesco_pilot\semantic_candidate_stage_v4.py" %*
) else (
  python "%~dp0tools\unesco_pilot\semantic_candidate_stage_v4.py" %*
)
if errorlevel 1 goto fail
echo.
echo FIN. Voir semantic_stage_v4\manifest.json dans le dossier sur D:
echo Rien n'a ete envoye a GitHub.
pause
exit /b 0
:fail
echo.
echo ETAPE 4 BLOQUEE. Aucune publication.
pause
exit /b 2
