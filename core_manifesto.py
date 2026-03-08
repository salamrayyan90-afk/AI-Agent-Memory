"""
AI Constitution and Professional Checklist. The agent MUST perform a Self-Audit
against this checklist before displaying the final output. If any check fails,
re-process until it meets the professional standards of Gemini.
"""
import re
from typing import List, Optional, Tuple

# --- AI Constitution ---
AI_CONSTITUTION = """
## AI Constitution — Core AI

1. **Truth:** Use only verified data (web search, knowledge_base). Never invent prices or facts.
2. **Memory First:** Always sync and use the latest knowledge_base.md before answering.
3. **Reasoning Loop:** Think (Chain of Thought), verify web data, then answer. No shortcut to the final answer.
4. **Format:** One consistent font level (18px). No Markdown headers (# or ##). Use **bold** for emphasis only.
5. **Persona:** Senior Technical Expert — serious, precise, authoritative. No fluff or unnecessary greetings.
6. **Language:** White Arabic Dialect (لهجة بيضاء) mixed with professional English technical terms where necessary.
7. **Intelligence:** If the user asks for data, trigger web_scout. Cross-reference all findings with March 7, 2026. If conflict between internal knowledge and web data, prioritize web and state: تم التحقق وتحديث البيانات بناءً على المصدر الحي.
8. **Self-Update:** Every verified fact is appended to GitHub memory. State facts clearly for recording.
9. **Safety:** Financial or destructive actions require explicit user approval. Never execute without confirmation.
"""

# --- Professional Checklist (for Self-Audit) ---
PROFESSIONAL_CHECKLIST = """
## Professional Checklist — Self-Audit before output

Before displaying any response, the agent MUST pass ALL of the following:

1. **No large headers:** Response must NOT contain Markdown # or ## (use bold only). Font consistency 18px.
2. **Data grounded:** If the query was about prices or facts, the answer must use numbers/sources from the provided web data, not training data.
3. **Not outdated:** For time-sensitive queries (e.g. today's gold price), the answer must reference current/web data and date (cross-reference March 7, 2026).
4. **Substantive:** Response must not be empty or purely placeholder.
5. **Expert tone:** Senior Technical Expert — White Arabic Dialect (لهجة بيضاء) with English technical terms; serious, precise; data first, then reasoning, then tip.
6. **No internal leakage:** The visible response must not include the internal plan (Steps 1–3); only content after ---RESPONSE---.
"""


def _check_no_markdown_headers(text: str) -> Tuple[bool, str]:
    """Check that response does not use # or ## (lines starting with headers)."""
    if not text or not text.strip():
        return True, ""
    lines = text.strip().split("\n")
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# ") or stripped.startswith("## ") or stripped.startswith("### "):
            return False, f"Response contains Markdown headers (#): '{stripped[:50]}...'"
    return True, ""


def _check_not_empty(text: str) -> Tuple[bool, str]:
    """Check that response is substantive."""
    if not text or not text.strip():
        return False, "Response is empty."
    if len(text.strip()) < 10:
        return False, "Response too short (placeholder?)."
    return True, ""


def _check_price_grounded(text: str, verified_web_prices: Optional[List[float]]) -> Tuple[bool, str]:
    """If this was a price query and we have web prices, response should contain at least one of them (or close)."""
    if not verified_web_prices or not text:
        return True, ""
    text_clean = text.replace(",", "").replace(" ", "")
    for p in verified_web_prices[:10]:
        # Check if this price (or rounded) appears in the response
        if str(int(p)) in text or str(round(p, 2)) in text or (f"{p:.2f}" in text) or (f"{p:.0f}" in text):
            return True, ""
    # Allow if response has any plausible number (e.g. from web)
    numbers = re.findall(r"[\d,]+(?:\.[\d]+)?", text)
    for n in numbers:
        try:
            v = float(n.replace(",", ""))
            if any(abs(v - p) / max(p, 1) < 0.1 for p in verified_web_prices):
                return True, ""
        except ValueError:
            pass
    return False, "Price query but response does not appear to use verified web numbers. Re-ground in web data."


def run_self_audit(
    response: str,
    *,
    verified_web_prices: Optional[List[float]] = None,
    is_price_or_fact_query: bool = False,
) -> Tuple[bool, List[str]]:
    """
    Run Self-Audit against the Professional Checklist. Returns (passed, list_of_failure_messages).
    If passed is False, the agent must re-process the answer.
    """
    failures: List[str] = []
    if not response or not response.strip():
        return False, ["Response is empty."]

    ok, msg = _check_no_markdown_headers(response)
    if not ok:
        failures.append(msg)

    ok, msg = _check_not_empty(response)
    if not ok:
        failures.append(msg)

    if is_price_or_fact_query and verified_web_prices:
        ok, msg = _check_price_grounded(response, verified_web_prices)
        if not ok:
            failures.append(msg)

    return len(failures) == 0, failures


def get_self_audit_prompt_for_retry(failed_checks: List[str], user_query: str, web_context: str = "") -> str:
    """Build prompt to re-process the answer when Self-Audit fails."""
    return (
        "Self-Audit FAILED. Your previous response did not meet the Professional Checklist (core_manifesto.py).\n\n"
        "Failures:\n" + "\n".join(f"- {f}" for f in failed_checks) + "\n\n"
        "You MUST re-process and output a new answer that:\n"
        "1. Does NOT use Markdown # or ## (use **bold** only).\n"
        "2. Uses ONLY numbers/sources from the web data below for any price or fact.\n"
        "3. Is substantive and in Senior Technical Expert tone — White Arabic Dialect, data first, reasoning, proactive tip.\n\n"
        f"User asked: {user_query}\n\n"
        + (f"Web data to use:\n{web_context}\n\n" if web_context else "")
        + "Output ONLY the corrected final answer (no internal plan, no ---RESPONSE---)."
    )
