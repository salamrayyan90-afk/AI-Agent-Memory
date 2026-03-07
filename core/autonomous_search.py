"""
Core AI — Autonomous Search (DuckDuckGo).
The agent triggers this automatically when it detects a need for real-time data.
"""
from typing import List, Tuple

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None


def autonomous_web_search(query: str, max_results: int = 6) -> Tuple[str, List[dict]]:
    """
    Run a web search. Used by the agent when real-time data is needed
    (prices, news, facts, code docs). Returns (raw_text, rows) for prompt injection.
    """
    if not query or not str(query).strip():
        return "", []
    if DDGS is None:
        return "", []
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(str(query).strip(), max_results=max_results))
        if not results:
            return "", []
        rows = []
        lines = []
        for r in results:
            href = r.get("href") or r.get("link") or ""
            body = (r.get("body") or r.get("snippet") or "").strip()
            title = (r.get("title") or body[:80] or "—").strip()
            rows.append({"title": title, "href": href, "body": body})
            lines.append(f"Source: {href}\nSnippet: {body}")
        return "\n\n".join(lines), rows
    except Exception:
        return "", []


def needs_realtime_data(query: str) -> bool:
    """
    Heuristic: does the query suggest a need for real-time data?
    If True, the agent should trigger autonomous_web_search.
    """
    if not query or not query.strip():
        return False
    q = query.strip().lower()
    triggers = [
        "سعر", "price", "أخبار", "news", "اليوم", "today", "أحدث", "latest",
        "current", "الآن", "now", "بحث", "search", "كم", "بكم", "؟", "?"
    ]
    return any(t in q for t in triggers)
