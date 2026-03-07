"""
GitHub repository search — Architect Mode: top-rated repos similar to Help Me Pro or any feature request.
"""
import requests
from typing import List, Dict, Any

# Help Me Pro–style and feature-request → GitHub search query
HELP_ME_PRO_QUERIES = [
    "AI coding assistant streamlit python",
    "code helper agent streamlit",
    "programming assistant python",
]


def resolve_search_topic(query: str) -> str:
    """
    Resolve user query to a GitHub search topic for find_similar_projects.
    - 'Help Me Pro' or similar → top repos like Help Me Pro (AI coding assistant).
    - New feature / module request → feature description for repo search.
    """
    if not query or not str(query).strip():
        return "python"
    q = str(query).strip().lower()
    # Help Me Pro or “project like X” → search for similar product
    if any(
        x in q
        for x in [
            "help me pro",
            "مساعد برمجة",
            "مشروع مساعد",
            "مثل مساعد",
            "نفس المشروع",
            "مشاريع مشابهة",
            "similar project",
        ]
    ):
        return HELP_ME_PRO_QUERIES[0]
    # Feature / module / implement → use query (possibly shortened) as topic
    return query.strip()[:200]


# GitHub token from core.config (مصدر واحد لجميع الاتصالات)
def _headers() -> dict:
    try:
        from core.config import GITHUB_TOKEN
        token = GITHUB_TOKEN or ""
    except ImportError:
        import os
        token = os.getenv("GITHUB_TOKEN", "")
    h = {"Accept": "application/vnd.github.v3+json"}
    if token:
        h["Authorization"] = f"token {token}"
    return h


def find_similar_projects(topic: str, max_repos: int = 3) -> List[Dict[str, Any]]:
    """
    البحث عن مشاريع مشابهة لتعلم الهيكل البرمجي (Python، مرتبة حسب النجوم).
    Returns list of {"name": full_name, "url": html_url, "desc": description}.
    """
    if not topic or not str(topic).strip():
        return []

    url = "https://api.github.com/search/repositories"
    params = {
        "q": f"{topic.strip()[:200]} language:python",
        "sort": "stars",
        "order": "desc",
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=_headers(),
            timeout=10,
        )
        if response.status_code != 200:
            return []
        data = response.json()
        items = data.get("items") or []
        repos = items[:max_repos]
        return [
            {
                "name": r.get("full_name") or "",
                "url": r.get("html_url") or "",
                "desc": (r.get("description") or "").strip() or "—",
            }
            for r in repos
        ]
    except Exception:
        return []


def similar_projects_to_prompt(projects: List[Dict[str, Any]]) -> str:
    """Format find_similar_projects output as text for the agent prompt."""
    if not projects:
        return ""
    lines = []
    for i, p in enumerate(projects, 1):
        name = p.get("name") or ""
        url = p.get("url") or ""
        desc = (p.get("desc") or "").strip() or "—"
        lines.append(f"{i}. {name}\n   URL: {url}\n   Description: {desc}")
    return "Similar Python projects (structure reference):\n" + "\n\n".join(lines)


def architect_mode_instruction() -> str:
    """Instruction for Architect Mode: benchmark Top 3 before implementing."""
    return (
        "**Architect Mode:** Before implementing a new module or feature, you MUST summarize "
        "how each of the Top 3 similar projects above handles the same logic (1–2 sentences per project). "
        "Then suggest your implementation. Do not use Markdown # or ## headers; keep a clean 18px-style layout."
    )


def lessons_learned_entry(projects: List[Dict[str, Any]], topic: str) -> str:
    """Build a one-block 'Lessons Learned' entry for knowledge_base.md push."""
    if not projects:
        return ""
    names = ", ".join((p.get("name") or p.get("url") or "?") for p in projects[:3])
    return f"[Architect Mode – Lessons Learned] Topic: {topic[:200]}. Reference repos: {names}. Use these patterns for future implementations."
