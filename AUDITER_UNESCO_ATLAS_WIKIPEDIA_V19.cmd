@echo off
setlocal
set "TOOL=%~dp0..\mediatheque-references\tools\wiki\atlas\atlas_wikipedia.py"
where py >nul 2>nul
if errorlevel 1 (set "PY=python") else (set "PY=py -3")
%PY% "%TOOL%" audit
if errorlevel 1 (echo AUDIT REFUSE) else (echo AUDIT REUSSI)
pause
