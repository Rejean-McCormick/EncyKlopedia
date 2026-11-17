@echo off
setlocal
cd /d "%~dp0"
title Spek - Atelier de publication
if exist "%~dp0Spek_Template_Manager.pyw" goto run
 echo ERREUR : Spek_Template_Manager.pyw absent.
 pause
 exit /b 1
:run
where py >nul 2>nul
if not errorlevel 1 (
 py -3 "%~dp0Spek_Template_Manager.pyw"
) else (
 where python >nul 2>nul
 if errorlevel 1 (
  echo ERREUR : Python 3.10+ et Tkinter sont requis.
  pause
  exit /b 1
 )
 python "%~dp0Spek_Template_Manager.pyw"
)
if errorlevel 1 (
 echo.
 echo Echec. Execute DIAGNOSTIC_TEMPLATES.cmd pour afficher l'erreur.
 pause
)
