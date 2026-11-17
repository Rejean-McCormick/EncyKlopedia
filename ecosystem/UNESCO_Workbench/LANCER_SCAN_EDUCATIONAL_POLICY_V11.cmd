@echo off
setlocal
set "ROOT=%~dp0"
set "KRISTALIZER=C:\mycode\Kristal\Kristalizer\kristalizer.py"
set "SOURCE=%ROOT%candidates\educational-policy-en-v11"
set "OUTPUT=%ROOT%reports\educational-policy-v11"
set "INDEX=D:\EncyKlopedia\30_working\wikidata\wikidata.compact.sqlite"
if not exist "%KRISTALIZER%" (
 echo [ERREUR] Kristalizer absent : %KRISTALIZER%
 pause
 exit /b 2
)
if not exist "%INDEX%" (
 echo [INFO] Index absent ; scan des crosswalks uniquement.
 py -3 "%KRISTALIZER%" scan --source "%SOURCE%" --output "%OUTPUT%" --max-results 12
) else (
 py -3 "%KRISTALIZER%" scan --source "%SOURCE%" --output "%OUTPUT%" --index "%INDEX%" --max-results 12
)
if errorlevel 1 (
 echo [ERREUR] Scan en echec.
 pause
 exit /b 1
)
echo.
echo Resultat : %OUTPUT%\ANALYSE\RAPPORT.json
pause
