@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo UNESCO V15 - workspace Kit reel / registre KQ-KP / GF
echo Un seul Kristal prive. AUCUN canon, KS, article ou GitHub.
echo ============================================================
if "%~1"=="" (
  python "%~dp0tools\unesco_pilot\workspace_readiness_v15.py"
) else (
  python "%~dp0tools\unesco_pilot\workspace_readiness_v15.py" --existing-workspace "%~1"
)
if errorlevel 1 (
  echo ECHEC : aucun canon ni publication modifies.
) else (
  echo SUCCES : workspace prive et diagnostics V15 sur D:.
)
pause
