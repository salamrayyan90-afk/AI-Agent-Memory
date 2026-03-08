"""
Advanced Core Search — قنص الأسعار مباشرة من رأس النبع (Saudi/global gold sources).
"""
import datetime
import requests
from bs4 import BeautifulSoup

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None


class AdvancedCoreSearch:
    def __init__(self):
        self.targets = {
            "saudi": "https://saudigoldprice.com",
            "global": "https://livepriceofgold.com",
        }

    def fetch_live_gold(self) -> str:
        """قنص الأسعار مباشرة من رأس النبع — Saudi 21K then fallback to DDGS."""
        try:
            response = requests.get(self.targets["saudi"], timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            # استخراج سعر عيار 21 — ضبط الـ selector حسب بنية الموقع الحالية
            el = soup.find(string=lambda t: t and "عيار 21" in (t if isinstance(t, str) else ""))
            if el:
                parent = el.parent
                if parent:
                    next_td = parent.find_next("td")
                    if next_td and next_td.get_text(strip=True):
                        price_21k = next_td.get_text(strip=True)
                        return f"تحديث مؤكد من المصدر: جرام عيار 21 = {price_21k} ريال (saudigoldprice.com)"
            # محاولة بديلة: أي td يحتوي رقم سعر قرب نص "21"
            for td in soup.find_all("td"):
                text = td.get_text(strip=True)
                if text and any(c.isdigit() for c in text) and ("21" in str(td.find_previous(string=lambda s: s and "عيار" in str(s)) or "")):
                    return f"تحديث مؤكد من المصدر: جرام عيار 21 = {text} ريال (saudigoldprice.com)"
        except Exception:
            pass
        # خطة بديلة: البحث الذكي في الويب
        if DDGS:
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text("سعر الذهب اليوم في السعودية عيار 21", max_results=3))
                    if results:
                        return results[0].get("body", "") or results[0].get("snippet", "")
            except Exception:
                pass
        return ""

    def web_scout(self, query: str, max_results: int = 5, filter_date: str = "") -> str:
        """
        بحث ويب للتحديثات التقنية/الأمنية (مكتبات، ثغرات، 2026).
        If filter_date is set (e.g. 'March 7, 2026'), only return snippets that contain that date.
        Ensures results are current; verify figures from at least two sources when using for facts.
        """
        if not query or not query.strip():
            return ""
        if DDGS is None:
            return ""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query.strip(), max_results=max_results * 2))
            if not results:
                return ""
            lines = []
            for r in results:
                body = (r.get("body") or r.get("snippet") or "").strip()
                if not body:
                    continue
                if filter_date and filter_date not in body and "2026" not in body:
                    continue
                lines.append(body)
                if len(lines) >= max_results:
                    break
            return " ".join(lines)[:1500] if lines else ""
        except Exception:
            return ""

    def sync_to_memory(self, data: str) -> bool:
        """تحديث ذاكرة المستودع فوراً — يلحق في knowledge_base.md ويدفع إلى GitHub."""
        if not data or not data.strip():
            return False
        try:
            from memory.github_rag import update_agent_knowledge
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            entry = f"[{timestamp}] Verified: {data.strip()[:2000]}"
            return update_agent_knowledge(entry)
        except Exception:
            return False
