@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
set "PYEXE=py"
set "SCRIPT=%~dp0tools\unesco_pilot\automated_local_pilot.py"
if not exist "%SCRIPT%" (
  echo ERREUR: autopilote UNESCO introuvable: "%SCRIPT%"
  pause
  exit /b 2
)
echo.
echo ============================================================
echo UNESCO Educational Policy - concept10 puis 41 concepts
 echo Inventaire et dossiers de recherche LOCAUX uniquement
 echo Zero publication, zero creation canonique KQ/KA/KS
 echo ============================================================
echo.
if "%~1"=="" (
  py -3 "%SCRIPT%" run --root "C:\mycode"
) else (
  py -3 "%SCRIPT%" run --root "C:\mycode" --scope-zip "%~1"
)
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
 echo Etapes terminees ou deja presentes.
 echo Dossier: D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41
 echo Aucun article publie. Aucun push GitHub.
) else (
 echo Traitement interrompu. Consulter journal_autopilote.log dans le dossier de travail.
 echo Relancer CE MEME FICHIER pour reprendre les etapes terminees.
)
echo.
pause
exit /b %RC%
