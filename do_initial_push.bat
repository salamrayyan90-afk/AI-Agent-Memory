@echo off
cd /d "%~dp0"
where git >nul 2>&1 || (echo Git not found. Install from https://git-scm.com && exit /b 1)
if not exist .git git init
git add .
git status
git commit -m "Initial Professional Build - CORE AI v1.0"
git branch -M main
echo.
echo If you have not added a remote yet:
echo   Create repo at https://github.com/new named Core-AI
echo   Then run: git remote add origin https://github.com/YOUR_USERNAME/Core-AI.git
echo   Then run: git push -u origin main
echo.
echo If remote already exists:
git remote -v
git push -u origin main 2>nul || echo Run the remote add command above, then: git push -u origin main
pause
