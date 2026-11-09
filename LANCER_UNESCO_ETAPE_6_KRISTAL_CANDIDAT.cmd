@echo off
setlocal
chcp 65001 >nul
set "HERE=%~dp0"
set "TOOL=%HERE%tools\unesco_pilot\semantic_candidate_stage_v6.py"
set "WORK=D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41"
echo.
echo ============================================================
echo ETAPE 6 - Graphe de revue UNESCO Educational Policy
echo 41 concepts, 85 propositions, 234 liens SKOS - SUR D: UNIQUEMENT
echo AUCUN KQ/KP/KA/KS canonique, AUCUN envoi GitHub
echo ============================================================
echo.
where py >nul 2>&1
if errorlevel 1 (
echo ERREUR: lanceur Python py introuvable.
 pause
 exit /b 2
)
py -3 "%TOOL%" --work "%WORK%"
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" (
echo ETAPE 6 BLOQUEE. Aucune donnee canonique modifiee.
) else (
echo SUCCES - Voir %WORK%\semantic_stage_v6\RAPPORT_ETAPE6.json
echo Aucune publication GitHub, aucune activation canonique.
)
pause
exit /b %RC%
