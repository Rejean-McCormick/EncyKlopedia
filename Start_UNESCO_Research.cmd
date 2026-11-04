@echo off
setlocal
cd /d "%~dp0"
set "ENCYKLOPEDIA_RESEARCH_VIEW=%~dp0..\UNESCO_Workbench\output\private\educational-policy-en\research-view.json"
if not exist "%ENCYKLOPEDIA_RESEARCH_VIEW%" (
  echo [ERROR] Research view missing. First run UNESCO_Workbench\LANCER_VERSION_TOTALE.cmd and BUILD.
  pause
  exit /b 2
)
where node >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js 22+ required.
  pause
  exit /b 2
)
set "ENCYKLOPEDIA_MODE=research"
set "ENCYKLOPEDIA_HOST=127.0.0.1"
set "ENCYKLOPEDIA_PORT=8787"
echo EncyKlopedia PRIVATE research: http://127.0.0.1:8787
echo No public release, no canonical Kristal write.
node src\server.mjs
if errorlevel 1 pause
endlocal
