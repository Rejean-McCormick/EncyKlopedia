@echo off
setlocal
pushd "%~dp0"
where node >nul 2>&1
if errorlevel 1 (
  echo [EncyKlopedia] Node.js 22+ is required.
  popd
  pause
  exit /b 2
)
set "ENCYKLOPEDIA_MODE=demo"
set "ENCYKLOPEDIA_HOST=127.0.0.1"
set "ENCYKLOPEDIA_PORT=8787"
echo [EncyKlopedia] Local synthetic demonstration only.
echo Open http://127.0.0.1:8787
node src\server.mjs
set "STATUS=%ERRORLEVEL%"
popd
if not "%STATUS%"=="0" pause
exit /b %STATUS%
