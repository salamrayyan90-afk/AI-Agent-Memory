# Launcher for CORE AI — runs Streamlit and opens browser
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

if getattr(sys, "frozen", False):
    ROOT = Path(sys.executable).resolve().parent
    if not (ROOT / "app.py").is_file():
        ROOT = Path(r"c:\Users\user\Desktop\Core AI")
else:
    ROOT = Path(__file__).resolve().parent

app_py = ROOT / "app.py"
if not app_py.is_file():
    sys.exit(1)

# Use venv Python if present (has groq, streamlit, etc.)
if sys.platform == "win32":
    venv_python = ROOT / "venv" / "Scripts" / "python.exe"
else:
    venv_python = ROOT / "venv" / "bin" / "python"
if venv_python.is_file():
    python_cmd = str(venv_python)
else:
    python_cmd = "py" if sys.platform == "win32" else "python3"

# Ensure Groq and python-dotenv are installed (venv-aware) before starting Streamlit
subprocess.run([python_cmd, "-m", "pip", "install", "groq", "python-dotenv"], cwd=str(ROOT), capture_output=True)

cmd = [python_cmd, "-m", "streamlit", "run", str(app_py), "--browser.gatherUsageStats", "false"]
try:
    proc = subprocess.Popen(cmd, cwd=str(ROOT))
except FileNotFoundError:
    proc = subprocess.Popen(["python", "-m", "streamlit", "run", str(app_py), "--browser.gatherUsageStats", "false"], cwd=str(ROOT))

time.sleep(4)
webbrowser.open("http://localhost:8501")
proc.wait()
