"""
Core AI — GitHub Sync Engine.
PULL context from knowledge_base.md at startup; PUSH new learned facts after each session.
"""
from typing import List, Optional, Tuple

try:
    from memory.github_rag import (
        ensure_knowledge_base_initialized,
        ensure_system_config_initialized,
        sync_knowledge,
        update_agent_knowledge,
        append_to_knowledge_base,
        read_from_github,
    )
except ImportError:
    ensure_knowledge_base_initialized = lambda: False
    ensure_system_config_initialized = lambda: False
    sync_knowledge = lambda: ("", None)
    update_agent_knowledge = lambda x: False
    append_to_knowledge_base = lambda e, d=None: False
    read_from_github = lambda p="knowledge_base.md": ""


def pull_at_startup() -> Tuple[str, Optional[str]]:
    """
    Call once at app startup. Ensures knowledge_base.md and system_config exist,
    then PULLs the latest knowledge_base.md from GitHub.
    Returns (content, last_date) for the agent context.
    """
    ensure_knowledge_base_initialized()
    ensure_system_config_initialized()
    return sync_knowledge()


def push_after_session(facts: List[str]) -> int:
    """
    PUSH new learned facts to knowledge_base.md after each session.
    Each fact is appended with a timestamp. Returns count of successfully pushed items.
    """
    if not facts:
        return 0
    count = 0
    for entry in facts:
        if entry and str(entry).strip():
            try:
                if update_agent_knowledge(entry.strip()[:3000]):
                    count += 1
            except Exception:
                pass
    return count


def get_knowledge_base_content(path: str = "knowledge_base.md") -> str:
    """Read current content of a repo file (default: knowledge_base.md)."""
    return read_from_github(path)
