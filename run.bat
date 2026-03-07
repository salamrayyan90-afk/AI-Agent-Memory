@echo off
cd /d "%~dp0"
set "VENV_DIR=.venv"
if not exist .venv if exist venv set "VENV_DIR=venv"
if not exist %VENV_DIR% (
  python -m venv %VENV_DIR%
  call %VENV_DIR%\Scripts\activate
  pip install -r requirements.txt
  pip install groq psutil python-dotenv streamlit requests
  where playwright >nul 2>&1 && playwright install chromium
) else (
  call %VENV_DIR%\Scripts\activate
)
pip install groq psutil python-dotenv streamlit requests
streamlit run app.py
