@echo off
setlocal EnableExtensions
title Konstellation - Tests Playwright

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "PLAYWRIGHT_PORT=4323"

if exist "C:\Program Files\nodejs\node.exe" set "PATH=C:\Program Files\nodejs;%PATH%"
where node >nul 2>nul || (echo [ERROR] Node.js introuvable. & goto :fail)
where npm >nul 2>nul || (echo [ERROR] npm introuvable. & goto :fail)

for /f "delims=" %%V in ('node --version') do set "NODE_VERSION=%%V"
set "NODE_VERSION_NUM=%NODE_VERSION:v=%"
for /f "tokens=1 delims=." %%M in ("%NODE_VERSION_NUM%") do set "NODE_MAJOR=%%M"
if %NODE_MAJOR% LSS 24 (
  echo [ERROR] Node.js 24.15 ou plus recent est requis. Version actuelle: %NODE_VERSION%
  goto :fail
)

pushd "%ROOT%"
if not exist "package.json" (echo [ERROR] package.json introuvable. & popd & goto :fail)
if not exist "data\theophile-biblical.enriched.pack.json" (
  echo [ERROR] data\theophile-biblical.enriched.pack.json introuvable.
  popd
  goto :fail
)
if not exist "node_modules" (
  echo Installation des dependances...
  call npm install
  if errorlevel 1 (popd & goto :fail)
)

echo Verification de Chromium Playwright...
call npx playwright install chromium
if errorlevel 1 (popd & goto :fail)

echo.
echo Verification du corpus biblique local...
node scripts\prepare-playwright-corpus.mjs
if errorlevel 1 (popd & goto :fail)

if /I "%~1"=="smoke" goto :smoke
if /I "%~1"=="astrolabe" goto :astrolabe
if /I "%~1"=="ui" goto :ui
if /I "%~1"=="report" goto :report
if /I "%~1"=="full" goto :full

echo.
echo ============================================================
echo   KONSTELLATION - PLAYWRIGHT
echo ============================================================
echo   1. Test rapide ^(demarrage + API^)
echo   2. Astrolabe seulement
echo   3. Suite complete ^(recommande^)
echo   4. Mode interactif Playwright UI
echo   5. Ouvrir le dernier rapport
echo   Q. Quitter
echo.
choice /C 12345Q /N /M "Choix: "
if errorlevel 6 (popd & exit /b 0)
if errorlevel 5 goto :report
if errorlevel 4 goto :ui
if errorlevel 3 goto :full
if errorlevel 2 goto :astrolabe
if errorlevel 1 goto :smoke

:smoke
call npm run test:e2e:smoke
set "RC=%ERRORLEVEL%"
goto :done

:astrolabe
call npm run test:e2e:astrolabe
set "RC=%ERRORLEVEL%"
goto :done

:full
call npm run test:e2e
set "RC=%ERRORLEVEL%"
goto :done

:ui
set "PLAYWRIGHT_HEADED=1"
call npm run test:e2e:ui
set "RC=%ERRORLEVEL%"
goto :done

:report
if exist "%ROOT%\playwright-report\index.html" (
  start "" "%ROOT%\playwright-report\index.html"
  set "RC=0"
) else (
  echo Aucun rapport Playwright trouve.
  set "RC=1"
)
goto :done

:done
if exist "%ROOT%\playwright-report\index.html" start "" "%ROOT%\playwright-report\index.html"
echo.
if "%RC%"=="0" (
  echo [OK] Tests termines sans echec.
) else (
  echo [ECHEC] Au moins un test a echoue. Le rapport HTML contient traces, captures et videos.
)
popd
pause
endlocal & exit /b %RC%

:fail
echo.
echo Impossible de lancer les tests.
pause
endlocal & exit /b 1
