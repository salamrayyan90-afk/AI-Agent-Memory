@echo off
cd /d "%~dp0"

echo === CORE AI - Push to AI-Agent-Memory for Streamlit ===
echo.

where git >nul 2>&1 || (
  echo ERROR: Git not installed. Install from https://git-scm.com then run this again.
  pause
  exit /b 1
)

if not exist .git (
  echo Initializing Git...
  git init
  git branch -M main
)

echo Ensuring app.py, requirements.txt, index.html are staged...
git add app.py requirements.txt index.html
git add .
echo.
git status
echo.
set /p USER="Enter your GitHub username: "
if "%USER%"=="" (
  echo No username entered. Run again and enter username.
  pause
  exit /b 1
)

git commit -m "Final deployment build - app.py, requirements.txt, index.html for Streamlit"
git remote remove origin 2>nul
git remote add origin https://github.com/%USER%/AI-Agent-Memory.git
echo.
echo Pushing to main...
git push -u origin main

echo.
echo === After push, verify on GitHub: ===
echo https://github.com/%USER%/AI-Agent-Memory
echo You must see: app.py, requirements.txt, index.html in the root.
echo.
pause
