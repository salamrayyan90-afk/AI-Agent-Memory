import sys
import subprocess
import os

try:
    from groq import Groq
    import psutil
except ModuleNotFoundError as e:
    _root = os.path.dirname(os.path.abspath(__file__))
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "groq", "psutil", "python-dotenv", "streamlit", "requests"],
        cwd=_root,
    )
    print("Installed groq, psutil, python-dotenv, streamlit, requests. Please restart the Streamlit app.")
    sys.exit(0)

import streamlit as st
import re
import base64
import io
import time
from datetime import datetime
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from PIL import Image
import psutil

# Required: groq (reasoning/Vision), psutil (sidebar System Status). Gemini API connected via init_core_ai().

try:
    from streamlit_paste_button import paste_image_button
except ImportError:
    paste_image_button = None
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

try:
    from core.advanced_search import AdvancedCoreSearch
except ImportError:
    AdvancedCoreSearch = None
try:
    from memory.vector_rag import query_vector_db, ensure_rag_context_loaded
except ImportError:
    query_vector_db = lambda q, k=5: ""
    ensure_rag_context_loaded = lambda: None
try:
    from core.research import research_for_query
except ImportError:
    research_for_query = lambda q: ""
try:
    from core.autonomous_agent import get_autonomous_agent
except ImportError:
    get_autonomous_agent = lambda: None
try:
    from core.stack_overflow import stack_overflow_search
except ImportError:
    stack_overflow_search = lambda q, max_items=3: ("", [])
try:
    from core.github_projects import (
        find_similar_projects,
        similar_projects_to_prompt,
        resolve_search_topic,
        architect_mode_instruction,
        lessons_learned_entry,
    )
except ImportError:
    find_similar_projects = lambda topic, max_repos=3: []
    similar_projects_to_prompt = lambda projects: ""
    resolve_search_topic = lambda q: (q or "")[:200]
    architect_mode_instruction = lambda: ""
    lessons_learned_entry = lambda projects, topic: ""

try:
    from core.file_editor import (
        apply_direct_edit,
        read_file as read_project_file,
        list_editable_files,
    )
except ImportError:
    apply_direct_edit = lambda path, content, summary, **kw: (False, "File editor not available")
    read_project_file = lambda path: None
    list_editable_files = lambda subdir="": []
try:
    from core.vision_analysis import run_core_vision_analysis, push_visual_insights_to_github
except ImportError:
    run_core_vision_analysis = lambda img, q="": {"report": "", "enhancement_code": "", "visual_errors": [], "auto_fix_script": "", "raw": ""}
    push_visual_insights_to_github = lambda a, b, c="": False

try:
    from core_manifesto import (
        AI_CONSTITUTION,
        PROFESSIONAL_CHECKLIST,
        run_self_audit,
        get_self_audit_prompt_for_retry,
    )
except ImportError:
    AI_CONSTITUTION = ""
    PROFESSIONAL_CHECKLIST = ""
    run_self_audit = lambda r, **kw: (True, [])
    get_self_audit_prompt_for_retry = lambda a, b, c="": ""

# Paths relative to app directory (portable for Linux/cloud)
ROOT = Path(__file__).resolve().parent
ICON_PATH = ROOT / "CoreAI.ico"
# set_page_config must be the first Streamlit command (prevents deployment errors)
try:
    st.set_page_config(
        page_title="CORE AI",
        layout="wide",
        initial_sidebar_state="expanded",
        icon=str(ICON_PATH) if ICON_PATH.is_file() else None,
    )
except Exception:
    st.set_page_config(page_title="CORE AI", layout="wide", initial_sidebar_state="expanded")
# Load credentials from .env for GroqCloud and GitHub
load_dotenv(ROOT / ".env")

# UI: single source of truth for font size (professional 2026 layout; no large headers)
UI_FONT_SIZE_PX = 18

# Lesson Learned: push once per process so agent recognizes the gold-price fact-check failure
_LESSON_GOLD_FAILURE_PUSHED = False
LESSON_LEARNED_GOLD = (
    "[Lesson Learned] Fact-checking failure: The agent once reported a gold price of $235 when the real-time value was $545.71 SAR. "
    "MUST verify figures from at least two sources dated March 7 2026 (or current date) before displaying any price. "
    "Never rely on a single source or old snippets. For gold: SAR/ريال per gram ~400-700; USD/oz 2000+."
)

try:
    from core.config import GROQ_API_KEY, GROQ_VISION_MODEL
except ImportError:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
try:
    from core.framework import init_core_ai
    from core.ui_theme import (
        get_streamlit_dark_css,
        get_logo_data_uri,
        get_blueprint_background_html,
        get_physics_background_full_html,
    )
except ImportError:
    init_core_ai = lambda: {}
    get_streamlit_dark_css = lambda px=18: ""
    get_logo_data_uri = lambda root: None
    get_blueprint_background_html = lambda: ""
    get_physics_background_full_html = lambda: ""

try:
    from memory.github_rag import (
        ensure_knowledge_base_initialized,
        ensure_system_config_initialized,
        get_latest_logs_for_session,
        get_system_config_from_github,
        pull_github_memory,
        sync_github_memory,
        sync_knowledge,
        read_from_github,
        update_agent_knowledge,
        append_to_knowledge_base,
        append_smart_learned_context,
        test_github_connection,
    )
except ImportError:
    ensure_knowledge_base_initialized = lambda: False
    ensure_system_config_initialized = lambda: False
    get_latest_logs_for_session = lambda: ""
    get_system_config_from_github = lambda: {"tone": "senior_technical_expert_white_arabic", "font_size": "18px", "web_search_priority": True}
    pull_github_memory = lambda max_files=10: ""
    sync_github_memory = lambda: ("", None)
    sync_knowledge = lambda: ("", None)
    read_from_github = lambda path="knowledge_base.md": ""
    update_agent_knowledge = lambda new_info: False
    append_to_knowledge_base = lambda entry, date_str=None: False
    append_smart_learned_context = lambda text: False
    test_github_connection = lambda: (False, "memory.github_rag not available")
try:
    from memory.smart_summarization import extract_learned_context
except ImportError:
    extract_learned_context = lambda user_msg, asst_resp: None

# Groq client for reasoning (Framework: Llama-3 high-speed)
try:
    from core.groq_client import get_groq_client
    client = get_groq_client() or Groq(api_key=os.getenv("GROQ_API_KEY") or GROQ_API_KEY)
except Exception:
    client = Groq(api_key=os.getenv("GROQ_API_KEY") or GROQ_API_KEY)

# --- Execution Trigger: agent remains idle until direct user command ---
# No background scans for gold or GitHub updates unless explicitly requested (e.g. "Update Gold", "Check Help Me Pro").
# _start_autonomous_loop() is intentionally NOT called; hourly scan disabled for on-demand-only operation.


def load_memory() -> tuple:
    """
    Initialize the agent's memory from GitHub at startup.
    Ensures knowledge_base.md and system_config.json exist on repo (with First Memory / defaults), reads both via GitHub API.
    Returns (kb_content: str, config: dict).
    """
    ensure_knowledge_base_initialized()
    ensure_system_config_initialized()
    kb_content = read_from_github("knowledge_base.md")
    config = get_system_config_from_github()
    return kb_content, config


def record_verified_fact(entry: str, date_str: Optional[str] = None) -> bool:
    """
    Self-Update: Append a verified fact to GitHub knowledge_base.md so the agent trains itself for next time.
    Call this every time a new fact is verified (e.g. after price or fact-checked answer).
    """
    if not entry or not entry.strip():
        return False
    try:
        return append_to_knowledge_base(entry.strip()[:2000], date_str)
    except Exception:
        return False


def run_smart_summarization_and_notify(user_input: str, assistant_response: str) -> bool:
    """
    Smart Summarization: extract only code snippets, verified data, user decisions via Groq;
    append to knowledge_base.md under ## Learned Context - 2026-03-07; show 18px notification on success.
    Returns True if something was extracted and saved.
    """
    if not assistant_response or not assistant_response.strip():
        return False
    try:
        extracted = extract_learned_context(user_input or "", assistant_response)
        if not extracted or not extracted.strip():
            return False
        ok = append_smart_learned_context(extracted)
        if ok:
            st.markdown(
                '<p style="font-size: 18px; margin: 0;">تم استخلاص الخلاصة وتحديث الذاكرة بنجاح</p>',
                unsafe_allow_html=True,
            )
        return ok
    except Exception:
        return False


def is_user_correction(user_input: str) -> bool:
    """True if the user message looks like a correction (e.g. 'لا، الصحيح...', 'actually it's')."""
    if not user_input or len(user_input.strip()) < 3:
        return False
    msg = user_input.strip().lower()
    correction_starts = ["لا،", "لا بل", "لا بل ", "الصحيح", "التصحيح", "actually", "wrong", "no,", "correction", "تصحيح", "المفروض", "صح"]
    if any(msg.startswith(s) or f" {s}" in msg for s in correction_starts):
        return True
    if "ليس " in msg or "مش " in msg or "ليس " in msg or "the correct" in msg or "the right" in msg:
        return True
    return False


def save_hard_rule_to_github(correction_text: str) -> bool:
    """Save user correction as a Hard Rule in knowledge_base.md for future. Self-Correction."""
    if not correction_text or not correction_text.strip():
        return False
    entry = f"[Hard Rule - user correction] {correction_text.strip()[:1500]}"
    try:
        return update_agent_knowledge(entry)
    except Exception:
        return False


def try_apply_user_price_correction(user_input: str) -> bool:
    """
    Self-Correction: If the user provides a newer price, update knowledge_base.md and PUSH to GitHub immediately.
    Returns True if an update was applied.
    """
    if not user_input or not user_input.strip():
        return False
    msg = user_input.strip().lower()
    # Detect user providing a price update (e.g. "السعر الجديد 5200", "الذهب الآن 5180", "update gold price to 5200")
    if any(
        x in msg
        for x in [
            "السعر الجديد",
            "السعر الآن",
            "الذهب الآن",
            "الذهب الجديد",
            "update price",
            "update gold",
            "new price",
            "سعر الذهب الآن",
            "أحدث سعر",
        ]
    ) or re.search(r"\d{4,}(?:\.\d+)?\s*(?:usd|\$|دولار|sar|ريال)", msg):
        entry = f"User-provided price update: {user_input.strip()[:1500]}"
        try:
            return update_agent_knowledge(entry)
        except Exception:
            return False
    return False


def sanitize_response_headers(text: str) -> str:
    """
    Mandatory Check for every on-demand request: 18px font equivalent, Zero Headers (#).
    Converts # Title to **Title** (bold, no header). ZERO # in final output.
    """
    if not text or not text.strip():
        return text
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#"):
            # Remove leading # and optional spaces; treat rest as bold
            rest = re.sub(r"^#+\s*", "", stripped).strip()
            if rest:
                lines.append("**" + rest + "**")
            else:
                lines.append("")
        else:
            lines.append(line)
    return "\n".join(lines)


def pil_to_base64_data_url(pil_img: Image.Image, fmt: str = "PNG") -> str:
    buf = io.BytesIO()
    pil_img.save(buf, format=fmt if pil_img.mode != "RGBA" else "PNG")
    b64 = base64.standard_b64encode(buf.getvalue()).decode("utf-8")
    mime = "image/png" if fmt == "PNG" else "image/jpeg"
    return f"data:{mime};base64,{b64}"


# Keywords that trigger real-time web search (prices, news, latest tech)
WEB_SEARCH_KEYWORDS = [
    "سعر", "أسعار", "أخبار", "بحث", "ابحث", "اشتري", "منتج", "كم سعر", "أحدث",
    "تقنية", "تكنولوجيا", "tech", "technology",
    "price", "prices", "news", "search", "buy", "latest", "today", "current",
]

def needs_web_search(query: str) -> bool:
    """True if the query is about prices, news, tech, or asking to search."""
    if not query or not query.strip():
        return False
    q = query.strip().lower()
    return any(kw in q for kw in WEB_SEARCH_KEYWORDS)


# --- Action Picker: same rigorous Search-then-Answer for ALL topics ---
def action_picker(query: str) -> str:
    """
    Autonomous Tool Use: pick the right tool for the query.
    Returns: "price" | "code" | "facts" | "general"
    - price → price-radar / live price logic
    - code → auto-read GitHub + RAG (and docs)
    - facts / general → auto-search Web
    """
    if not query or not query.strip():
        return "general"
    q = query.strip().lower()
    if needs_live_price_prompt(query) or needs_price_radar(query):
        return "price"
    code_kw = ["كود", "code", "github", "برمجة", "programming", "python", "api", "دالة", "function", "مكتبة", "library", "syntax", "خطأ", "error", "bug", "ميزة", "feature", "implement", "module", "هيكل", "مشروع", "مثل help me pro"]
    if any(kw in q for kw in code_kw):
        return "code"
    facts_kw = ["أخبار", "news", "بحث", "ابحث", "fact", "حقيقة", "اليوم", "today", "أحدث", "latest", "سعر", "price"]
    if any(kw in q for kw in facts_kw):
        return "facts"
    return "general"


def web_search_tool(query: str, max_results: int = 6) -> tuple:
    """
    Autonomous Search: fetch real-time data (DuckDuckGo). Agent triggers this when real-time data is needed.
    Returns (raw_text, rows) for prompt injection and Top 3 table.
    """
    try:
        from core.autonomous_search import autonomous_web_search
        return autonomous_web_search(query, max_results=max_results)
    except Exception:
        pass
    if not query or not query.strip():
        return "", []
    if DDGS is None:
        return "", []
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query.strip(), max_results=max_results))
        if not results:
            return "", []
        rows = []
        lines = []
        for r in results:
            href = r.get("href") or r.get("link") or ""
            body = r.get("body") or r.get("snippet") or ""
            title = r.get("title") or body[:80] or "—"
            rows.append({"title": title, "href": href, "body": body})
            lines.append(f"Source: {href}\nSnippet: {body}")
        return "\n\n".join(lines), rows
    except Exception:
        return "", []


def top3_table_markdown(rows: list) -> str:
    """Format top 3 search results as a markdown table for the chat."""
    if not rows:
        return ""
    top3 = rows[:3]
    header = "| # | Title | Snippet | Link |"
    sep = "| --- | --- | --- | --- |"
    body_lines = []
    for i, r in enumerate(top3, 1):
        title = (r.get("title") or "")[:60].replace("|", " ")
        snippet = (r.get("body") or "")[:100].replace("|", " ").replace("\n", " ")
        link = r.get("href") or ""
        body_lines.append(f"| {i} | {title} | {snippet} | [Link]({link}) |")
    return "\n\n**Top 3 results:**\n\n" + header + "\n" + sep + "\n" + "\n".join(body_lines)


def load_gemini_expertise() -> str:
    """Load Gemini_Expertise_Transfer.md so every response is grounded in its logic."""
    path = ROOT / "Gemini_Expertise_Transfer.md"
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


REASONING_AGENT_DELIMITER = "---RESPONSE---"


def get_current_date_context() -> str:
    """Return current system date for model context (today's search results)."""
    return datetime.now().strftime("%Y-%m-%d")


# --- Gemini Search Protocol ---
def get_current_date_strings() -> list:
    """Strings to match in snippets for context validation (today's timestamp)."""
    now = datetime.now()
    return [
        f"{now.strftime('%B')} {now.day}",   # March 7
        now.strftime("%d/%m"),               # 07/03
        now.strftime("%Y-%m-%d"),            # 2026-03-07
        now.strftime("%m/%d/%Y"),            # 03/07/2026
        f"{now.day} {now.strftime('%B')}",   # 7 March
        now.strftime("%B %d"),               # March 07
    ]


def validate_snippets_for_today(rows: list, current_date: str) -> tuple:
    """
    Context Validation: keep only snippets that contain today's date (e.g. March 7, 2026).
    STRICT: must include year 2026 (or current year) and date marker. Reject data without timestamp.
    Returns (filtered_rows, raw_text).
    """
    if not rows:
        return [], ""
    date_strings = get_current_date_strings()
    date_strings.append(current_date)
    d = datetime.now()
    date_strings.extend([f"March {d.day}", f"{d.day:02d}/03", "03/07", "March 7", "7 March", "2026", "March 7, 2026", "7 March 2026"])
    filtered = []
    for r in rows:
        text = ((r.get("body") or "") + " " + (r.get("title") or "")).strip()
        # Require at least one date string AND (2026 or current year) for strictness
        has_date = any(ds in text for ds in date_strings if ds)
        has_year = str(d.year) in text or "2026" in text
        if has_date and has_year:
            filtered.append(r)
    if not filtered:
        return [], ""
    lines = []
    for r in filtered:
        href = r.get("href") or ""
        body = r.get("body") or ""
        lines.append(f"Source: {href}\nSnippet: {body}")
    return filtered, "\n\n".join(lines)


def price_search_strict(query: str, current_date: str, min_sources: int = 2) -> tuple:
    """
    Price search with strict filter: only return data when we have at least min_sources
    snippets that contain the current date (March 7, 2026). Tries query + date explicitly.
    Returns (raw_text, rows) or ("", []) if insufficient verified sources.
    """
    if not query or not query.strip() or DDGS is None:
        return "", []
    # Inject date into query to bias results toward today
    date_queries = [
        f"{query.strip()} {current_date}",
        f"{query.strip()} March 7 2026",
        f"سعر الذهب 7 مارس 2026",
        f"gold price March 7 2026",
    ]
    all_rows = []
    seen_hrefs = set()
    for q in date_queries:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(q, max_results=6, timelimit="d"))
        except Exception:
            continue
        for r in results:
            href = r.get("href") or r.get("link") or ""
            if href and href not in seen_hrefs:
                seen_hrefs.add(href)
                all_rows.append({
                    "title": (r.get("title") or "").strip(),
                    "href": href,
                    "body": (r.get("body") or r.get("snippet") or "").strip(),
                })
        filtered, raw = validate_snippets_for_today(all_rows, current_date)
        if len(filtered) >= min_sources:
            return raw, filtered
    # Last attempt: validate whatever we have
    filtered, raw = validate_snippets_for_today(all_rows, current_date)
    if len(filtered) >= min_sources:
        return raw, filtered
    return "", []


def apply_gemini_search_protocol(
    web_data: str, search_rows: list, current_date: str, user_input: str
) -> tuple:
    """
    Gemini Search Protocol: (1) Context Validation — keep only snippets with today's date;
    (2) Gold ratio cross-check — if conflict, add third source. Returns (final_raw, final_rows).
    """
    if not web_data and not search_rows:
        return "", []
    # Context Validation: reject data without today's timestamp
    filtered_rows, filtered_raw = validate_snippets_for_today(search_rows, current_date)
    use_raw = filtered_raw if filtered_raw else web_data
    use_rows = filtered_rows if filtered_rows else search_rows
    # Mathematical Cross-Check (gold): if ratio conflict, add third source
    aligned, third_source = gold_ratio_cross_check(use_rows, use_raw, user_input)
    if not aligned and third_source:
        use_raw = use_raw + "\n\n[Third source — conflict resolution]:\n" + third_source
    return use_raw, use_rows


def gold_ratio_cross_check(rows: list, raw_text: str, query: str) -> tuple:
    """
    Mathematical Cross-Check: Global Spot Gold (USD/oz) vs Local Retail. If they don't align within 5%, fetch third source.
    Returns (aligned: bool, third_source_raw: str).
    """
    q = (query or "").lower()
    if "gold" not in q and "ذهب" not in q and "gold" not in (raw_text or "").lower():
        return True, ""
    prices = extract_price_numbers_from_text(raw_text or "")
    # Plausible spot range USD/oz (e.g. 2000-3500); filter to same-unit candidates
    spot_like = sorted(set(p for p in prices if 2000 <= p <= 4000))
    if len(spot_like) < 2:
        return True, ""
    low, high = min(spot_like), max(spot_like)
    ratio = high / low if low else 1
    if ratio > 1.05:
        if DDGS:
            try:
                with DDGS() as ddgs:
                    third = list(ddgs.text("gold spot price March 7 2026 USD per ounce", max_results=5))
                    if not third:
                        third = list(ddgs.text("سعر الذهب عالمي اليوم USD", max_results=5))
                    if third:
                        lines = [f"Source: {r.get('href','')}\nSnippet: {r.get('body','')}" for r in third]
                        return False, "\n\n".join(lines)
            except Exception:
                pass
    return True, ""


def highlight_prices_in_text(text: str) -> str:
    """Pre-process search results: highlight $ and JOD (and similar) so the model sees prices clearly."""
    if not text:
        return text
    result = text
    result = re.sub(r"(\$\s*[\d,]+(?:\.[\d]+)?)", r"**PRICE \1**", result)
    result = re.sub(r"([\d,]+(?:\.[\d]+)?\s*(?:JOD|USD|دينار|د\.ك))", r"**PRICE \1**", result, flags=re.IGNORECASE)
    result = re.sub(r"((?:JOD|USD)\s*[\d,]+(?:\.[\d]+)?)", r"**PRICE \1**", result, flags=re.IGNORECASE)
    return result


def extract_price_numbers_from_text(text: str) -> list:
    """Extract numeric price-like values from text (for self-correction check)."""
    if not text:
        return []
    numbers = []
    # Match numbers with optional currency or comma/dot
    for m in re.finditer(r"[\d,]+(?:\.[\d]+)?", text):
        s = m.group(0).replace(",", "")
        try:
            v = float(s)
            if 0.1 < v < 1e10:  # plausible price range
                numbers.append(round(v, 2))
        except ValueError:
            pass
    return numbers


def plan_contradicts_web_data(plan_text: str, web_raw: str) -> bool:
    """True if the plan mentions a price that is not supported by web data (contradiction)."""
    plan_all = extract_price_numbers_from_text(plan_text)
    # Ignore small integers (e.g. Step 1, 2, 3) — keep only price-like numbers
    plan_prices = set(p for p in plan_all if p >= 10 or (p != int(p)))
    web_prices = set(extract_price_numbers_from_text(web_raw))
    if not web_prices or not plan_prices:
        return False
    for p in plan_prices:
        if p in web_prices:
            continue
        if any(abs(p - w) / max(w, 1) < 0.05 for w in web_prices):
            continue
        return True
    return False


# Baseline reference (March 7, 2026) — Logic Rule: difference > 2% → Volatile Market alert + update KB
GOLD_SPOT_BASELINE_OZ = 5172.89
GOLD_21K_SAR_BASELINE = 545.71
VOLATILITY_THRESHOLD_PCT = 0.02


def get_last_verified_from_kb(knowledge_base: str, max_chars: int = 1200) -> str:
    """
    Extract a short 'last verified' snippet from knowledge_base.md for use when no live price is found.
    Used to show last verified price with an 'Outdated' warning instead of 'No price found'.
    """
    if not knowledge_base or not knowledge_base.strip():
        return ""
    kb = knowledge_base.strip()
    # Prefer a block that contains price-like numbers and a date (YYYY-MM-DD or March 7, 2026)
    lines = kb.split("\n")
    chunk = []
    for line in lines:
        if any(x in line for x in ["$", "SAR", "ريال", "USD", "oz", "عيار", "Spot", "545", "5172", "March 7", "2026"]):
            chunk.append(line)
        if len(chunk) >= 15:
            break
    if not chunk:
        # Fallback: first 800 chars that might contain baseline
        for i, line in enumerate(lines):
            if i > 30:
                break
            chunk.append(line)
    text = "\n".join(chunk)[:max_chars] if chunk else kb[:max_chars]
    return text.strip()


def check_volatile_market(verified_prices: list) -> tuple:
    """
    Compare web prices to baseline. If any difference > 2%, return (True, alert_message) and caller should update KB.
    Returns (is_volatile: bool, alert_message: str).
    """
    if not verified_prices:
        return False, ""
    prices = sorted(set(verified_prices))
    alerts = []
    for p in prices:
        if 2000 <= p <= 7000:
            diff_pct = abs(p - GOLD_SPOT_BASELINE_OZ) / GOLD_SPOT_BASELINE_OZ
            if diff_pct > VOLATILITY_THRESHOLD_PCT:
                alerts.append(f"Global Spot: baseline ${GOLD_SPOT_BASELINE_OZ:.2f}/oz vs web ${p:.2f} ({diff_pct*100:.1f}% diff)")
        if 400 <= p <= 800:
            diff_pct = abs(p - GOLD_21K_SAR_BASELINE) / GOLD_21K_SAR_BASELINE
            if diff_pct > VOLATILITY_THRESHOLD_PCT:
                alerts.append(f"Local 21K (KSA): baseline {GOLD_21K_SAR_BASELINE} SAR vs web {p:.2f} ({diff_pct*100:.1f}% diff)")
    if not alerts:
        return False, ""
    return True, "**Volatile Market Alert:** " + "; ".join(alerts) + ". Baseline updated in knowledge_base.md."


def get_verified_prices_from_search(search_results: str) -> list:
    """Extract numerical price-like values from search_results first (for strict fact-checking)."""
    return extract_price_numbers_from_text(search_results or "")


def get_core_logic_response(
    user_query: str,
    search_results: str,
    github_memory: str,
    knowledge_base: str = "",
    verified_web_prices: Optional[list] = None,
    rag_context: str = "",
    research_context: str = "",
) -> str:
    """
    STRICT OPERATING ENVIRONMENT + Strict Fact-Checking flow.
    verified_web_prices: numbers extracted from search_results; agent MUST use these and emit Data Discrepancy Alert on conflict.
    """
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    kb_section = ""
    if knowledge_base and knowledge_base.strip():
        kb_section = f"""
KNOWLEDGE BASE (knowledge_base.md — use with expert logic from Gemini_Expertise_Transfer.md; if stale for prices, use only web data below):
{knowledge_base[:6000]}

"""
    # Extract numerical values from search_results first (strict fact-checking)
    web_prices = verified_web_prices if verified_web_prices is not None else get_verified_prices_from_search(search_results)
    web_prices_str = ", ".join(f"${p}" for p in sorted(set(web_prices))[:20]) if web_prices else "(none extracted)"
    fact_check_block = f"""
STRICT FACT-CHECKING (mandatory):
1. VERIFIED NUMBERS FROM WEB (extracted from search results): {web_prices_str}
2. Baseline reference (knowledge_base.md): Global Spot $5,172.89/oz, Local 21K (KSA) 545.71 SAR (March 7, 2026). Cross-reference all findings with March 7, 2026.
3. If a conflict exists between internal knowledge and web data: prioritize the web and state: تم التحقق وتحديث البيانات بناءً على المصدر الحي. Use ONLY the web value.
4. If no conflict, use the web numbers as the source of truth. Do not invent or substitute prices from training data.
"""
    extra = ""
    if rag_context and rag_context.strip():
        extra += f"""
**RAG (local vector DB — previous projects / Help Me Pro context):**
{rag_context[:4000]}

"""
    if research_context and research_context.strip():
        extra += f"""
**Research (Alpha Vantage / official docs):**
{research_context[:3000]}

"""
    return f"""
STRICT OPERATING ENVIRONMENT: CORE AI AGENT
CURRENT TIME: {current_date}

PERSONA: Act as a Senior Technical Expert. Tone: serious, precise, authoritative. No fluff or unnecessary greetings.
LANGUAGE: Use White Arabic Dialect (لهجة بيضاء) mixed with professional English technical terms where necessary.
UI: Strictly 18px font for all outputs. Zero Headers Policy — do NOT use #, ##, ###. Use **bold** for emphasis only.
INTELLIGENCE: Cross-reference all findings with March 7, 2026. If conflict between internal knowledge and web data, prioritize web and state: تم التحقق وتحديث البيانات بناءً على المصدر الحي.

GEMINI SEARCH PROTOCOL:
- Mandatory Verification: Never provide financial data from internal memory. You MUST use a live search and verify against current date (March 7, 2026).
- Zero-Trust Policy: Do NOT use internal knowledge for prices. Always use ONLY the fresh web search results provided below.
- Source Priority: For gold in KSA and Jordan, prioritize local sources (e.g. saudigoldprice.com) when present in the results.
- Reply structure: (1) **Data first** — state the numbers and sources, (2) **Reasoning** — brief why, (3) **Proactive tip** — e.g. "Wait for the evening fix" / "شوف المساء للتحديث".

{fact_check_block}
{extra}
LOGIC FRAMEWORK:
1. FACTUAL PRIORITY: The 'Web Search Results' below are the ONLY source of truth. Use the VERIFIED NUMBERS FROM WEB above.
2. MEMORY INTEGRATION: Read the 'GitHub Memory' and Knowledge Base below. Apply expert reasoning; for prices always prefer web.
3. FORMATTING: 18px font only. NO Markdown headers (#). Use **Bold** for emphasis.
4. REASONING: Show your logic step-by-step but keep the final answer focused on the LATEST data.
{kb_section}
GITHUB MEMORY (Your past experience):
{github_memory or "(None loaded.)"}

WEB SEARCH RESULTS (Real-time data — use these numbers only):
{search_results}
"""


def build_reasoning_agent_system(
    expertise: str,
    current_date: str = "",
    github_rag_text: str = "",
    knowledge_base: str = "",
    kb_stale_for_price: bool = False,
    rag_context: str = "",
    research_context: str = "",
) -> str:
    """Build system prompt for the Reasoning Agent (Gemini-style: CoT, RAG, Research, expertise)."""
    date_note = f"\n\n**Current date (today): {current_date}** — Treat search results as referring to this date.\n" if current_date else ""
    data_date = current_date or "March 7, 2026"
    rag_block = ""
    if github_rag_text and github_rag_text.strip():
        rag_block = """
**Deep Memory (GitHub logs)** — You MUST read the following logs from the private repo to understand past errors and successes before generating a new response. Use this context to avoid repeating mistakes.

""" + github_rag_text[:12000] + "\n\n---\n\n"
    vector_rag_block = ""
    if rag_context and rag_context.strip():
        vector_rag_block = """
**RAG (local vector DB)** — Relevant previous projects / Help Me Pro context from GitHub. Use this before answering.

""" + rag_context[:6000] + "\n\n---\n\n"
    research_block = ""
    if research_context and research_context.strip():
        research_block = """
**Research (Alpha Vantage / official docs)** — Use this data for gold/finance or coding answers.

""" + research_context[:4000] + "\n\n---\n\n"
    kb_block = ""
    if knowledge_base and knowledge_base.strip():
        kb_block = """
**Knowledge base (knowledge_base.md)** — Use this as prior context. Apply reasoning from Gemini_Expertise_Transfer.md: decide if this information needs updating or if current memory is sufficient. For prices: if the date in the knowledge base is before today (""" + data_date + """), you MUST rely only on fresh web search data, not the old memory.

**Data priority (RAG & Sync):** knowledge_base.md and the latest web search results ALWAYS override your internal training memory. For prices and time-sensitive facts, use only the provided snippets and knowledge_base; never rely on model weights alone.

""" + knowledge_base[:8000] + "\n\n---\n\n"
    stale_warning = ""
    if kb_stale_for_price:
        stale_warning = "\n**STRICT UPDATE:** The user asked for a price and the knowledge_base date is old or missing. You MUST perform or use only a live search and verify against current date (March 7, 2026). Do not use knowledge_base or internal memory for the price.\n"
    manifesto_block = ""
    if AI_CONSTITUTION or PROFESSIONAL_CHECKLIST:
        manifesto_block = "\n\n**Self-Audit (mandatory):** Before outputting your final answer, you MUST pass the Professional Checklist. If your response would fail (e.g. uses # headers or ungrounded data), correct it before sending.\n\n" + (AI_CONSTITUTION or "") + "\n" + (PROFESSIONAL_CHECKLIST or "") + "\n---\n\n"
    return (
        (expertise + "\n\n---\n\n") if expertise else ""
    ) + manifesto_block + rag_block + vector_rag_block + research_block + kb_block + """You are the Core AI Reasoning Agent. Follow this cognitive style in every response.
""" + date_note + stale_warning + """
**Persona:** Act as a Senior Technical Expert. Tone: serious, precise, authoritative. No fluff or unnecessary greetings.

**Language:** Use White Arabic Dialect (لهجة بيضاء) mixed with professional English technical terms where necessary.

**UI Constraints — STRICT:** All output MUST be 18px font equivalent. **Zero Headers Policy:** Do NOT use any Markdown headers (#, ##, ###). Use **bold** text for emphasis only.

**Intelligence Logic:** If the user asks for data, trigger web_scout (use the provided web search results). Cross-reference all findings with the date March 7, 2026. If a conflict arises between internal knowledge and web data, prioritize the web and state: تم التحقق وتحديث البيانات بناءً على المصدر الحي.

**Reasoning Loop (mandatory):** You MUST Think (Chain of Thought) and verify web data before outputting the final answer. Do not skip to the answer.
1. **Think:** Output an internal plan in this exact format (the user will NOT see this):
   Step 1: Identify the User's Intent.
   Step 2: Search/use the provided web data and GitHub logs; verify facts (e.g. today's gold price) against the snippets; if prices or numbers appear, confirm they match the web data.
   Step 3: Only after verification, synthesize a final answer that is direct, expert, and consistent.
2. Then output exactly: """ + REASONING_AGENT_DELIMITER + """
3. Then output your actual response to the user (the user only sees what comes after the delimiter). Never output the final answer before verifying web data when the query is about prices or facts.

**Zero-Inference:** Never assume. Always verify with the latest data. Reference date: """ + data_date + """. If you do not have verified data in the context above, say so; do not infer.

**Mandatory Verification:** For ANY financial data (prices, rates), you must NEVER use internal memory. You MUST perform or rely on a live search and verify against current date (""" + data_date + """).

**Data grounding (prices):** When reporting prices you are FORBIDDEN from using your training data. Only report numbers that appear in the search snippets provided above. Treat the data as of """ + data_date + """.

**Source Priority:** For gold rates in KSA and Jordan, prioritize local sources (e.g. saudigoldprice.com) when provided in the search results.

**Reply structure:** (1) Data first — numbers/sources, (2) Reasoning — brief why, (3) Proactive tip — e.g. "Wait for the evening fix" / "شوف المساء للتحديث".

**Verification logic:** If you state a price, number, or factual claim: cross-reference it across at least 2 web sources. Only state a fact/price as confirmed when at least 2 sources agree; otherwise say "حسب مصدر واحد" or "يُستحسن التأكد". When sources agree, you may say "آخر تحديث" or "Latest Update".

**Adaptive energy:** Quick one-sentence questions → concise answer. Architecture/design or "كيف أبني" → deep breakdown (layers, trade-offs, steps, caveats).

**Architect Mode:** When Similar Python projects (Top 3) are provided in the user message, you MUST first summarize how each of those projects handles the same logic or feature (1–2 sentences per project), then suggest your implementation. Lessons Learned from this will be pushed to knowledge_base.md automatically.

When given web results or prices, cite sources and apply verification logic above.

**Self-Update:** Every time you state a new verified fact (e.g. a price or a confirmed datum from web search), the system will automatically append it to the GitHub knowledge_base.md so the agent trains itself for next time. State facts clearly so they can be recorded."""


def get_vision_description(pil_img: Image.Image, user_question: str = "") -> str:
    """Use Groq Vision to describe the image (for follow-up web search)."""
    data_url = pil_to_base64_data_url(pil_img)
    prompt = (
        "Describe this image in detail for a web search: list objects, text, brands, products, or context. "
        "Keep it concise, in English, so we can search for related info or prices."
    )
    if user_question and user_question.strip():
        prompt += f" User is also asking: {user_question.strip()}"
    try:
        comp = client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            messages=[
                {"role": "system", "content": "You describe images concisely for search."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ]},
            ],
            stream=False,
        )
        return (comp.choices[0].message.content or "").strip()
    except Exception:
        return ""


# --- Live price sniper (قنص السعر اللحظي) ---
LIVE_PRICE_FAILED_MSG = "تعذر جلب السعر اللحظي، حاول مرة أخرى."


def fetch_live_gold_from_source() -> str:
    """قنص سعر الذهب مباشرة من المصدر (saudigoldprice.com) مع fallback لـ DDGS. يُحدّث الذاكرة عند النجاح."""
    if AdvancedCoreSearch is None:
        return ""
    try:
        acs = AdvancedCoreSearch()
        data = acs.fetch_live_gold()
        if data and data.strip():
            acs.sync_to_memory(data)
            return data
    except Exception:
        pass
    return ""


def get_live_price(item_name: str) -> str:
    """وظيفة قنص الأسعار الحية من الويب — سعر عالمي (وأردن إن وُجد)."""
    if not item_name or not item_name.strip() or DDGS is None:
        return LIVE_PRICE_FAILED_MSG
    raw = item_name.strip()
    for w in ["كم سعر", "سعر", "بكم", "كم واصل", "اليوم", "؟", "?"]:
        raw = raw.replace(w, " ").strip()
    search_term = raw if raw else item_name.strip()
    # أولوية السعر العالمي ثم المحلي
    queries = [
        f"{search_term} price today world",
        f"سعر {search_term} اليوم عالمي",
        f"{search_term} price USD",
        f"سعر {search_term} اليوم",
    ]
    try:
        with DDGS() as ddgs:
            for query in queries:
                # محاولة أولى مع timelimit يوم
                results = list(ddgs.text(query, max_results=6, timelimit="d"))
                if not results:
                    results = list(ddgs.text(query, max_results=6))
                if results:
                    context = ""
                    for r in results:
                        href = r.get("href") or r.get("link") or ""
                        body = r.get("body") or r.get("snippet") or ""
                        context += f"المصدر: {href}\nالمعلومة: {body}\n---\n"
                    return context.strip()
        return LIVE_PRICE_FAILED_MSG
    except Exception:
        return LIVE_PRICE_FAILED_MSG


LIVE_PRICE_KEYWORDS = ["سعر", "بكم", "كم واصل"]


def needs_live_price_prompt(query: str) -> bool:
    """True if the user is asking for a live price (سعر، بكم، كم واصل)."""
    if not query or not query.strip():
        return False
    return any(word in query for word in LIVE_PRICE_KEYWORDS)


# --- Real-time Price Radar ---
PRICE_RADAR_KEYWORDS = ["سعر", "أسعار", "price", "prices", "كم", "ذهب", "gold", "دولار", "دينار", "ريال"]


def is_explicit_update_command(query: str) -> bool:
    """True if the user explicitly asked to update or check (e.g. 'Update Gold', 'Check Help Me Pro'). No background scans unless this is True."""
    if not query or not query.strip():
        return False
    q = query.strip().lower()
    triggers = [
        "update gold", "تحديث الذهب", "تحديث سعر الذهب", "check gold", "تحقق من الذهب",
        "check help me pro", "تحقق من help me pro", "update help me pro", "تحديث help me pro",
        "جلب الذهب", "fetch gold", "refresh gold", "تحديث جيت هاب", "update github",
    ]
    return any(t in q for t in triggers)


def needs_financial_analysis(query: str) -> bool:
    """True if the user explicitly requests Financial Analysis (charts/visualization). Keeps UI lightweight; load heavy data only then."""
    if not query or not query.strip():
        return False
    q = query.strip().lower()
    return any(x in q for x in ["financial analysis", "تحليل مالي", "تحليل مالى", "price chart", "رسم بياني", "chart"])


def is_fix_or_feature_request(query: str) -> bool:
    """True if the user is asking to fix a bug or add a feature (triggers direct file edit with backup + GitHub log)."""
    if not query or not query.strip():
        return False
    q = query.strip().lower()
    triggers = [
        "أصلح", "عدّل", "عديل", "edit", "fix", "fix the", "أضف ميزة", "add feature",
        "عدّل الملف", "edit file", "edit the file", "تعديل الملف", "عديل الملف",
        "اصلح الخطأ", "fix the bug", "fix bug", "عدّل الكود", "edit code", "غيّر",
    ]
    return any(t in q for t in triggers)


def try_auto_fix_and_notify(user_input: str, assistant_response: str) -> tuple:
    """
    Auto-Fix Protocol: if user asked for a fix/feature, use Groq to produce file path + content,
    then backup, edit, push Change Log to GitHub. Returns (edited: bool, message: str) for UI (18px).
    """
    if not is_fix_or_feature_request(user_input) or not assistant_response or not assistant_response.strip():
        return False, ""
    try:
        files = list_editable_files()[:50]
        if not files:
            return False, ""
        prompt = (
            f"User request: {user_input[:1500]}\n\nAssistant reply: {assistant_response[:2000]}\n\n"
            "Editable project files (relative path): " + ", ".join(files[:30]) + "\n\n"
            "Output a single file edit to fulfill the request. Use 18px font and Zero Markdown headers (#) in any UI-related code. "
            "Format exactly:\nFILE_PATH: <relative path e.g. app.py or core/ui_theme.py>\nCHANGE_SUMMARY: <one line>\nCONTENT:\n<full new file content>\n"
            "If no edit should be made, output only: NONE"
        )
        try:
            from core.groq_client import get_reasoning_model
            edit_model = get_reasoning_model()
        except Exception:
            edit_model = "llama-3.1-8b-instant"
        comp = client.chat.completions.create(
            model=edit_model,
            messages=[
                {"role": "system", "content": "You output a file path, one-line change summary, and full file content for a direct edit. No # headers in UI code; 18px standard."},
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )
        text = (comp.choices[0].message.content or "").strip()
        if not text or text.upper() == "NONE":
            return False, ""
        path_match = re.search(r"FILE_PATH:\s*(\S.+?)(?:\n|$)", text, re.IGNORECASE)
        summary_match = re.search(r"CHANGE_SUMMARY:\s*(.+?)(?=\nCONTENT:|\nFILE_PATH:|\Z)", text, re.DOTALL | re.IGNORECASE)
        content_match = re.search(r"CONTENT:\s*\n([\s\S]+)", text, re.IGNORECASE)
        path = path_match.group(1).strip() if path_match else None
        summary = (summary_match.group(1).strip()[:500] if summary_match else "Direct edit")[:500]
        content = content_match.group(1).strip() if content_match else None
        if not path or not content:
            return False, ""
        ok, msg = apply_direct_edit(path, content, summary)
        return ok, msg
    except Exception:
        return False, ""


def needs_price_radar(query: str) -> bool:
    """True if the user is asking for a price (gold, product, etc.)."""
    if not query or not query.strip():
        return False
    q = query.strip().lower()
    return any(kw in q for kw in PRICE_RADAR_KEYWORDS)


def price_radar_search(query: str, max_results: int = 10) -> tuple:
    """
    Fetch search results from the last 24 hours for price queries (timelimit=d).
    Returns:
        (raw_text: str, rows: list of {title, href, body}) for Gemini Search Protocol and price parsing.
    """
    if not query or not query.strip() or DDGS is None:
        return "", []
    try:
        with DDGS() as ddgs:
            # timelimit="d" = past day (24 hours)
            results = list(ddgs.text(
                query.strip(),
                max_results=max_results,
                timelimit="d",
            ))
        if not results:
            return "", []
        rows = []
        lines = []
        for r in results:
            href = r.get("href") or r.get("link") or ""
            body = r.get("body") or r.get("snippet") or ""
            title = r.get("title") or body[:80] or "—"
            rows.append({"title": title, "href": href, "body": body})
            lines.append(f"Source: {href}\nSnippet: {body}")
        return "\n\n".join(lines), rows
    except Exception:
        return "", []


def parse_prices_from_snippets(rows: list) -> list:
    """Extract numerical price-like values from snippets. Returns list of {value, text, href, snippet}."""
    found = []
    # Match numbers with optional commas/dots, optional currency (USD, JOD, $, etc.)
    price_pattern = re.compile(
        r"(?:USD|JOD|\$|د\.ك|دينار|ريال|جنيه|\$)\s*[\d,.]+\s*[\d,.]*|"
        r"[\d,.]+\s*(?:USD|JOD|\$|د\.ك|دينار|ريال|جنيه|per ounce|/oz|/gram)|"
        r"[\d,]+\.[\d]{2}(?:\s*(?:USD|JOD|\$))?|"
        r"[\d,]+(?:\.[\d]+)?(?=\s*(?:per|/|ounce|gram|oz|g\b))",
        re.IGNORECASE,
    )
    for r in rows:
        body = (r.get("body") or r.get("title") or "")
        href = r.get("href") or ""
        for m in price_pattern.finditer(body):
            text = m.group(0).strip()
            # Try to get a single float
            num_str = re.sub(r"[^\d.]", "", text.replace(",", ""))
            try:
                value = float(num_str) if num_str else None
                if value is not None and 0 < value < 1e9:
                    found.append({"value": value, "text": text, "href": href, "snippet": body[:200]})
            except ValueError:
                pass
    return found


def get_price_analysis_from_model(query: str, search_raw: str, price_findings: list) -> dict:
    """
    Use Groq to compare sources. STRICT: only output a price if at least 2 sources agree.
    Gold sanity: SAR/local ~400-700, USD/oz 2000+; reject implausible values (e.g. $235 for gold).
    """
    prompt = (
        f"User asked for the price of: {query}\n\n"
        "Search results (must be dated March 7, 2026 or today):\n" + search_raw + "\n\n"
    )
    if price_findings:
        prompt += "Parsed price-like values from snippets:\n"
        for i, p in enumerate(price_findings[:8], 1):
            prompt += f"  {i}. {p.get('text', '')} (source: {p.get('href', '')})\n"
    prompt += (
        "\nRULES: (1) Only output CURRENT_PRICE if at least TWO different sources show the same or very close value. "
        "(2) If only one source or sources disagree, set CURRENT_PRICE to empty and in REASONING say 'يُستحسن التأكد من مصدر ثانٍ'. "
        "(3) For gold: SAR/ريال per gram is typically 400-700; USD per ounce is 2000+. Reject clearly wrong numbers (e.g. $235 for gold). "
        "Reply in this exact format (one per line):\n"
        "CURRENT_PRICE: <one number and currency ONLY if 2+ sources agree; else leave empty>\n"
        "BEST_SOURCE: <full URL>\n"
        "REASONING: <1-2 sentences in White Arabic Dialect (لهجة بيضاء)>\n"
    )
    try:
        comp = client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            messages=[
                {"role": "system", "content": "You compare price sources. Output CURRENT_PRICE only when at least 2 sources agree. Never guess; reject implausible gold prices (e.g. $235). Output CURRENT_PRICE, BEST_SOURCE, REASONING."},
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )
        text = (comp.choices[0].message.content or "").strip()
        out = {"current_price": "", "best_source": "", "reasoning": "", "raw": text}
        for line in text.split("\n"):
            line = line.strip()
            if line.upper().startswith("CURRENT_PRICE:"):
                out["current_price"] = line.split(":", 1)[-1].strip()
            elif line.upper().startswith("BEST_SOURCE:"):
                out["best_source"] = line.split(":", 1)[-1].strip()
            elif line.upper().startswith("REASONING:"):
                out["reasoning"] = line.split(":", 1)[-1].strip()
        return out
    except Exception:
        return {"current_price": "", "best_source": "", "reasoning": "", "raw": ""}


def render_price_card(current_price: str, source_link: str, last_updated: str):
    """Render a clean Price Card in the chat (Streamlit markdown + link)."""
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid #333;
            border-radius: 12px;
            padding: 20px;
            margin: 12px 0;
        ">
            <div style="font-size: 0.85rem; color: #888;">Current Price</div>
            <div style="font-size: 1.8rem; font-weight: 700; color: #4ade80;">{current_price or "—"}</div>
            <div style="margin-top: 12px; font-size: 0.9rem;"><a href="{source_link or '#'}" target="_blank" style="color: #60a5fa;">{source_link or "—"}</a></div>
            <div style="margin-top: 8px; font-size: 0.75rem; color: #666;">Last updated: {last_updated}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Base64 logo/icon for injected index.html so the logo never appears broken
_LOGO_BASE64_URI: Optional[str] = None


def _get_logo_base64_uri() -> str:
    """Return Base64 data URI for CoreAI.ico or logo; cached."""
    global _LOGO_BASE64_URI
    if _LOGO_BASE64_URI is None:
        _LOGO_BASE64_URI = get_logo_data_uri(ROOT) or ""
    return _LOGO_BASE64_URI


def get_index_html_for_component() -> str:
    """Load index.html (path relative to app dir for Linux/cloud) and replace logo/icon with Base64. Full blueprint including physics and JS."""
    index_path = ROOT / "index.html"
    if not index_path.is_file():
        return ""
    try:
        html = index_path.read_text(encoding="utf-8")
    except Exception:
        return ""
    logo_uri = _get_logo_base64_uri()
    if logo_uri:
        html = html.replace('src="logo.png"', f'src="{logo_uri}"')
        html = html.replace("src='logo.png'", f"src='{logo_uri}'")
        html = html.replace('href="CoreAI.ico"', f'href="{logo_uri}"')
        html = html.replace("href='CoreAI.ico'", f"href='{logo_uri}'")
    return html


def load_background() -> None:
    """Inject blueprint CSS only (physics comes from full index.html component)."""
    st.markdown(get_streamlit_dark_css(UI_FONT_SIZE_PX), unsafe_allow_html=True)


def load_sidebar() -> None:
    """Render sidebar: logo, CORE AI, New Chat, Navigation, History, Settings, status, footer. 18px, no #."""
    logo_uri = get_logo_data_uri(ROOT)
    with st.sidebar:
        st.markdown('<div class="sidebar-header" style="display:flex;align-items:center;gap:8px;margin-bottom:24px;">', unsafe_allow_html=True)
        if logo_uri:
            st.markdown(f'<img src="{logo_uri}" alt="CORE AI" style="height:36px;width:36px;object-fit:contain;border-radius:6px;">', unsafe_allow_html=True)
        st.markdown('<span style="font-weight:700;font-size:1.2rem;">CORE AI</span></div>', unsafe_allow_html=True)
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.history = []
            st.rerun()
        st.markdown('<div style="font-size:0.75rem;text-transform:uppercase;color:var(--text-secondary);margin:24px 0 12px 0;font-weight:600;">Navigation</div>', unsafe_allow_html=True)
        st.markdown('<div style="display:flex;align-items:center;gap:12px;padding:8px 12px;border-radius:6px;background:#2d2e2e;font-size:0.9rem;"><i class="fas fa-home"></i> Home</div>', unsafe_allow_html=True)
        st.markdown('<div style="display:flex;align-items:center;gap:12px;padding:8px 12px;border-radius:6px;font-size:0.9rem;color:var(--text-secondary);"><i class="fas fa-layer-group"></i> Library</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.75rem;text-transform:uppercase;color:var(--text-secondary);margin:24px 0 12px 0;font-weight:600;">History</div>', unsafe_allow_html=True)
        st.caption("Threads will appear here")
        st.markdown('<div style="font-size:0.75rem;text-transform:uppercase;color:var(--text-secondary);margin:24px 0 12px 0;font-weight:600;">Settings</div>', unsafe_allow_html=True)
        st.markdown('<div style="display:flex;align-items:center;gap:12px;padding:8px 12px;border-radius:6px;font-size:0.9rem;color:var(--text-secondary);"><i class="fas fa-adjust"></i> Switch Theme</div>', unsafe_allow_html=True)
        st.divider()
        if not st.session_state.get("github_connection_ok", True):
            st.error("Connection Error")
        fw = st.session_state.get("framework_init") or {}
        if fw.get("groq_ok"):
            st.success("Groq ✅")
        else:
            st.caption("Groq: set GROQ_API_KEY in .env")
        if fw.get("github_ok") and st.session_state.get("github_connection_ok", True):
            st.success("GitHub Sync ✅")
        elif st.session_state.get("github_connection_ok", True):
            st.caption("GitHub: set GITHUB_TOKEN & GITHUB_REPO in .env")
        if fw.get("search_ok"):
            st.success("Web Search ✅")
        else:
            st.caption("Search: pip install duckduckgo-search")
        if fw.get("neural_connection_established") or fw.get("gemini_ok"):
            st.markdown('<p style="font-size:18px;font-weight:700;color:#10b981;">Neural Connection Established</p>', unsafe_allow_html=True)
        else:
            st.caption("Gemini: set GEMINI_API_KEY in .env")
        all_ok = (
            fw.get("groq_ok")
            and fw.get("github_ok")
            and st.session_state.get("github_connection_ok", True)
            and (fw.get("gemini_ok") or fw.get("neural_connection_established"))
            and fw.get("search_ok")
        )
        if all_ok:
            st.markdown('<p style="font-size:14px;font-weight:600;color:#10b981;">جميع الاتصالات نشطة</p>', unsafe_allow_html=True)
        if fw.get("groq_ok"):
            st.markdown('<p style="font-size:18px;margin:0;color:#10b981;">تم تثبيت المكتبات اللازمة وتفعيل محرك CORE AI بنجاح</p>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.75rem;text-transform:uppercase;color:var(--text-secondary);margin:24px 0 12px 0;font-weight:600;">System Status</div>', unsafe_allow_html=True)
        try:
            st.metric("CPU", f"{psutil.cpu_percent()}%")
            st.metric("RAM", f"{psutil.virtual_memory().percent}%")
        except Exception:
            st.caption("System metrics unavailable")
        st.markdown('<p style="font-size:0.7rem;color:var(--text-secondary);margin-top:auto;">All rights reserved to CORE AI</p>', unsafe_allow_html=True)


def load_chat_interface() -> tuple:
    """Inject full index.html (physics + JS) via st.components.v1.html, then chat area and input linked to backend. Returns (chat_holder, user_input, pending_image)."""
    from streamlit.components.v1 import html as components_html
    full_html = get_index_html_for_component()
    if full_html:
        components_html(full_html, height=900)
    else:
        st.warning("index.html not found; using fallback layout.")
    st.markdown('<p style="font-size:18px;margin:12px 0 4px 0;"><strong>Conversation — CORE AI</strong></p>', unsafe_allow_html=True)
    chat_holder = st.container()
    pasted_img = None
    with st.popover("➕ Add photos and more"):
        st.markdown("<strong>Add photos</strong>")
        if paste_image_button is not None:
            pasted_img = paste_image_button(label="📷 Add photos", background_color="#202222", errors="ignore")
        else:
            st.caption("📷 Add photos")
        st.caption("Web search runs automatically when you ask.")
    user_input = st.chat_input("Type your message here (sends to CORE AI / Gemini backend)...")
    user_input = user_input or st.session_state.pop("pending_prompt", None)
    if "pending_image" not in st.session_state:
        st.session_state.pending_image = None
    if pasted_img and getattr(pasted_img, "image_data", None) is not None:
        st.session_state.pending_image = pasted_img.image_data
    pending_image = st.session_state.pending_image
    if pending_image is not None:
        st.image(pending_image, caption="صورة جاهزة للتحليل — اكتب في Ask anything ثم أرسل", width=250)
    return chat_holder, user_input, pending_image


if "history" not in st.session_state:
    st.session_state.history = []
if "framework_init" not in st.session_state:
    try:
        st.session_state.framework_init = init_core_ai()
    except Exception:
        st.session_state.framework_init = {}
if "github_connection_ok" not in st.session_state:
    try:
        ok, err = test_github_connection()
        st.session_state.github_connection_ok = ok
        st.session_state.github_connection_error = err or "Connection failed"
    except Exception as e:
        st.session_state.github_connection_ok = False
        st.session_state.github_connection_error = str(e)
if st.session_state.get("github_connection_ok") and not st.session_state.get("github_init_pushed"):
    try:
        if update_agent_knowledge("Core AI Memory Initialized"):
            st.session_state.github_init_pushed = True
    except Exception:
        pass
if st.session_state.get("github_connection_ok") and not st.session_state.get("ui_v3_pushed"):
    try:
        if update_agent_knowledge(
            "UI Version 3.0: Blueprint HTML/CSS applied. --bg-color #191a1a, glassmorphism, sidebar 260px, "
            "search-container with controls (Microphone, Image Gen, Control computer), hero glow, floating icons background. "
            "18px font, Zero Headers. Logo: logo.jpg."
        ):
            st.session_state.ui_v3_pushed = True
    except Exception:
        pass
if "system_config" not in st.session_state:
    try:
        _kb, _config = load_memory()
        st.session_state.system_config = _config
        st.session_state.initial_kb = _kb
    except Exception:
        st.session_state.system_config = {"tone": "senior_technical_expert_white_arabic", "font_size": "18px", "web_search_priority": True}
        st.session_state.initial_kb = ""
if "github_rag_text" not in st.session_state:
    st.session_state.github_rag_text = ""

# Blueprint: index.html layout order — background, sidebar, main (header, logo, hero, search, chat container)
load_background()
load_sidebar()
chat_holder, user_input, pending_image = load_chat_interface()

with chat_holder:
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Send to Groq — Vision, web search, Gemini expertise, Top 3 table
if user_input:
    # Lesson Learned: save gold-price fact-check failure to knowledge_base.md once per process
    if not _LESSON_GOLD_FAILURE_PUSHED:
        try:
            update_agent_knowledge(LESSON_LEARNED_GOLD)
            _LESSON_GOLD_FAILURE_PUSHED = True
        except Exception:
            pass
    # Self-Correction: if user corrects the agent, save as Hard Rule to GitHub for future
    if st.session_state.history and st.session_state.history[-1].get("role") == "assistant" and is_user_correction(user_input):
        try:
            save_hard_rule_to_github(user_input)
        except Exception:
            pass
    # Self-Correction: if user provides a newer price, update knowledge_base.md and PUSH to GitHub immediately
    try_apply_user_price_correction(user_input)
    st.session_state.history.append({"role": "user", "content": user_input})
    with chat_holder:
        with st.chat_message("user"):
            st.markdown(user_input)
            if pending_image is not None:
                st.image(pending_image, use_container_width=True)
        with st.chat_message("assistant"):
            resp = ""
            area = st.empty()
            search_rows = []
            try:
                # System: Reasoning Agent + current date awareness
                expertise = load_gemini_expertise()
                current_date = get_current_date_context()
                # Memory First: sync_knowledge() pulls latest facts from GitHub knowledge_base.md before any reasoning
                try:
                    kb_content, kb_date = sync_knowledge()
                except Exception:
                    kb_content, kb_date = "", None
                # Pull last 10 experience files from GitHub before every response (Gemini-style memory)
                try:
                    st.session_state.github_rag_text = pull_github_memory(max_files=10) or ""
                except Exception:
                    st.session_state.github_rag_text = st.session_state.get("github_rag_text", "")
                github_rag_text = st.session_state.get("github_rag_text", "")
                # Strict update: for price queries, if KB date is old we must use fresh web data only
                kb_is_stale_for_price = (
                    (needs_live_price_prompt(user_input) or needs_price_radar(user_input))
                    and (kb_date is None or kb_date < current_date)
                )
                # RAG: check local vector DB for previous projects / Help Me Pro context before answering
                if "rag_loaded" not in st.session_state:
                    try:
                        ensure_rag_context_loaded()
                        st.session_state.rag_loaded = True
                    except Exception:
                        st.session_state.rag_loaded = True
                rag_context = ""
                research_context = ""
                try:
                    rag_context = query_vector_db(user_input, k=5) or ""
                    # UI Resource Management: load Alpha Vantage / data viz only when user requests "Financial Analysis"
                    if needs_financial_analysis(user_input):
                        research_context = research_for_query(user_input) or ""
                except Exception:
                    pass
                system_content = build_reasoning_agent_system(
                    expertise, current_date, github_rag_text,
                    knowledge_base=kb_content,
                    kb_stale_for_price=kb_is_stale_for_price,
                    rag_context=rag_context,
                    research_context=research_context,
                )
                injected_web_raw = ""  # for self-correction when we have web data
                architect_projects_used = []  # Architect Mode: push Lessons Learned to KB after code response

                # 1. Image path: Core Vision analysis + describe + web search
                if pending_image is not None:
                    with st.spinner("🖼️ Describing image with Vision..."):
                        img_description = get_vision_description(pending_image, user_input)
                    with st.spinner("🔬 Core Vision — تحليل بصري (دقة، إضاءة، إمكانية 3D)..."):
                        vision_analysis = run_core_vision_analysis(pending_image, user_input)
                    core_vision_report = (vision_analysis.get("report") or "").strip()
                    augmented_prompt = (
                        f"User asked: {user_input}\n\n"
                        "[Vision description of the image]: " + (img_description or "—") + "\n\n"
                    )
                    if core_vision_report:
                        augmented_prompt += "[Core Vision — Visual analysis (resolution, lighting, 3D-depth potential)]:\n" + core_vision_report[:3000] + "\n\n"
                        area.markdown(
                            "<p style='font-size: 18px; margin: 0;'><strong>Core Vision — التقرير البصري</strong></p>",
                            unsafe_allow_html=True,
                        )
                        area.markdown(sanitize_response_headers(core_vision_report))
                    with st.spinner("🔍 Searching web for related info or prices..."):
                        web_data, search_rows = web_search_tool(
                            (img_description + " " + user_input).strip(), max_results=6
                        )
                    st.session_state.vision_analysis = vision_analysis
                    if web_data:
                        injected_web_raw, search_rows = apply_gemini_search_protocol(web_data, search_rows, current_date, user_input)
                        if not injected_web_raw:
                            injected_web_raw = web_data
                        augmented_prompt += (
                            f"DATA OVERRIDE: Use the following real-time web data to answer. Do not use your training data for prices. Today: {current_date}\n\n"
                            "Real-time web results (prices highlighted):\n" + highlight_prices_in_text(injected_web_raw) + "\n\n"
                        )
                    augmented_prompt += (
                        "Summarize what is in the image and the web findings in White Arabic Dialect (لهجة بيضاء). "
                        "Mention related info or prices if found. Cross-reference any price or fact across at least 2 of the sources; say 'آخر تحديث' when consistent."
                    )
                elif needs_price_radar(user_input) and not needs_live_price_prompt(user_input):
                    # 2b. Price Radar — Zero-Trust: fresh search; strict filter for March 7 2026; require 2+ sources
                    with st.spinner("📡 Fetching latest prices (last 24 hours)..."):
                        web_data, search_rows = price_radar_search(user_input, max_results=10)
                    if web_data:
                        web_data, search_rows = apply_gemini_search_protocol(web_data, search_rows or [], current_date, user_input)
                    # Only use radar data for display when we have at least 2 date-validated sources
                    if not search_rows or len(search_rows) < 2:
                        strict_raw, strict_rows = price_search_strict(user_input, current_date, min_sources=2)
                        if strict_rows:
                            web_data, search_rows = strict_raw, strict_rows
                    if web_data and "سعر" in user_input and current_date not in kb_content:
                        try:
                            update_agent_knowledge(web_data)
                        except Exception:
                            pass
                    price_findings = parse_prices_from_snippets(search_rows)
                    with st.spinner("🤖 Comparing sources for most accurate average..."):
                        analysis = get_price_analysis_from_model(user_input, web_data, price_findings)
                    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M")
                    render_price_card(
                        analysis.get("current_price") or "—",
                        analysis.get("best_source") or "",
                        last_updated,
                    )
                    reasoning = analysis.get("reasoning") or analysis.get("raw") or ""
                    if reasoning:
                        st.markdown(sanitize_response_headers(reasoning))
                    resp = sanitize_response_headers(f"**{analysis.get('current_price', '—')}**\n\n{reasoning}")
                    st.session_state.history.append({"role": "assistant", "content": resp})
                    if pending_image is not None:
                        st.session_state.pending_image = None
                    # Self-Update: append verified fact to GitHub memory
                    try:
                        entry = f"Query: {user_input}\nPrice: {analysis.get('current_price', '—')}\nSource: {analysis.get('best_source', '')}\nReasoning: {reasoning[:800]}"
                        record_verified_fact(entry, current_date)
                    except Exception:
                        pass
                    # Smart Summarization: extract and append to ## Learned Context - 2026-03-07
                    try:
                        run_smart_summarization_and_notify(user_input, resp)
                    except Exception:
                        pass
                else:
                    # Action Picker: same Search-then-Answer flow for code, facts, general; price uses live/radar
                    action = action_picker(user_input)
                    # 2. Text path: live price sniper (سعر، بكم، كم واصل) or web search
                    if needs_live_price_prompt(user_input):
                        # Only run gold/GitHub update when user explicitly asks (e.g. "Update Gold"); agent stays idle otherwise
                        if is_explicit_update_command(user_input) and get_autonomous_agent and ("ذهب" in user_input or "gold" in user_input.lower()):
                            try:
                                agent = get_autonomous_agent()
                                if agent:
                                    agent.auto_check_and_update("gold")
                            except Exception:
                                pass
                        # High-speed: Groq Llama-3 executes search and analysis immediately on command
                        # قنص من رأس النبع أولاً للذهب ثم بحث صارم بتاريخ March 7 2026 ومراعاة مصدرين
                        price_data = ""
                        search_rows = []
                        if "ذهب" in user_input or "gold" in user_input.lower():
                            with st.spinner("🔍 قنص من المصدر (saudigoldprice.com)..."):
                                direct_gold = fetch_live_gold_from_source()
                            if direct_gold:
                                strict_raw, strict_rows = price_search_strict("gold price سعر الذهب", current_date, min_sources=2)
                                if strict_rows:
                                    search_rows = strict_rows
                                    price_data = direct_gold + "\n---\n" + strict_raw
                                else:
                                    ddgs_fallback = get_live_price(user_input)
                                    price_data = direct_gold + ("\n---\n" + ddgs_fallback if ddgs_fallback != LIVE_PRICE_FAILED_MSG else "")
                                    if not search_rows:
                                        search_rows = [{"body": b.strip(), "title": "", "href": ""} for b in (price_data or "").split("---") if b.strip()]
                            else:
                                strict_raw, strict_rows = price_search_strict(user_input + " gold سعر الذهب", current_date, min_sources=2)
                                if strict_rows:
                                    price_data = strict_raw
                                    search_rows = strict_rows
                                else:
                                    price_data = get_live_price(user_input)
                                    if price_data != LIVE_PRICE_FAILED_MSG and price_data:
                                        search_rows = [{"body": price_data.strip(), "title": "", "href": ""}]
                        else:
                            strict_raw, strict_rows = price_search_strict(user_input, current_date, min_sources=2)
                            if strict_rows:
                                price_data = strict_raw
                                search_rows = strict_rows
                            else:
                                price_data = get_live_price(user_input)
                                if price_data != LIVE_PRICE_FAILED_MSG and price_data:
                                    search_rows = [{"body": price_data.strip(), "title": "", "href": ""}]
                        if price_data == LIVE_PRICE_FAILED_MSG or not price_data:
                            with st.spinner("🔍 بحث احتياطي + بدائل..."):
                                web_data, search_rows = web_search_tool(user_input, max_results=6)
                                if not web_data:
                                    strict_raw, strict_rows = price_search_strict(user_input + " " + current_date, current_date, min_sources=2)
                                    if strict_rows:
                                        web_data, search_rows = strict_raw, strict_rows
                                price_data = web_data if web_data else price_data
                        if not search_rows and price_data and price_data != LIVE_PRICE_FAILED_MSG:
                            search_rows = [{"body": b.strip(), "title": "", "href": ""} for b in (price_data or "").split("---") if b.strip()]
                        # Gemini Search Protocol: only use data with today's date; require 2+ sources for display
                        raw_for_protocol = price_data if price_data and price_data != LIVE_PRICE_FAILED_MSG else ""
                        if raw_for_protocol:
                            raw_for_protocol, search_rows = apply_gemini_search_protocol(raw_for_protocol, search_rows or [], current_date, user_input)
                        injected_web_raw = raw_for_protocol or ""
                        # When price data missing or < 2 sources: do NOT say "No price found"; show last verified with Outdated warning or trend
                        if not injected_web_raw or len(search_rows) < 2:
                            last_verified = get_last_verified_from_kb(kb_content)
                            pivot_prompt = f"""Real-time price could not be verified from at least two sources dated {current_date}.
Do NOT output "No price found" or "لم أجد سعراً". You MUST do one of the following:
(1) If the knowledge base below contains a last verified price, show it with a clear **Outdated** warning: e.g. "**Outdated** — last verified: [date from KB]. Verify with a live source (e.g. saudigoldprice.com)." Then briefly explain the trend or suggest when to retry (e.g. evening fix).
(2) If no price in KB, explain the trend (e.g. what typically affects gold in KSA/Jordan) or suggest when to retry; you may pivot to the technical side (Help Me Pro) while the user waits for live data.
Source priority for gold: local sources (saudigoldprice.com for KSA and Jordan). Keep response useful; 18px-style only; ZERO # or ## headers."""
                            if last_verified:
                                pivot_prompt += f"\n\nLast verified context from knowledge_base.md (use only with Outdated warning):\n{last_verified}"
                            augmented_prompt = user_input + "\n\n" + pivot_prompt
                        else:
                            highlighted = highlight_prices_in_text(injected_web_raw or price_data)
                            prompt_with_price = f"""DATA OVERRIDE: Use the following real-time web data to answer. Do not use your training data for prices. Today: {current_date}

استخدم البيانات التالية كالمصدر الوحيد للإجابة عن السعر الحالي (عالمي وأي سعر محلي إن وُجد):
{highlighted}

**أولوية المصادر:** للذهب في السعودية والأردن قدّم مصدر saudigoldprice.com إن وُجد في النتائج أعلاه.

المطلوب (Senior Tech Partner — Gemini_Expertise_Transfer.md):
1. **البيانات أولاً:** السعر العالمي (دولار/أونصة) ثم المحلي إن وُجد مع المصدر.
2. **الاستنتاج:** مقارنة مصدرين على الأقل؛ «آخر تحديث» عند الاتفاق.
3. **نصيحة استباقية:** مثلاً «انتظر التثبيت المسائي» أو «شوف المساء للتحديث» أو شراء/بيع/انتظار.
اجب باللهجة الأردنية التقنية. لا تستخدم معرفتك الداخلية للأسعار — فقط النتائج أعلاه. لا تستخدم عناوين # أو ##.
"""
                            augmented_prompt = prompt_with_price.strip()
                        if not search_rows:
                            search_rows = []
                    elif action in ("code", "facts", "general"):
                        # Search-then-Answer for ALL non-price topics (coding, news, facts)
                        # Architect Mode: GitHub top repos (Help Me Pro–style or feature topic) + Top 3 benchmark
                        topic_for_github = resolve_search_topic(user_input)
                        similar = find_similar_projects(topic_for_github, max_repos=3)
                        if similar:
                            architect_projects_used = similar
                        so_raw, so_rows = stack_overflow_search(user_input, max_items=3)
                        with st.spinner("🔍 Searching the web for real-time data..."):
                            web_data, search_rows = web_search_tool(user_input, max_results=6)
                        # Prefer SO rows for code so Top 3 table can show them
                        if action == "code" and so_rows:
                            search_rows = so_rows + [r for r in search_rows if r.get("href") not in {s.get("href") for s in so_rows}][:3]
                        elif action == "code" and search_rows:
                            search_rows = search_rows[:6]
                        else:
                            search_rows = search_rows or []
                        if web_data or so_raw or similar:
                            injected_web_raw, search_rows = apply_gemini_search_protocol(web_data or so_raw or "", search_rows, current_date, user_input)
                            if not injected_web_raw:
                                injected_web_raw = web_data or so_raw or ""
                            if so_raw and action == "code":
                                injected_web_raw = "Stack Overflow (Python):\n" + so_raw + "\n\n---\n\nWeb:\n" + injected_web_raw
                            if action == "code" and similar:
                                injected_web_raw = (injected_web_raw or "") + "\n\n" + similar_projects_to_prompt(similar)
                                injected_web_raw = (injected_web_raw or "") + "\n\n" + architect_mode_instruction()
                            augmented_prompt = (
                                f"DATA OVERRIDE: Use the following real-time web data to answer. Do not use your training data for prices. Today: {current_date}\n\n"
                                f"User asked: {user_input}\n\n"
                                "Real-time web results (prices highlighted):\n" + highlight_prices_in_text(injected_web_raw) + "\n\n"
                                "Analyze and summarize in White Arabic Dialect (لهجة بيضاء) with English technical terms. Cite sources. "
                                "For any price or fact, cross-reference at least 2 of the sources; say 'آخر تحديث' when they agree. "
                                "Structure: (1) Data first, (2) Reasoning, (3) Proactive tip (e.g. Wait for the evening fix). "
                                "If there are multiple options, highlight the best ones."
                            )
                        else:
                            augmented_prompt = user_input
                            injected_web_raw = so_raw if action == "code" and so_raw else ""
                            if action == "code":
                                similar = find_similar_projects(topic_for_github, max_repos=3)
                                if similar:
                                    architect_projects_used = similar
                                    injected_web_raw = (injected_web_raw or "") + ("\n\n" if injected_web_raw else "") + similar_projects_to_prompt(similar) + "\n\n" + architect_mode_instruction()
                                    augmented_prompt = user_input + "\n\n" + injected_web_raw
                    else:
                        augmented_prompt = user_input
                        search_rows = []
                        injected_web_raw = ""

                    # إذا طلب سعر والذاكرة لا تحتوي تاريخ اليوم → تم البحث أعلاه؛ نحدّث الذاكرة على GitHub
                    if "سعر" in user_input and current_date not in kb_content and injected_web_raw:
                        try:
                            update_agent_knowledge(injected_web_raw)
                        except Exception:
                            pass

                    # When we have real web data: extract numbers first, then strict fact-checking prompt
                    verified_web_prices = []
                    if injected_web_raw and injected_web_raw.strip():
                        verified_web_prices = get_verified_prices_from_search(injected_web_raw)
                        system_content = get_core_logic_response(
                            user_input, injected_web_raw, github_rag_text, kb_content, verified_web_prices,
                            rag_context=rag_context, research_context=research_context,
                        )

                    # 3. Call Groq (with image in message if present)
                    with st.spinner("🤖 Analyzing and summarizing with AI..."):
                        api_messages = (
                        [{"role": "system", "content": system_content}]
                        + [{"role": m["role"], "content": m["content"]} for m in st.session_state.history]
                    )
                    api_messages[-1] = {"role": "user", "content": augmented_prompt}
                    if pending_image is not None:
                        data_url = pil_to_base64_data_url(pending_image)
                        api_messages[-1] = {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": augmented_prompt},
                                {"type": "image_url", "image_url": {"url": data_url}},
                            ],
                        }
                    stream = client.chat.completions.create(
                        model=GROQ_VISION_MODEL,
                        messages=api_messages,
                        stream=True,
                    )
                    full_content = ""
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_content += chunk.choices[0].delta.content
                            if REASONING_AGENT_DELIMITER in full_content:
                                resp = full_content.split(REASONING_AGENT_DELIMITER, 1)[-1].strip()
                                area.markdown(resp + "▌")
                            else:
                                area.markdown("*...جاري التخطيط...*")
                    resp = full_content.split(REASONING_AGENT_DELIMITER, 1)[-1].strip() if REASONING_AGENT_DELIMITER in full_content else full_content.strip()

                    # Self-correction: if plan contradicts web data, re-generate with Data Discrepancy Alert + web value only
                    if injected_web_raw and REASONING_AGENT_DELIMITER in full_content:
                        plan_part = full_content.split(REASONING_AGENT_DELIMITER, 1)[0]
                        if plan_contradicts_web_data(plan_part, injected_web_raw):
                            with st.spinner("⚠️ تصحيح: تنبيه تعارض بيانات — استخدام قيمة الويب فقط..."):
                                try:
                                    corr_prices = get_verified_prices_from_search(injected_web_raw)
                                    corr_prices_str = ", ".join(f"${p}" for p in sorted(set(corr_prices))[:15]) if corr_prices else "see snippets"
                                    correction_prompt = (
                                        f"Data Discrepancy detected. VERIFIED NUMBERS FROM WEB: {corr_prices_str}. "
                                        f"Re-answer using ONLY these values. Start your response with: **Data Discrepancy Alert:** internal vs web — using web value: $[value]. "
                                        f"Today: {current_date}\n\n{highlight_prices_in_text(injected_web_raw)}\n\nUser asked: {user_input}"
                                    )
                                    comp = client.chat.completions.create(
                                        model=GROQ_VISION_MODEL,
                                        messages=[
                                            {"role": "system", "content": "You are a Senior Technical Expert. Output ONLY the web numbers. No training data for prices. Use White Arabic Dialect (لهجة بيضاء) with English technical terms. If conflict with internal knowledge, state: تم التحقق وتحديث البيانات بناءً على المصدر الحي. 18px font, no # headers."},
                                            {"role": "user", "content": correction_prompt},
                                        ],
                                        stream=False,
                                    )
                                    resp = (comp.choices[0].message.content or "").strip()
                                    area.markdown(resp)
                                except Exception:
                                    pass

                    # Self-Audit: MUST pass Professional Checklist before displaying; re-process until pass or max retries
                    max_audit_retries = 2
                    for _ in range(max_audit_retries):
                        verified_for_audit = get_verified_prices_from_search(injected_web_raw) if injected_web_raw else None
                        is_price_fact = bool(needs_live_price_prompt(user_input) or needs_price_radar(user_input) or (injected_web_raw and ( "سعر" in user_input or "price" in user_input.lower() )))
                        passed, failures = run_self_audit(
                            resp,
                            verified_web_prices=verified_for_audit,
                            is_price_or_fact_query=is_price_fact,
                        )
                        if passed:
                            break
                        with st.spinner("⚠️ Self-Audit failed — re-processing to meet professional standards..."):
                            try:
                                retry_prompt = get_self_audit_prompt_for_retry(
                                    failures, user_input,
                                    web_context=highlight_prices_in_text(injected_web_raw)[:3000] if injected_web_raw else "",
                                )
                                comp = client.chat.completions.create(
                                    model=GROQ_VISION_MODEL,
                                    messages=[
                                        {"role": "system", "content": "You are Core AI — Senior Technical Expert. Output ONLY the corrected final answer. 18px font, no # or ##. Use only web data for prices. White Arabic Dialect (لهجة بيضاء) with English terms; serious, precise; data first, then reasoning, then tip."},
                                        {"role": "user", "content": retry_prompt},
                                    ],
                                    stream=False,
                                )
                                resp = (comp.choices[0].message.content or "").strip()
                                area.markdown(resp)
                            except Exception:
                                break

                    # Formatting Lock: ZERO headers — sanitize before display
                    resp = sanitize_response_headers(resp)
                    # 4. Append Top 3 table when we have multiple search results
                    if len(search_rows) >= 3:
                        resp += "\n\n" + top3_table_markdown(search_rows)
                    area.markdown(resp)

                    st.session_state.history.append({"role": "assistant", "content": resp})
                    if pending_image is not None:
                        st.session_state.pending_image = None

                    # Architect Mode: push Lessons Learned from Top 3 similar projects to knowledge_base.md
                    if architect_projects_used and resp and resp.strip():
                        try:
                            update_agent_knowledge(lessons_learned_entry(architect_projects_used, user_input))
                        except Exception:
                            pass

                    # Self-Update: every verified fact is appended to GitHub knowledge_base.md
                    if injected_web_raw and resp and resp.strip():
                        try:
                            entry = f"Query: {user_input}\nFact-checked answer (sources from web): {resp[:1500]}"
                            record_verified_fact(entry, current_date)
                        except Exception:
                            pass

                    # Strict Fact-Checking: push verified price; Logic Rule: if > 2% vs baseline → Volatile Market alert + update KB
                    if injected_web_raw and resp and resp.strip():
                        try:
                            verified = get_verified_prices_from_search(injected_web_raw)
                            if verified:
                                is_volatile, alert_msg = check_volatile_market(verified)
                                if is_volatile and alert_msg:
                                    resp = alert_msg + "\n\n" + resp
                                    area.markdown(resp)
                                    st.session_state.history[-1]["content"] = resp
                                prices_str = ", ".join(f"${p}" for p in sorted(set(verified))[:10])
                                push_entry = f"Verified prices from web ({current_date}): {prices_str} | Query: {user_input} | Answer: {resp[:500]}"
                                if is_volatile:
                                    push_entry = f"[Volatile Market — >2% vs baseline] {push_entry}"
                                update_agent_knowledge(push_entry)
                        except Exception:
                            pass
                    # Smart Summarization: extract only code/verified data/user decisions; append to Learned Context; notify
                    try:
                        run_smart_summarization_and_notify(user_input, resp)
                    except Exception:
                        pass
                    # Direct File System Access: if user asked for fix/feature, apply edit with .bak backup and push Change Log to GitHub
                    try:
                        edited, file_msg = try_auto_fix_and_notify(user_input, resp)
                        if file_msg:
                            st.markdown(
                                f'<p style="font-size: 18px; margin: 0;">{file_msg}</p>',
                                unsafe_allow_html=True,
                            )
                    except Exception:
                        pass
                    # Core Vision: save Auto-Fix script (with rollback) and push Visual Insights to GitHub
                    try:
                        va = st.session_state.pop("vision_analysis", None)
                        if va and isinstance(va, dict):
                            auto_script = (va.get("auto_fix_script") or "").strip()
                            saved_path = ""
                            if auto_script:
                                ok, _ = apply_direct_edit("core/vision_auto_fix.py", auto_script, "Core Vision Auto-Fix from image analysis")
                                if ok:
                                    saved_path = "core/vision_auto_fix.py"
                            push_visual_insights_to_github(
                                va.get("report") or "",
                                va.get("enhancement_code") or va.get("auto_fix_script") or "",
                                saved_path,
                            )
                    except Exception:
                        pass
            except Exception as e:
                st.error(f"Error: {e}")
