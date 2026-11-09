@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "WIKIDB=D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite"
set "WORK=D:\EncyKlopedia\30_working\unesco_mt1_10"
set "SPEK=C:\mycode\Spek_Semantic-publishing\Spek"
if not exist "%WIKIDB%" (
  echo Index Wikipedia absent: "%WIKIDB%"
  pause
  exit /b 2
)
echo.
echo Projet: UNESCO Educational policy, 41 concepts, 14 langues cibles.
echo Sortie PRIVEe et NON CANONIQUE. Aucune publication GitHub.
echo.
set /p "SCOPE=Chemin complet du ZIP UNESCO-Educational-Policy-Scope-EN : "
set "SCOPE=%SCOPE:"=%"
if not exist "%SCOPE%" (
  echo ZIP introuvable.
  pause
  exit /b 2
)
py -3 "%~dp0tools\unesco_pilot\local_wikipedia_bridge.py" plan --scope-zip "%SCOPE%" --db "%WIKIDB%"
if errorlevel 1 (
  echo Precontrole REFUSE. Aucun fichier de sortie.
  pause
  exit /b 2
)
set /p "GO=Produire la file de preparation privee ? (O/N) : "
if /I not "%GO%"=="O" exit /b 0
for /f %%a in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "STAMP=%%a"
set "INV=%WORK%\inventory-%STAMP%.json"
set "QUEUE=%WORK%\spek-queue-%STAMP%.json"
py -3 "%~dp0tools\unesco_pilot\local_wikipedia_bridge.py" build --scope-zip "%SCOPE%" --db "%WIKIDB%" --out "%INV%"
if errorlevel 1 goto :error
if not exist "%SPEK%\spek\unesco_pilot.py" (
  echo Spek non corrige: dossier absent. Inventaire prive conserve: "%INV%"
  pause
  exit /b 2
)
pushd "%SPEK%"
py -3 -m spek.unesco_pilot --inventory "%INV%" --out "%QUEUE%"
set "CODE=%ERRORLEVEL%"
popd
if not "%CODE%"=="0" goto :error
echo.
echo Inventaire prive: "%INV%"
echo File de 574 projections BLOQUEES: "%QUEUE%"
echo 0 articles publies; aucun depot distant modifie.
pause
exit /b 0
:error
echo Echec controle: aucune publication lancee.
pause
exit /b 2
