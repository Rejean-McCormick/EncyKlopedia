@echo off
setlocal EnableExtensions
title Konstellation - Explorateur de Kristals

rem ============================================================
rem Konstellation portable launcher
rem - Explicit reader first, then opted-in legacy collection, then local reader
rem - Theophile remains a demo, never an implicit choice when a local reader exists
rem Place this file in the repository root, beside package.json.
rem ============================================================

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "PORT=4321"
set "LOCAL_PACK=%ROOT%\data\theophile-biblical.enriched.pack.json"
set "LOCAL_LENSES=%ROOT%\lenses-enriched"
set "BACKEND_CONFIG=%ROOT%\examples\integrations\kristal-kollection.json"
set "ACTIVE_READER_CONFIG=%ROOT%\config\local-catalog.json"
set "COLLECTION_DOMAINS=%ROOT%\..\kristals\domains"
set "MODE=local"
rem Démarrage neutre : catalogue local. Pas de lecture automatique de Catho/Théophile.
rem A local reader is an operator-supplied JSON config, not an automatic filesystem scan.
if not exist "%ACTIVE_READER_CONFIG%" (
    echo [ERROR] Catalogue local introuvable: %ACTIVE_READER_CONFIG%
    goto :fail
)
set "BACKEND_CONFIG=%ACTIVE_READER_CONFIG%"
set "MODE=configured"

echo.
echo ============================================================
echo   Konstellation - Explorateur de connaissances
echo ============================================================
echo Repo : %ROOT%
if /I "%MODE%"=="kristals" (
    echo Mode : Kristal-Kollection ^(selection dans l'interface^)
    echo Collection : %ROOT%\..\kristals
) else if /I "%MODE%"=="configured" (
    echo Mode : selection neutre dans Mes Kristals
) else (
    echo Mode : corpus local enrichi
)
echo.

if not exist "%ROOT%\package.json" (
    echo [ERROR] package.json not found.
    goto :fail
)

if /I "%MODE%"=="kristals" (
    if not exist "%BACKEND_CONFIG%" (
        echo [ERROR] Kristal collection backend config not found:
        echo         %BACKEND_CONFIG%
        goto :fail
    )
    if not exist "%COLLECTION_DOMAINS%" (
        echo [ERROR] Kristal collection not found:
        echo         %COLLECTION_DOMAINS%
        goto :fail
    )
) else if /I "%MODE%"=="configured" (
    if not exist "%BACKEND_CONFIG%" (
        echo [ERROR] Explicit backend configuration not found: %BACKEND_CONFIG%
        goto :fail
    )
) else (
    if not exist "%LOCAL_PACK%" (
        echo [ERROR] Enriched local pack not found:
        echo         %LOCAL_PACK%
        echo Legacy collection mode needs KONSTELLATION_USE_LEGACY_KOLLECTION=true.
        goto :fail
    )
    if not exist "%LOCAL_LENSES%" (
        echo [ERROR] Enriched lenses not found:
        echo         %LOCAL_LENSES%
        goto :fail
    )
)

rem Prefer the known portable Node 24 installation. Do not change the system PATH.
if exist "C:\mycode\Tools\node24\node.exe" (
    set "PATH=C:\mycode\Tools\node24;%PATH%"
) else if exist "C:\Program Files\nodejs\node.exe" (
    set "PATH=C:\Program Files\nodejs;%PATH%"
)

where node >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js was not found.
    echo Konstellation requires Node.js 24.15 or newer.
    goto :fail
)
where npm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] npm was not found.
    goto :fail
)

for /f "delims=" %%V in ('node --version') do set "NODE_VERSION=%%V"
for /f "delims=" %%V in ('npm --version') do set "NPM_VERSION=%%V"
set "NODE_VERSION_NUM=%NODE_VERSION:v=%"
for /f "tokens=1,2 delims=." %%M in ("%NODE_VERSION_NUM%") do (set "NODE_MAJOR=%%M" & set "NODE_MINOR=%%N")

echo Node : %NODE_VERSION%
echo npm  : %NPM_VERSION%
if /I "%MODE%"=="kristals" (
    echo Lecteur : %BACKEND_CONFIG%
) else if /I "%MODE%"=="configured" (
    echo Lecteur : %BACKEND_CONFIG%
) else (
    echo Pack : %LOCAL_PACK%
    echo Lenses: %LOCAL_LENSES%
)
echo.

if not defined NODE_MAJOR goto :badnode
if %NODE_MAJOR% LSS 24 goto :badnode
if %NODE_MAJOR% EQU 24 if %NODE_MINOR% LSS 15 goto :badnode

if /I "%MODE%"=="kristals" (
    set "KONSTELLATION_BACKEND_CONFIG=%BACKEND_CONFIG%"
    set "KONSTELLATION_PACK="
    set "KONSTELLATION_LENSES="
) else if /I "%MODE%"=="configured" (
    set "KONSTELLATION_BACKEND_CONFIG=%BACKEND_CONFIG%"
    set "KONSTELLATION_PACK="
    set "KONSTELLATION_LENSES="
    set "KONSTELLATION_ENABLE_MY_KRISTALS=true"
) else (
    set "KONSTELLATION_BACKEND_CONFIG="
    set "KONSTELLATION_PACK=%LOCAL_PACK%"
    set "KONSTELLATION_LENSES=%LOCAL_LENSES%"
)
rem Le catalogue local n'est accessible que depuis un serveur prive sur loopback.
rem Fixer explicitement le meme profil que server/config.mjs pour eviter un
rem environnement herite (HOST/public) ou ambigu.
set "KONSTELLATION_DEPLOYMENT_PROFILE=local"
set "HOST=127.0.0.1"
set "KONSTELLATION_ANONYMOUS_READONLY=false"
set "KONSTELLATION_PUBLIC_READONLY=false"
set "KONSTELLATION_SA_CONFIG="

rem Stop previous Konstellation instances on this port, but never unrelated apps.
rem New launches have an absolute server script path. Older npm launches
rem used a relative path and must also pass the Konstellation health check.
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop'; $port=%PORT%; $root=$env:ROOT;" ^
  "$listeners=@(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue);" ^
  "if($listeners.Count -eq 0){exit 0};" ^
  "$owners=@($listeners | Select-Object -ExpandProperty OwningProcess -Unique);" ^
  "if($owners.Count -ne 1){Write-Host '[ERROR] Multiple processes are listening on this port. Nothing stopped.';exit 3};" ^
  "$ownerPid=[int]$owners[0]; $p=Get-CimInstance Win32_Process -Filter ('ProcessId=' + $ownerPid) -ErrorAction SilentlyContinue;" ^
  "if(-not $p){Write-Host '[ERROR] Cannot identify the port owner. Nothing stopped.';exit 3};" ^
  "$line=[string]$p.CommandLine; $expected=[IO.Path]::Combine($root,'server','index.mjs');" ^
  "$current=($p.Name -ieq 'node.exe') -and ($line.IndexOf($expected,[StringComparison]::OrdinalIgnoreCase) -ge 0);" ^
  "$legacy=($p.Name -ieq 'node.exe') -and ($line -match '(^|\s)server[\\/]index\.mjs(\s|$)');" ^
  "if($legacy -and -not $current){try{$health=Invoke-RestMethod -Uri ('http://127.0.0.1:' + $port + '/api/health') -TimeoutSec 3; $legacy=($health.status -eq 'ok' -and -not [string]::IsNullOrWhiteSpace([string]$health.version))}catch{$legacy=$false}};" ^
  "if(-not ($current -or $legacy)){Write-Host ('[ERROR] Port ' + $port + ' belongs to an unverified app (PID ' + $ownerPid + '). Nothing stopped.');exit 3};" ^
  "Write-Host ('Stopping previous Konstellation instance (PID ' + $ownerPid + ')...');" ^
  "try{Stop-Process -Id $ownerPid -Force -ErrorAction Stop}catch{Write-Host ('[ERROR] Cannot stop PID ' + $ownerPid + ': ' + $_.Exception.Message);exit 3};" ^
  "for($i=0;$i -lt 30;$i++){Start-Sleep -Milliseconds 200;$busy=@(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue);if($busy.Count -eq 0){exit 0}};" ^
  "Write-Host '[ERROR] Port still occupied after stopping old Konstellation instance.';exit 3"
if errorlevel 1 goto :portbusy

pushd "%ROOT%"
if not exist "node_modules" (
    echo.
    echo First launch: installing dependencies...
    call npm install
    if errorlevel 1 (popd & goto :fail)
)

echo.
echo Building Konstellation...
call npm run build
if errorlevel 1 (popd & goto :fail)

echo.
echo Starting Konstellation - choisissez un Kristal dans l interface...
echo URL : http://127.0.0.1:%PORT%
if /I "%MODE%"=="kristals" (
    echo Kristal selector: enabled
) else if /I "%MODE%"=="configured" (
    echo Lecteur: %BACKEND_CONFIG%
) else (
    echo Corpus: Theophile v0.2.1 + Graphe biblique enrichi
)
echo.

start "" /B powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -Command ^
  "$u='http://127.0.0.1:%PORT%';" ^
  "for($i=0;$i -lt 80;$i++){" ^
  "  try{" ^
  "    $r=Invoke-WebRequest -Uri ($u + '/api/health') -UseBasicParsing -TimeoutSec 1;" ^
  "    if($r.StatusCode -ge 200 -and $r.StatusCode -lt 500){ Start-Process $u; exit 0 }" ^
  "  }catch{}; Start-Sleep -Milliseconds 250" ^
  "}; Start-Process $u"

rem Run Node directly with an absolute script path to identify future instances safely.
node "%ROOT%\server\index.mjs"
set "RC=%ERRORLEVEL%"
popd
if not "%RC%"=="0" goto :fail
endlocal
exit /b 0

:badnode
echo [ERROR] Node.js 24.15 or newer is required. Current: %NODE_VERSION%
goto :fail

:portbusy
echo [ERROR] Port %PORT% could not be freed safely.
goto :fail

:fail
echo.
pause
endlocal
exit /b 1
