@echo off
setlocal EnableExtensions
where py >nul 2>nul
if errorlevel 1 (set "PY=python") else (set "PY=py -3")
%PY% "%~dp0tools\unesco_pilot\verifier_overlay_extraction_v20.py"
pause
