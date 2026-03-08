@echo off
title CORE AI - Push to GitHub
cd /d "%~dp0"

where git >nul 2>&1 || (
  echo ERROR: Git is not installed or not in PATH.
  echo Install from https://git-scm.com then run this script again.
  pause
  exit /b 1
)

if not exist .git (
  echo Initializing Git repository...
  git init
  git branch -M main
)

echo.
echo Staging all files...
git add .

echo.
echo Committing with message: Final deployment build
git commit -m "Final deployment build"

echo.
echo Current remote:
git remote -v
echo.
if not exist .git\refs\remotes\origin (
  echo No remote 'origin' set. To link your GitHub repo, run:
  echo   git remote add origin https://github.com/YOUR_USERNAME/Core-AI.git
  echo Replace YOUR_USERNAME with your GitHub username, then run this script again.
  pause
  exit /b 0
)

echo Pushing to origin main...
git push -u origin main
if errorlevel 1 (
  echo.
  echo If push failed: create repo at https://github.com/new named "Core-AI", then run:
  echo   git remote add origin https://github.com/YOUR_USERNAME/Core-AI.git
  echo   git push -u origin main
)
echo.
echo Done. Your repo link: https://github.com/YOUR_USERNAME/Core-AI
pause
