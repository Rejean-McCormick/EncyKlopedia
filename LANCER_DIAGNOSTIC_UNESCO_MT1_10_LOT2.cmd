@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if %ERRORLEVEL%==0 (
 py -3 "tools\unesco_pilot\lot2_preflight.py" --root "C:\mycode"
) else (
 python "tools\unesco_pilot\lot2_preflight.py" --root "C:\mycode"
)
set EXITCODE=%ERRORLEVEL%
echo.
if %EXITCODE% EQU 0 (
 echo Verification des composants terminee. LA PUBLICATION RESTE BLOQUEE.
) else (
 echo Certains composants ou contrats manquent. Verifier le rapport ci-dessus.
)
pause
exit /b %EXITCODE%
