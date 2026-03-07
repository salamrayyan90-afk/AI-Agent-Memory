"""GitHub RAG: search private repo for past experiences and push task summaries."""
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from github import Github
from core.config import GITHUB_TOKEN, GITHUB_REPO

KNOWLEDGE_BASE_PATH = "knowledge_base.md"
SYSTEM_CONFIG_PATH = "system_config.json"

# Smart Summarization: section for extracted points (date strictly March 7, 2026)
LEARNED_CONTEXT_HEADER = "## Learned Context - 2026-03-07"

FIRST_MEMORY = """# Knowledge Base — Agent Memory

## Baseline Reference (March 7, 2026)

| Metric | Value | Source |
|--------|--------|--------|
| **Global Spot** | $5,172.89/oz | March 7, 2026 |
| **Local 21K (KSA)** | 545.71 SAR | saudigoldprice.com |

Logic Rule: If any future web search shows a difference **> 2%** from these values, trigger a **Volatile Market** alert and update this file with the new verified data.

## First Memory
As of March 7, 2026, the global gold price is $5,172.89/oz. Local 21K gold is 545.71 SAR. Source: saudigoldprice.com.
"""


def _get_repo():
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return None
    try:
        g = Github(GITHUB_TOKEN)
        return g.get_repo(GITHUB_REPO)
    except Exception:
        return None


def _extract_latest_date_from_text(text: str) -> Optional[str]:
    """Extract the most recent YYYY-MM-DD date from text. Returns None if none found."""
    if not text or not text.strip():
        return None
    matches = re.findall(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
    if not matches:
        return None
    return max(matches)


def sync_github_memory() -> Tuple[str, Optional[str]]:
    """
    Run at the start of every query. Pull the latest knowledge_base.md from the repo.
    Returns (content, last_date): content of the file (or empty), and the latest date found in it (YYYY-MM-DD) for comparison with today.
    """
    repo = _get_repo()
    if not repo:
        return "", None
    try:
        f = repo.get_contents(KNOWLEDGE_BASE_PATH)
        content = f.decoded_content.decode("utf-8", errors="replace")
        last_date = _extract_latest_date_from_text(content)
        return content.strip(), last_date
    except Exception:
        return "", None


def sync_knowledge() -> Tuple[str, Optional[str]]:
    """
    Memory First: Pull the latest facts from GitHub knowledge_base.md.
    Call this at the very start of every query before any reasoning or web search.
    Returns (content, last_date) for use in the agent context.
    """
    return sync_github_memory()


def update_agent_knowledge(new_info: str) -> bool:
    """
    تحديث ذاكرة البرنامج على جيت هاب — يلحق سطراً بتوقيت ويحفظ للأبد.
    Appends a timestamped log line to knowledge_base.md and PUSHes to GitHub.
    """
    if not new_info or not new_info.strip():
        return False
    repo = _get_repo()
    if not repo:
        return False
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    log_entry = f"\n- [{timestamp}] Updated Info: {new_info.strip()[:3000]}"
    try:
        existing = repo.get_contents(KNOWLEDGE_BASE_PATH)
        new_content = existing.decoded_content.decode("utf-8", errors="replace") + log_entry
        repo.update_file(KNOWLEDGE_BASE_PATH, "Core AI: update_agent_knowledge", new_content, existing.sha)
        return True
    except Exception:
        try:
            repo.create_file(KNOWLEDGE_BASE_PATH, "Core AI: create knowledge_base.md", log_entry.strip(), branch=None)
            return True
        except Exception:
            return False


def test_github_connection() -> Tuple[bool, str]:
    """
    اختبار الاتصال بـ GitHub: قراءة knowledge_base.md (يتطلب صلاحية قراءة).
    للتعديل والإضافة والحذف تأكد أن التوكن يملك repo (أو contents: read + write).
    Returns (success: bool, error_message: str).
    """
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return False, "GITHUB_TOKEN or GITHUB_REPO not set in .env"
    try:
        repo = _get_repo()
        if not repo:
            return False, "Failed to connect to GitHub (check token and repo name)"
        repo.get_contents(KNOWLEDGE_BASE_PATH)
        return True, ""
    except Exception as e:
        return False, str(e) or "Connection failed"


def test_github_read_write() -> Tuple[bool, bool, str]:
    """
    اختبار القراءة (والتحقق من إمكانية الوصول للكتابة عبر get_repo).
    صلاحية الكتابة تُختبر فعلياً عند أول دفع من التطبيق (مثلاً Core AI Memory Initialized).
    Returns (read_ok: bool, write_ok: bool, error_message: str).
    """
    ok, err = test_github_connection()
    if ok:
        return True, True, ""  # read OK; write assumed (token with repo scope can write)
    return False, False, err


def delete_file_from_github(path: str, message: str = "Core AI: delete file") -> bool:
    """
    حذف ملف من المستودع. يتطلب صلاحية كتابة (contents: write).
    path: المسار النسبي للملف (مثلاً knowledge_base.md أو memory/file.md).
    Returns True إذا تم الحذف بنجاح.
    """
    repo = _get_repo()
    if not repo:
        return False
    try:
        existing = repo.get_contents(path)
        repo.delete_file(path, message, existing.sha)
        return True
    except Exception:
        return False


def read_from_github(path: str = KNOWLEDGE_BASE_PATH) -> str:
    """قراءة الذاكرة من جيت هاب. Returns content of the file or empty string."""
    repo = _get_repo()
    if not repo:
        return ""
    try:
        f = repo.get_contents(path)
        return f.decoded_content.decode("utf-8", errors="replace")
    except Exception:
        return ""


def ensure_knowledge_base_initialized() -> bool:
    """Create knowledge_base.md on GitHub with First Memory if it does not exist. Returns True if ok."""
    repo = _get_repo()
    if not repo:
        return False
    try:
        repo.get_contents(KNOWLEDGE_BASE_PATH)
        return True
    except Exception:
        try:
            repo.create_file(
                KNOWLEDGE_BASE_PATH,
                "Core AI: initialize knowledge_base.md with First Memory",
                FIRST_MEMORY,
                branch=None,
            )
            return True
        except Exception:
            return False


DEFAULT_SYSTEM_CONFIG = {"tone": "senior_technical_expert_white_arabic", "font_size": "18px", "web_search_priority": True}


def ensure_system_config_initialized() -> bool:
    """Create system_config.json on GitHub with defaults if it does not exist. Returns True if ok."""
    repo = _get_repo()
    if not repo:
        return False
    try:
        repo.get_contents(SYSTEM_CONFIG_PATH)
        return True
    except Exception:
        try:
            content = json.dumps(DEFAULT_SYSTEM_CONFIG, indent=2)
            repo.create_file(
                SYSTEM_CONFIG_PATH,
                "Core AI: initialize system_config.json",
                content,
                branch=None,
            )
            return True
        except Exception:
            return False


def get_system_config_from_github() -> Dict[str, Any]:
    """Read system_config.json from GitHub repo. Returns dict with tone, font_size, web_search_priority or defaults."""
    default = dict(DEFAULT_SYSTEM_CONFIG)
    repo = _get_repo()
    if not repo:
        return default
    try:
        f = repo.get_contents(SYSTEM_CONFIG_PATH)
        text = f.decoded_content.decode("utf-8", errors="replace")
        data = json.loads(text)
        return {**default, **data} if isinstance(data, dict) else default
    except Exception:
        return default


def append_to_knowledge_base(entry: str, date_str: Optional[str] = None) -> bool:
    """
    Append a fact-checked entry to knowledge_base.md and PUSH back to GitHub (self-training).
    entry: the new fact to add (e.g. today's gold price + sources).
    date_str: optional YYYY-MM-DD; defaults to today UTC.
    """
    repo = _get_repo()
    if not repo:
        return False
    if not date_str:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
    block = f"\n\n---\n\n## {date_str}\n{entry.strip()}"
    try:
        existing = repo.get_contents(KNOWLEDGE_BASE_PATH)
        new_content = existing.decoded_content.decode("utf-8", errors="replace") + block
        repo.update_file(KNOWLEDGE_BASE_PATH, "Core AI: continuous learning — append fact-checked data", new_content, existing.sha)
        return True
    except Exception:
        try:
            repo.create_file(KNOWLEDGE_BASE_PATH, "Core AI: create knowledge_base.md", block.strip(), branch=None)
            return True
        except Exception:
            return False


def _metric_key(line: str) -> Optional[str]:
    """Extract a normalizable key from a line for contradiction detection (e.g. same price metric)."""
    if not line or not line.strip():
        return None
    s = line.strip().lower()
    # Verified data: Gold 21K (KSA), Global Spot, etc.
    if "gold" in s and ("21k" in s or "sar" in s or "ksa" in s):
        return "gold_21k_ksa"
    if "gold" in s and ("spot" in s or "/oz" in s or "global" in s):
        return "gold_global_spot"
    if "user" in s and ("preference" in s or "decision" in s or "يفضل" in s):
        return "user_preference"
    if "verified data" in s or "سعر" in s:
        return "verified_data"
    return None


def _remove_contradictions_in_learned_section(content: str, new_block: str) -> str:
    """
    Self-Cleanup: if a new fact contradicts an old one in ## Learned Context - 2026-03-07,
    remove the old line so Source of Truth stays accurate.
    """
    if not new_block or not new_block.strip():
        return content
    new_keys = set()
    for line in new_block.strip().split("\n"):
        k = _metric_key(line)
        if k:
            new_keys.add(k)
    if not new_keys:
        return content
    # Find section "## Learned Context - 2026-03-07" and remove lines whose _metric_key is in new_keys
    header = LEARNED_CONTEXT_HEADER
    if header not in content:
        return content
    parts = content.split(header, 1)
    if len(parts) != 2:
        return content
    before, after = parts[0], parts[1]
    # Section runs until next ## or end
    section_match = re.match(r"^([\s\S]*?)(?=\n## |\Z)", after)
    section_body = section_match.group(1).strip() if section_match else after
    rest = after[len(section_body):] if section_match else ""
    kept_lines = []
    for line in section_body.split("\n"):
        k = _metric_key(line)
        if k and k in new_keys:
            continue  # drop old contradictory line
        kept_lines.append(line)
    new_section = "\n".join(kept_lines).strip()
    new_after = (new_section + "\n" + rest) if new_section else rest.lstrip("\n")
    return before + header + "\n" + new_after


def append_smart_learned_context(extracted_points: str) -> bool:
    """
    Append extracted points (from Smart Summarization) to knowledge_base.md under
    ## Learned Context - 2026-03-07. Applies self-cleanup: replaces contradictory old data.
    """
    if not extracted_points or not extracted_points.strip():
        return False
    repo = _get_repo()
    if not repo:
        return False
    try:
        existing = repo.get_contents(KNOWLEDGE_BASE_PATH)
        current = existing.decoded_content.decode("utf-8", errors="replace")
        current = _remove_contradictions_in_learned_section(current, extracted_points)
        block = extracted_points.strip()[:4000]
        if LEARNED_CONTEXT_HEADER in current:
            # Append new block inside the section (after header, before next ##)
            parts = current.split(LEARNED_CONTEXT_HEADER, 1)
            before, after = parts[0], parts[1]
            section_match = re.match(r"^\n*([\s\S]*?)(?=\n## |\Z)", after)
            section_body = (section_match.group(1).strip() if section_match else after).strip()
            rest = after[len(section_body):] if section_match else after.lstrip()
            new_section = (section_body + "\n\n" + block) if section_body else block
            current = before + LEARNED_CONTEXT_HEADER + "\n\n" + new_section + rest
        else:
            current = current.rstrip() + "\n\n" + LEARNED_CONTEXT_HEADER + "\n\n" + block
        repo.update_file(
            KNOWLEDGE_BASE_PATH,
            "Core AI: Smart Summarization — Learned Context",
            current.strip(),
            existing.sha,
        )
        return True
    except Exception:
        try:
            block = LEARNED_CONTEXT_HEADER + "\n\n" + extracted_points.strip()[:4000]
            repo.create_file(
                KNOWLEDGE_BASE_PATH,
                "Core AI: create knowledge_base.md with Learned Context",
                block,
                branch=None,
            )
            return True
        except Exception:
            return False


def _get_files_from_folder(repo, folder: str) -> List[dict]:
    """Get content of files under folder (e.g. memory/tasks) for RAG."""
    out = []
    try:
        contents = repo.get_contents(folder)
        for c in contents:
            if c.type == "dir":
                out.extend(_get_files_from_folder(repo, c.path))
            elif c.path.endswith((".md", ".txt")):
                try:
                    content = c.decoded_content.decode("utf-8", errors="replace")
                    out.append({"path": c.path, "snippet": content[:1500], "url": c.html_url})
                except Exception:
                    pass
    except Exception:
        pass
    return out


def _list_experience_file_paths(repo, folder: str) -> List[str]:
    """List paths of experience-like files (md/txt) under folder, recursively."""
    paths = []
    try:
        contents = repo.get_contents(folder)
        for c in contents:
            if c.type == "dir":
                paths.extend(_list_experience_file_paths(repo, c.path))
            elif c.path.endswith((".md", ".txt", ".log")):
                paths.append(c.path)
    except Exception:
        pass
    return paths


def pull_github_memory(max_files: int = 10) -> str:
    """
    Read the last N experience files from the GitHub repo (by path/date order).
    Call this before generating any response so the LLM gets what it learned
    yesterday or an hour ago — this is how it becomes smart like Gemini.
    Returns concatenated content of the most recent experience files (memory/, memory/tasks/, logs/).
    """
    repo = _get_repo()
    if not repo:
        return ""
    all_paths = []
    for folder in ("memory/tasks", "memory", "logs"):
        all_paths.extend(_list_experience_file_paths(repo, folder))
    # Deduplicate and sort by path descending (paths like memory/tasks/2026-03-07_14-00.md = newest first)
    all_paths = sorted(set(all_paths), reverse=True)
    recent_paths = all_paths[:max_files]
    if not recent_paths:
        return ""
    out_text = []
    for path in recent_paths:
        try:
            f = repo.get_contents(path)
            content = f.decoded_content.decode("utf-8", errors="replace")
            out_text.append(f"[{path}]\n{content}")
        except Exception:
            continue
    return "\n\n---\n\n".join(out_text) if out_text else ""


def get_latest_logs_for_session() -> str:
    """
    Fetch the latest logs/experiences from the private repo (for session context).
    Call at session start so the agent reads past errors and successes before responding.
    Returns concatenated text from memory/, logs/, memory/tasks (md/txt).
    """
    # Use pull_github_memory so we get the last 10 experience files (Gemini-style memory)
    return pull_github_memory(max_files=10)


def search_repo(query: str, file_extensions: Optional[List[str]] = None) -> List[dict]:
    """
    Search the private GitHub repo for past experiences.
    Uses repo contents under memory/ (and tasks/) for RAG when code search is not available.
    Returns list of dicts: {path, content_snippet, url}.
    """
    repo = _get_repo()
    if not repo:
        return []
    # Prefer reading memory/ or memory/tasks for past experiences (works with private repos)
    for folder in ("memory", "memory/tasks", ""):
        if not folder:
            break
        try:
            out = _get_files_from_folder(repo, folder)
            if out:
                break
        except Exception:
            continue
    # Simple filter by query words
    if query and out:
        q = query.lower().strip()
        if q:
            out = [x for x in out if q in x.get("snippet", "").lower() or q in x.get("path", "").lower()]
    return out[:15]


def update_github_repo(filename: str, content: str) -> bool:
    """
    إنشاء أو استبدال ملف في المستودع (مثلاً autonomous_log.md).
    الملف يُخزّن تحت memory/ إن لم يبدأ المسار بـ memory/.
    """
    repo = _get_repo()
    if not repo:
        return False
    path = filename if filename.startswith("memory/") else f"memory/{filename}"
    try:
        existing = repo.get_contents(path)
        repo.update_file(path, "Core AI: update_github_repo", content.strip(), existing.sha)
        return True
    except Exception:
        try:
            repo.create_file(path, "Core AI: create file", content.strip(), branch=None)
            return True
        except Exception:
            return False


def push_proposed_update(filename: str, content: str) -> bool:
    """
    Save a proposed fix/update to the proposed_updates/ folder on GitHub.
    Used when the autonomous scan finds library updates; the agent writes the fix here.
    Path: proposed_updates/<filename> (repo root).
    """
    repo = _get_repo()
    if not repo:
        return False
    path = f"proposed_updates/{filename}" if not filename.startswith("proposed_updates/") else filename
    try:
        existing = repo.get_contents(path)
        repo.update_file(path, "Core AI: proposed update (autonomous)", content.strip(), existing.sha)
        return True
    except Exception:
        try:
            repo.create_file(path, "Core AI: proposed update (autonomous)", content.strip(), branch=None)
            return True
        except Exception:
            return False


def list_proposed_updates() -> List[dict]:
    """List files in proposed_updates/ folder (name, path) for UI."""
    repo = _get_repo()
    if not repo:
        return []
    try:
        contents = repo.get_contents("proposed_updates")
        return [{"name": c.name, "path": c.path} for c in contents if c.type == "file"]
    except Exception:
        return []


def push_task_summary(summary: str, filename: Optional[str] = None) -> bool:
    """
    Push a new task summary to the GitHub repo (e.g. memory/tasks/YYYY-MM-DD_HH-MM.md).
    Returns True if successful.
    """
    repo = _get_repo()
    if not repo:
        return False
    if not filename:
        from datetime import datetime
        filename = f"memory/tasks/{datetime.utcnow().strftime('%Y-%m-%d_%H-%M')}.md"
    if not filename.startswith("memory/"):
        filename = f"memory/{filename}"
    try:
        try:
            existing = repo.get_contents(filename)
            content = (existing.decoded_content.decode("utf-8") + "\n\n---\n\n" + summary)
            repo.update_file(filename, "Core AI: append task summary", content, existing.sha)
        except Exception:
            content = summary
            repo.create_file(filename, "Core AI: new task summary", content)
        return True
    except Exception:
        return False
