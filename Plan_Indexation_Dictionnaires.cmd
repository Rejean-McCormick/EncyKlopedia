@echo off
setlocal
cd /d "%~dp0"
if not defined ENCYK_DATA_ROOT set "ENCYK_DATA_ROOT=D:\EncyKlopedia"
node tools\dictionary-harvester\cli.mjs index-plan
pause
