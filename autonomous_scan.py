"""
Autonomous Proactive Loop — مسح تلقائي كل ساعة:
- فحص تحديثات تقنية/أمنية (مكتبات Help Me Pro / Core AI)
- فحص أسواق (ذهب وعملات)
- إذا وُجد تحديث مكتبات: الوكيل يكتب الإصلاح ويحفظه في proposed_updates/
- كل نتيجة تُحفظ في knowledge_base.md (Self-Training 24/7)
- autonomous_log.md يُحدَّث للواجهة (Proactive Suggestions)
"""
import sys
import time
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import schedule
from core.advanced_search import AdvancedCoreSearch
from memory.github_rag import (
    update_github_repo,
    update_agent_knowledge,
    push_proposed_update,
)

# Optional: Groq for generating proposed fix (agent writes the fix)
_groq_client = None
_groq_model = None


def _get_groq():
    global _groq_client, _groq_model
    if _groq_client is not None:
        return _groq_client, _groq_model
    try:
        from groq import Groq
        from core.config import GROQ_API_KEY, GROQ_VISION_MODEL
        if GROQ_API_KEY:
            _groq_client = Groq(api_key=GROQ_API_KEY)
            _groq_model = GROQ_VISION_MODEL or "llama-3.1-8b-instant"
            return _groq_client, _groq_model
    except Exception:
        pass
    return None, None


def _generate_proposed_fix(tech_findings: str) -> str:
    """Use the agent to write a short fix/migration note for Help Me Pro libraries."""
    client, model = _get_groq()
    if not client or not model or not tech_findings or len(tech_findings.strip()) < 50:
        return ""
    try:
        prompt = (
            "Based on the following security/tech findings for a Python project (Help Me Pro / Core AI) "
            "that uses streamlit, groq, requests, beautifulsoup4, duckduckgo-search, chromadb, langchain, playwright:\n\n"
            f"{tech_findings[:2000]}\n\n"
            "Write a short proposed update document (Markdown): "
            "1) Summary of the finding, 2) Recommended action (e.g. upgrade package X to Y, or apply patch), "
            "3) One or two code/config lines if relevant. Keep under 400 words. Use clear headings."
        )
        r = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a senior devops engineer. Output only the proposed update document in Markdown."},
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )
        return (r.choices[0].message.content or "").strip()
    except Exception:
        return ""


def run_autonomous_scan_once() -> dict:
    """
    Run one full autonomous scan. Call this from a background thread or from __main__.
    - Self-Training: every finding is appended to knowledge_base.md via update_agent_knowledge.
    - If tech findings exist: agent generates a fix and saves to proposed_updates/.
    - Updates memory/autonomous_log.md for the UI (Proactive Suggestions).
    Returns dict with keys: tech, market, proposed_fix_path, summary, success.
    """
    result = {"tech": "", "market": "", "proposed_fix_path": None, "summary": "", "success": False}
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 1. Tech / security scan (Help Me Pro libraries) — strict filter for 2026
    tech_updates = ""
    try:
        acs = AdvancedCoreSearch()
        tech_updates = acs.web_scout("latest python security patches 2026", max_results=6, filter_date="2026")
        if not tech_updates:
            tech_updates = acs.web_scout("streamlit langchain security update 2026", max_results=4, filter_date="2026")
    except Exception:
        pass
    result["tech"] = tech_updates or "(no new tech findings)"

    # 2. Market scan (gold, etc.)
    market_updates = ""
    try:
        market_updates = AdvancedCoreSearch().fetch_live_gold()
    except Exception:
        pass
    result["market"] = market_updates or "(no market data)"

    # 3. Self-Training: save every finding to knowledge_base.md (24/7)
    try:
        if tech_updates and tech_updates.strip():
            update_agent_knowledge(f"[Autonomous Scan {ts}] Tech/Security: {tech_updates.strip()[:2500]}")
        if market_updates and market_updates.strip():
            update_agent_knowledge(f"[Autonomous Scan {ts}] Market: {market_updates.strip()[:1500]}")
    except Exception:
        pass

    # 4. If tech finding is substantial → agent writes fix → proposed_updates/
    proposed_path = None
    if tech_updates and len(tech_updates.strip()) >= 80:
        fix_doc = _generate_proposed_fix(tech_updates)
        if fix_doc:
            safe_ts = datetime.now().strftime("%Y-%m-%d_%H")
            filename = f"{safe_ts}_security-fix.md"
            try:
                if push_proposed_update(filename, fix_doc):
                    proposed_path = f"proposed_updates/{filename}"
            except Exception:
                pass
    result["proposed_fix_path"] = proposed_path

    # 5. Build summary and update autonomous_log.md for UI
    summary_lines = [
        f"# Proactive Suggestions — Last scan: {ts}",
        "",
        "## Security / Tech",
        (tech_updates[:800] + ("..." if len(tech_updates) > 800 else "")) if tech_updates else "(no new findings)",
        "",
        "## Market",
        (market_updates[:400] + ("..." if len(market_updates) > 400 else "")) if market_updates else "(no data)",
        "",
    ]
    if proposed_path:
        summary_lines.append(f"## Proposed fix saved\n- `{proposed_path}`")
    summary = "\n".join(summary_lines)
    result["summary"] = summary

    try:
        result["success"] = update_github_repo("autonomous_log.md", summary)
    except Exception:
        pass

    return result


def autonomous_scan():
    """Legacy entry point: one scan + print (for schedule or CLI)."""
    print("--- بدء الفحص الدوري المستقل ---")
    r = run_autonomous_scan_once()
    if r["success"]:
        print("--- تم تحديث الذاكرة بنجاح ---")
    else:
        print("--- تحذير: تعذر رفع المستودع (تحقق من GITHUB_TOKEN و GITHUB_REPO) ---")
    return r


# جدولة كل ساعة عند التشغيل المباشر
schedule.every().hour.do(autonomous_scan)

if __name__ == "__main__":
    autonomous_scan()
    while True:
        schedule.run_pending()
        time.sleep(1)
