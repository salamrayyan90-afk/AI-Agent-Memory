@echo off
title Push to AI-Agent-Memory
cd /d "%~dp0"

where git >nul 2>&1 || (
  echo [ERROR] Git not found. Install from https://git-scm.com
  pause
  exit /b 1
)

if not exist .git (
  git init
  git branch -M main
)

git add .
git commit -m "Final deployment build - CORE AI (app.py, index.html, requirements.txt, CoreAI.ico)"
if errorlevel 1 (
  echo No changes to commit or commit failed.
  pause
  exit /b 0
)

set "USER=%~1"
if "%USER%"=="" (
  echo Usage: PUSH_TO_AI_AGENT_MEMORY.bat YOUR_GITHUB_USERNAME
  echo Example: PUSH_TO_AI_AGENT_MEMORY.bat johndoe
  echo.
  echo Or run manually:
  echo   git remote add origin https://github.com/YOUR_USERNAME/AI-Agent-Memory.git
  echo   git push -u origin main
  pause
  exit /b 0
)

git remote remove origin 2>nul
git remote add origin https://github.com/%USER%/AI-Agent-Memory.git
git push -u origin main
echo.
echo Repo: https://github.com/%USER%/AI-Agent-Memory
pause
