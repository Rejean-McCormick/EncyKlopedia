@echo off
setlocal EnableExtensions
set "TOOL=%~dp0..\mediatheque-references\tools\wiki\atlas\extraire_lots_v20.py"
where py >nul 2>nul
if errorlevel 1 (set "PY=python") else (set "PY=py -3")
%PY% "%TOOL%" audit %*
if errorlevel 1 (echo AUDIT V20 ECHEC) else (echo AUDIT V20 REUSSI)
pause
