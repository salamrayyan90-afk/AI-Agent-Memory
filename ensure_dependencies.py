"""
CORE AI — تثبيت والتحقق من كل التبعيات والاتصالات.
شغّل هذا الملف مرة واحدة (أغلق أي نافذة CORE AI قبل التشغيل):
  py ensure_dependencies.py
  أو من داخل المجلد: venv\Scripts\python ensure_dependencies.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
venv_python = ROOT / "venv" / "Scripts" / "python.exe"
if not venv_python.is_file():
    print("لم يتم العثور على venv. أنشئه أولاً: py -m venv venv")
    sys.exit(1)

def run(cmd, desc):
    print(f"  {desc}...", end=" ", flush=True)
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=300)
    if r.returncode == 0:
        print("OK")
        return True
    print("FAILED")
    if r.stderr:
        print("    ", r.stderr[:200])
    return False

print("1. تثبيت الحزم من requirements.txt")
run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip", "-q"], "pip upgrade")
run([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt", "-q"], "requirements.txt")

print("2. التحقق من الاستيراد")
run([str(venv_python), "-c",
     "import streamlit; import groq; import dotenv; from duckduckgo_search import DDGS; import google.generativeai; print('ok')"],
    "streamlit, groq, dotenv, duckduckgo, gemini")

print("3. التحقق من .env")
env_file = ROOT / ".env"
if not env_file.is_file():
    print("   تحذير: لا يوجد ملف .env. انسخ .env.example إلى .env واملأ المفاتيح.")
else:
    content = env_file.read_text(encoding="utf-8", errors="replace")
    for key in ("GROQ_API_KEY", "GITHUB_TOKEN", "GITHUB_REPO", "GEMINI_API_KEY"):
        if key in content and "your_" not in content and "=your" not in content.lower():
            print(f"   {key}: معيّن")
        else:
            print(f"   {key}: غير معيّن أو placeholder — أضف المفتاح في .env")

print("4. تشغيل اختبار سريع لـ Streamlit (تحميل app فقط)")
r = subprocess.run([str(venv_python), "-c",
    "import sys; sys.path.insert(0, r'" + str(ROOT).replace("\\", "\\\\") + "'); import app; print('app load OK')"],
    cwd=str(ROOT), capture_output=True, text=True, timeout=30)
if r.returncode == 0:
    print("   تحميل app: OK")
else:
    print("   تحميل app: فشل —", (r.stderr or r.stdout or "")[:300])

print("\nانتهى. شغّل البرنامج من اختصار CORE AI أو: venv\\Scripts\\python -m streamlit run app.py")
