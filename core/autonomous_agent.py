"""
AutonomousAgent: يبحث ويحدث نفسه ذاتياً إذا وجد جديداً.
Auto-check and update knowledge_base from the web; push to GitHub when data is new.
Optimized for resource efficiency: memory cache with TTL to reduce GitHub API calls.
"""
import datetime
import re
import time
from typing import Optional

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

try:
    from memory.github_rag import sync_knowledge, update_agent_knowledge
except ImportError:
    sync_knowledge = lambda: ("", None)
    update_agent_knowledge = lambda x: False

# Cache TTL in seconds: avoid hitting GitHub on every is_data_new() in the same request (i7/16GB friendly).
_MEMORY_CACHE_TTL_SEC = 60


class AutonomousAgent:
    """
    Autonomous agent that checks the web for new data and pushes to knowledge_base.md when relevant.
    Uses a short-lived in-memory cache to reduce redundant GitHub fetches.
    """

    def __init__(self, github_repo=None):
        """
        Args:
            github_repo: Optional repo object; if None, sync/push use memory.github_rag (GITHUB_REPO from config).
        """
        self.repo = github_repo
        self.last_update = None
        self._memory = ""
        self._memory_date = None
        self._memory_cache_ts: Optional[float] = None

    def _refresh_memory(self) -> None:
        """Load current knowledge_base from GitHub into _memory. Uses TTL cache to limit API calls."""
        now = time.monotonic()
        if self._memory_cache_ts is not None and (now - self._memory_cache_ts) < _MEMORY_CACHE_TTL_SEC:
            return
        try:
            self._memory, self._memory_date = sync_knowledge()
            self._memory_cache_ts = now
        except Exception:
            self._memory, self._memory_date = "", None
            self._memory_cache_ts = now

    def is_data_new(self, info: str) -> bool:
        """
        منطق لمقارنة المعلومة الجديدة بما هو موجود في الذاكرة.
        Returns True if info appears new (e.g. contains today's date, or numbers not in memory).
        """
        if not info or not info.strip():
            return False
        self._refresh_memory()
        current_date = datetime.date.today().strftime("%Y-%m-%d")
        # إذا الذاكرة لا تحتوي تاريخ اليوم، المعلومة الجديدة تعتبر جديدة
        if not self._memory or (self._memory_date and self._memory_date < current_date):
            return True
        if current_date not in self._memory and current_date in info:
            return True
        # استخراج أرقام من الذاكرة والمعلومة الجديدة
        def extract_numbers(text):
            out = set()
            for m in re.finditer(r"[\d,]+(?:\.[\d]+)?", text or ""):
                try:
                    v = float(m.group(0).replace(",", "").replace(" ", ""))
                    if 10 < v < 1e7:
                        out.add(round(v, 2))
                except ValueError:
                    pass
            return out
        try:
            mem_nums = extract_numbers(self._memory)
            new_nums = extract_numbers(info)
            # إذا وُجدت أرقام في الجديد غير موجودة في الذاكرة (أو مختلفة كثيراً)، تعتبر جديدة
            if not mem_nums:
                return True
            for n in new_nums:
                if not any(abs(n - m) / max(m, 1) < 0.02 for m in mem_nums):
                    return True
        except Exception:
            return True
        return False

    def push_to_github(self, topic: str, new_info: str) -> bool:
        """يدفع المعلومة الجديدة إلى knowledge_base.md على GitHub."""
        if not new_info or not new_info.strip():
            return False
        entry = f"[Auto] {topic}: {new_info.strip()[:2500]}"
        try:
            ok = update_agent_knowledge(entry)
            if ok:
                self.last_update = datetime.datetime.now().isoformat()
            return ok
        except Exception:
            return False

    def auto_check_and_update(self, topic: str) -> Optional[str]:
        """
        يبحث ويحدث نفسه ذاتياً إذا وجد جديداً.
        Searches for latest data on the topic (e.g. price today); if data is new, pushes to GitHub and returns it.
        Uses a single DDGS context and minimal result set for efficiency (i7-7700HQ / 16GB friendly).
        """
        if not DDGS:
            return None
        current_date = datetime.date.today().strftime("%Y-%m-%d")
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(f"{topic} price today {current_date}", max_results=3))
                if not results:
                    results = list(ddgs.text(f"{topic} price", max_results=3))
            if not results:
                return None
            new_info = (results[0].get("body") or results[0].get("snippet") or "").strip()
            if not new_info:
                return None
            if self.is_data_new(new_info):
                self.push_to_github(topic, new_info)
            return new_info
        except Exception:
            return None


def get_autonomous_agent() -> AutonomousAgent:
    """Return a shared AutonomousAgent (no repo needed; uses config)."""
    return AutonomousAgent(github_repo=None)
