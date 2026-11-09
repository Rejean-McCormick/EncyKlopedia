@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "INDEX=%~dp0..\mediatheque-references\tools\wiki\atlas\index_xml_v21.py"
where py >nul 2>nul
if errorlevel 1 (set "PY=python") else (set "PY=py -3")
%PY% "%~dp0tools\unesco_pilot\verifier_overlay_entrepot_v21.py"
if errorlevel 1 goto :err
%PY% "%INDEX%" status
if errorlevel 1 goto :err
pause
exit /b 0
:err
echo Index absent, incompatible, ou overlay incomplet.
pause
exit /b 2
