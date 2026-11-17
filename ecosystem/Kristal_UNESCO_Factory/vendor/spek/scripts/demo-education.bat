@echo off
setlocal
cd /d "%~dp0.."
python -m spek import-educational --adapter ekole --input examples/education/ekole-curated-preview.json --out-dir education-ekole
if errorlevel 1 exit /b 1
python -m spek build --source education-ekole/article.json --realizations education-ekole/realizations.json --out dist-education --formats "html,pdf,tex"
if errorlevel 1 exit /b 1
python -m spek verify-site dist-education
if errorlevel 1 exit /b 1
echo Run: python -m http.server 8000 --directory dist-education
