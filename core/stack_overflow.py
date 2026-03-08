"""
Stack Overflow search — حلول للمشاكل البرمجية (Python).
يُستخدم في مسار الكود عندما يكون السؤال عن خطأ أو استفسار برمجي.
"""
import re
import requests
from typing import List, Tuple

STACK_NO_RESULTS_MSG = "لم أجد حلاً مشابهاً، سأقوم بتحليل الكود منطقياً."


def stack_overflow_search(error_message: str, max_items: int = 3) -> Tuple[str, List[dict]]:
    """
    يبحث عن حلول للمشاكل البرمجية المشابهة على Stack Overflow (Python).
    Returns (raw_text for prompt, rows for table: list of {title, href, body}).
    """
    if not error_message or not error_message.strip():
        return "", []

    url = "https://api.stackexchange.com/2.3/search/advanced"
    params = {
        "order": "desc",
        "sort": "relevance",
        "q": error_message.strip()[:500],
        "tagged": "python",
        "site": "stackoverflow",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        results = response.json()
    except Exception:
        return "", []

    items = results.get("items") or []
    if not items:
        return "", []

    rows = []
    lines = []
    for item in items[:max_items]:
        link = item.get("link") or ""
        title = (item.get("title") or "").strip()
        excerpt = (item.get("body") or item.get("excerpt") or "").strip()
        if excerpt:
            excerpt = re.sub(r"<[^>]+>", "", excerpt)[:300]
        rows.append({"title": title, "href": link, "body": excerpt or "See link for solution."})
        lines.append(f"Source: {link}\nTitle: {title}\nSnippet: {excerpt or '—'}")

    raw_text = "\n\n".join(lines) if lines else ""
    return raw_text, rows


def stack_overflow_links_only(error_message: str, max_items: int = 3) -> List[str]:
    """Returns only the top N links (legacy-style)."""
    _, rows = stack_overflow_search(error_message, max_items=max_items)
    return [r.get("href") or "" for r in rows if r.get("href")]
