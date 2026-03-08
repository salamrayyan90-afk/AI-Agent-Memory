"""
Check: .env loaded? GitHub connection OK?
Run from project folder: python check_github_connection.py
"""
import os
import sys
from pathlib import Path

# Force UTF-8 on Windows for emoji/arrows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
env_path = ROOT / ".env"

def main():
    print("=" * 50)
    print("CORE AI - GitHub connection check")
    print("=" * 50)

    if not env_path.is_file():
        print("[X] .env not found in project folder.")
        print("    Expected:", env_path)
        return

    print("[OK] .env found:", env_path)

    from dotenv import load_dotenv
    load_dotenv(env_path)

    token = os.getenv("GITHUB_TOKEN", "")
    repo = os.getenv("GITHUB_REPO", "")

    if not token or not token.strip():
        print("[X] GITHUB_TOKEN missing or empty in .env")
        return
    print("[OK] GITHUB_TOKEN is set")

    if not repo or not repo.strip():
        print("[X] GITHUB_REPO missing or empty in .env")
        return
    print("[OK] GITHUB_REPO:", repo)

    try:
        from memory.github_rag import test_github_connection, test_github_read_write
        ok, err = test_github_connection()
        if ok:
            print("[OK] GitHub connection success - knowledge_base.md readable (read)")
            read_ok, write_ok, werr = test_github_read_write()
            if read_ok and write_ok:
                print("[OK] Read + write access OK (add/update/delete allowed with repo scope)")
            else:
                print("[!] Write/delete:", werr or "check token has repo or contents:write scope")
            print("     In the app: GitHub Sync OK, memory linked to GitHub OK")
        else:
            print("[X] Connection failed:", err)
    except Exception as e:
        print("[X] Error:", e)

if __name__ == "__main__":
    main()
    print()
    print("Run from project folder with the same Python you use for Streamlit (e.g. activate venv first).")
