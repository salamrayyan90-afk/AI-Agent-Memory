"""Computer control: local files and system resources (i7-7700HQ, 16GB RAM)."""
import os
import platform
from pathlib import Path
from typing import List, Optional

try:
    import psutil
except ImportError:
    psutil = None


def get_system_resources() -> dict:
    """Monitor CPU and RAM. Optimized context for i7-7700HQ and 16GB RAM."""
    if not psutil:
        return {"error": "psutil not installed", "cpu_percent": 0, "ram_percent": 0, "ram_gb": 0}
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        return {
            "cpu_percent": round(cpu_percent, 1),
            "ram_percent": round(mem.percent, 1),
            "ram_used_gb": round(mem.used / (1024 ** 3), 2),
            "ram_total_gb": round(mem.total / (1024 ** 3), 2),
            "platform": platform.system(),
        }
    except Exception as e:
        return {"error": str(e), "cpu_percent": 0, "ram_percent": 0, "ram_gb": 0}


def list_directory(path: str, max_entries: int = 50) -> dict:
    """List files and folders. Safe: no delete/write."""
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists() or not p.is_dir():
            return {"error": "المسار غير موجود أو ليس مجلداً", "entries": []}
        entries = []
        for i, entry in enumerate(p.iterdir()):
            if i >= max_entries:
                break
            try:
                stat = entry.stat()
                entries.append({
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "size": stat.st_size if entry.is_file() else None,
                })
            except (OSError, PermissionError):
                continue
        return {"path": str(p), "entries": entries}
    except Exception as e:
        return {"error": str(e), "entries": []}


def read_file_safe(path: str, max_bytes: int = 100_000) -> dict:
    """Read file contents (text) up to max_bytes. Safe read-only."""
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists() or not p.is_file():
            return {"error": "الملف غير موجود", "content": None}
        if p.stat().st_size > max_bytes:
            return {"error": f"الملف أكبر من {max_bytes} بايت", "content": None}
        content = p.read_text(encoding="utf-8", errors="replace")
        return {"path": str(p), "content": content}
    except Exception as e:
        return {"error": str(e), "content": None}


def requires_approval(action_type: str, detail: str) -> bool:
    """Return True if this action requires Approve/Run (financial or OS-level)."""
    from core.config import FINANCIAL_KEYWORDS, OS_LEVEL_KEYWORDS
    text = (action_type + " " + detail).lower()
    if any(k in text for k in FINANCIAL_KEYWORDS):
        return True
    if any(k in text for k in OS_LEVEL_KEYWORDS):
        return True
    return False
