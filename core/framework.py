"""
Core AI Framework — Initialize the four pillars:
1. Groq integration (reasoning, Llama-3)
2. GitHub Sync Engine (pull at startup, push after session)
3. Autonomous Search (DuckDuckGo, trigger when real-time data needed)
4. UI Branding (Streamlit dark theme, professional layout)
"""
from typing import Any, Dict, Optional, Tuple

from core.config import GROQ_API_KEY, GITHUB_TOKEN, GITHUB_REPO


def init_core_ai() -> Dict[str, Any]:
    """
    Initialize the Core AI framework. Call once at app startup.
    Returns a dict with: groq_ok, github_ok, search_ok, gemini_ok, neural_connection_established, kb_content, kb_date, reasoning_model.
    """
    result = {
        "groq_ok": False,
        "github_ok": False,
        "search_ok": False,
        "gemini_ok": False,
        "neural_connection_established": False,
        "kb_content": "",
        "kb_date": None,
        "reasoning_model": "",
    }

    # 1. Groq integration
    try:
        from core.groq_client import get_groq_client, get_reasoning_model
        client = get_groq_client()
        result["groq_ok"] = client is not None and bool(GROQ_API_KEY)
        result["reasoning_model"] = get_reasoning_model()
    except Exception:
        pass

    # 2. GitHub Sync Engine — PULL at startup
    try:
        from memory.github_sync_engine import pull_at_startup
        kb_content, kb_date = pull_at_startup()
        result["kb_content"] = kb_content or ""
        result["kb_date"] = kb_date
        result["github_ok"] = bool(GITHUB_TOKEN and GITHUB_REPO)
    except Exception:
        result["github_ok"] = bool(GITHUB_TOKEN and GITHUB_REPO)

    # 3. Autonomous Search (DuckDuckGo) — available when agent needs real-time data
    try:
        from duckduckgo_search import DDGS
        result["search_ok"] = DDGS is not None
    except Exception:
        pass

    # 4. Gemini Neural Link — test call so UI can show "Neural Connection Established"
    try:
        from core.gemini_client import test_neural_connection
        ok, err = test_neural_connection()
        result["gemini_ok"] = ok
        result["neural_connection_established"] = ok
    except Exception:
        pass

    return result
