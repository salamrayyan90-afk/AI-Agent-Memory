"""
Core AI — Direct File System Access within the project directory.
Read/Write with .bak backup and .core_backup snapshot; integrity check and auto-rollback on failure.
Standard: 18px font and Zero Headers (#) in UI-related code.
"""
import ast
import json
import shutil
from pathlib import Path
from typing import Optional, Tuple

# Project root: Core AI folder (parent of core/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Hidden folder for fail-safe snapshots (filename.py.tmp)
BACKUP_DIR = PROJECT_ROOT / ".core_backup"
ALLOWED_EXTENSIONS = (".py", ".css", ".md", ".json", ".html", ".js", ".txt", ".yml", ".yaml")
FORBIDDEN_DIRS = {"venv", ".git", "__pycache__", "node_modules", ".cursor"}

# UI standard reminder for change log (18px, Zero Headers)
UI_STANDARD_NOTE = " (18px / Zero Headers enforced in UI code)"
ROLLBACK_MESSAGE = "تم رصد خطأ برمي وتفعيل التراجع التلقائي لحماية النظام"


def _resolve_path(relative_path: str) -> Optional[Path]:
    """Resolve relative path under PROJECT_ROOT; reject paths outside or in forbidden dirs."""
    if not relative_path or not relative_path.strip():
        return None
    p = (PROJECT_ROOT / relative_path.strip().lstrip("/")).resolve()
    try:
        p.relative_to(PROJECT_ROOT)
    except ValueError:
        return None
    parts = p.parts
    for i, part in enumerate(parts):
        if part in FORBIDDEN_DIRS:
            return None
        if part.startswith(".") and part != ".env" and part != ".gitignore":
            continue
    if p.suffix.lower() not in ALLOWED_EXTENSIONS:
        return None
    return p


def _snapshot_path(relative_path: str) -> Path:
    """Path for temporary snapshot in .core_backup (e.g. app.py -> .core_backup/app.py.tmp)."""
    safe = relative_path.strip().lstrip("/").replace("\\", "/")
    return BACKUP_DIR / (safe + ".tmp")


def _create_snapshot(relative_path: str, source_path: Path) -> bool:
    """Create snapshot in .core_backup before any direct modification. Returns True on success."""
    if not source_path.exists():
        return True
    snap = _snapshot_path(relative_path)
    try:
        snap.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, snap)
        return True
    except Exception:
        return False


def _delete_snapshot(relative_path: str) -> None:
    """Delete the temporary snapshot after success or after rollback."""
    snap = _snapshot_path(relative_path)
    try:
        if snap.is_file():
            snap.unlink()
    except Exception:
        pass


def _integrity_check(relative_path: str, content: str) -> Tuple[bool, Optional[str]]:
    """
    Silent syntax/structure check after save. Returns (ok, error_message).
    For .py uses ast.parse; for .json uses json.loads; else passes.
    """
    ext = Path(relative_path).suffix.lower()
    if ext == ".py":
        try:
            ast.parse(content)
            return True, None
        except SyntaxError as e:
            return False, str(e)
    if ext == ".json":
        try:
            json.loads(content)
            return True, None
        except json.JSONDecodeError as e:
            return False, str(e)
    return True, None


def read_file(relative_path: str) -> Optional[str]:
    """Read file content from project directory. Returns None if path invalid or read fails."""
    path = _resolve_path(relative_path)
    if not path or not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def write_file_with_backup(relative_path: str, content: str, create_backup: bool = True) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Write content to file under project directory. If create_backup is True, creates a .bak of the original first.
    Returns (success, backup_path, error_message).
    """
    path = _resolve_path(relative_path)
    if not path:
        return False, None, "Path not allowed or invalid extension"
    backup_path = None
    if create_backup and path.exists():
        backup_path = path.with_suffix(path.suffix + ".bak")
        try:
            shutil.copy2(path, backup_path)
        except Exception as e:
            return False, None, f"Backup failed: {e}"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", errors="replace")
        return True, str(backup_path) if backup_path else None, None
    except Exception as e:
        return False, str(backup_path) if backup_path else None, str(e)


def push_change_log_to_github(file_path: str, change_summary: str) -> bool:
    """Append a Change Log entry to knowledge_base.md on GitHub after a local file modification."""
    try:
        from memory.github_rag import update_agent_knowledge
    except ImportError:
        return False
    entry = f"[Change Log] File: {file_path} | {change_summary.strip()[:2000]}{UI_STANDARD_NOTE}"
    return update_agent_knowledge(entry)


def push_success_log_to_github(file_path: str, change_summary: str) -> bool:
    """Push a Success Log to knowledge_base.md after a verified edit (integrity check passed)."""
    try:
        from memory.github_rag import update_agent_knowledge
    except ImportError:
        return False
    entry = f"[Success Log] File: {file_path} | {change_summary.strip()[:2000]}{UI_STANDARD_NOTE}"
    return update_agent_knowledge(entry)


def apply_direct_edit(
    relative_path: str,
    new_content: str,
    change_summary: str,
    create_backup: bool = True,
) -> Tuple[bool, str]:
    """
    Fail-Safe Auto-Rollback: snapshot in .core_backup -> write -> integrity check ->
    on failure: restore from snapshot, delete .tmp, notify rollback message;
    on success: push Success Log to GitHub, delete snapshot.
    Returns (success, message). Message is 18px-safe for UI; no Markdown headers.
    """
    path = _resolve_path(relative_path)
    if not path:
        return False, "Path not allowed or invalid extension"
    # 1. Snapshot: before any modification, create temporary snapshot in .core_backup
    if not _create_snapshot(relative_path, path):
        return False, "فشل إنشاء اللقطة الاحتياطية"
    ok, backup_path, err = write_file_with_backup(relative_path, new_content, create_backup=create_backup)
    if not ok:
        _delete_snapshot(relative_path)
        return False, err or "فشل التعديل"
    # 2. Integrity check (silent syntax / dry-run)
    check_ok, check_err = _integrity_check(relative_path, new_content)
    if not check_ok:
        # 3. Automatic rollback: overwrite corrupted file with snapshot, then delete .tmp
        snap = _snapshot_path(relative_path)
        if snap.is_file():
            try:
                path.write_text(snap.read_text(encoding="utf-8", errors="replace"), encoding="utf-8", errors="replace")
            except Exception:
                pass
        _delete_snapshot(relative_path)
        return False, ROLLBACK_MESSAGE
    # 4. Success: push Success Log to GitHub and delete local temporary snapshot
    push_success_log_to_github(relative_path, change_summary)
    _delete_snapshot(relative_path)
    filename = Path(relative_path).name
    return True, f"تم تعديل الملف {filename} بنجاح وفقاً للمعايير الاحترافية"


def list_editable_files(subdir: str = "") -> list:
    """List .py and .css files under project (optionally under subdir) for the agent to locate."""
    root = PROJECT_ROOT / subdir.strip().lstrip("/") if subdir else PROJECT_ROOT
    if not root.is_dir():
        return []
    out = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".py", ".css", ".md", ".html", ".js", ".json"):
            continue
        try:
            rel = p.relative_to(PROJECT_ROOT)
            if any(part in FORBIDDEN_DIRS for part in rel.parts):
                continue
            out.append(str(rel).replace("\\", "/"))
        except ValueError:
            continue
    return sorted(out)[:200]
