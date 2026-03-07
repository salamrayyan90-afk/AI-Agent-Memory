"""
Research module: LangChain-backed data from Alpha Vantage (gold/finance) and official docs (coding).
"""
import os
from typing import Any, Dict, List, Optional

try:
    from core.config import ALPHA_VANTAGE_API_KEY
except ImportError:
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")


def fetch_alpha_vantage_gold() -> Dict[str, Any]:
    """
    Pull gold/finance data from Alpha Vantage (GOLD, XAU, or CURRENCY).
    Returns dict with price, last_updated, or error.
    """
    if not ALPHA_VANTAGE_API_KEY:
        return {"error": "ALPHA_VANTAGE_API_KEY not set", "source": "alpha_vantage"}
    try:
        import requests
        # Alpha Vantage: CURRENCY_EXCHANGE_RATE or GLOBAL_QUOTE for commodities
        url = (
            "https://www.alphavantage.co/query"
            "?function=CURRENCY_EXCHANGE_RATE"
            "&from_currency=XAU&to_currency=USD"
            f"&apikey={ALPHA_VANTAGE_API_KEY}"
        )
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        rate = data.get("Realtime Currency Exchange Rate", {})
        if rate:
            return {
                "from": rate.get("2. From_Currency Name", "Gold"),
                "to": rate.get("4. To_Currency Name", "USD"),
                "price": rate.get("5. Exchange Rate"),
                "last_updated": rate.get("6. Last Refreshed"),
                "source": "alpha_vantage",
            }
        # Fallback: try CRYPTO or GLOBAL_QUOTE if available
        return {"error": "No rate in response", "raw": data, "source": "alpha_vantage"}
    except Exception as e:
        return {"error": str(e), "source": "alpha_vantage"}


def fetch_alpha_vantage_quote(symbol: str = "GOLD") -> Dict[str, Any]:
    """Fetch GLOBAL_QUOTE for a symbol (e.g. GOLD, XAU)."""
    if not ALPHA_VANTAGE_API_KEY:
        return {"error": "ALPHA_VANTAGE_API_KEY not set"}
    try:
        import requests
        url = (
            "https://www.alphavantage.co/query"
            "?function=GLOBAL_QUOTE"
            f"&symbol={symbol}"
            f"&apikey={ALPHA_VANTAGE_API_KEY}"
        )
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        quote = data.get("Global Quote", {})
        if quote:
            return {
                "symbol": symbol,
                "price": quote.get("05. price"),
                "change": quote.get("09. change"),
                "latest_trading_day": quote.get("07. latest trading day"),
                "source": "alpha_vantage",
            }
        return {"error": "No quote", "raw": data}
    except Exception as e:
        return {"error": str(e)}


def research_gold_finance(query: str) -> str:
    """
    Use Alpha Vantage for gold/finance queries. Returns a short context string for the prompt.
    """
    q = (query or "").lower()
    if "gold" not in q and "ذهب" not in q and "xau" not in q and "finance" not in q and "سعر" not in q:
        return ""
    out = fetch_alpha_vantage_gold()
    if out.get("error"):
        quote = fetch_alpha_vantage_quote("GLD")
        if not quote.get("error") and quote.get("price"):
            return f"Alpha Vantage (GLD): {quote.get('price')} USD (latest: {quote.get('latest_trading_day', '')})"
        return ""
    price = out.get("price")
    updated = out.get("last_updated", "")
    return f"Alpha Vantage: {out.get('from', 'Gold')} = {price} {out.get('to', 'USD')} (updated: {updated})"


def fetch_docs_for_coding(query: str, doc_urls: Optional[List[str]] = None) -> str:
    """
    Pull official documentation for coding queries using LangChain document loaders.
    Returns concatenated relevant snippets (or empty if no loader/docs).
    """
    if not query or not query.strip():
        return ""
    q = (query or "").strip().lower()
    if "python" in q or "pip" in q or "langchain" in q or "كود" in q or "code" in q or "api" in q or "doc" in q:
        try:
            from langchain_community.document_loaders import WebBaseLoader
        except Exception:
            return ""
        urls = list(doc_urls or [])
        if not urls:
            urls = [
                "https://python.langchain.com/docs/introduction/",
                "https://docs.python.org/3/",
            ]
        snippets = []
        for url in urls[:3]:
            try:
                loader = WebBaseLoader(url)
                docs = loader.load()
                for d in docs[:2]:
                    if d.page_content and len(d.page_content) > 100:
                        snippets.append(d.page_content[:1500].strip())
            except Exception:
                continue
        if snippets:
            return "\n\n---\n\n".join(snippets[:3])
    return ""


def research_for_query(query: str) -> str:
    """
    Combined Research: Alpha Vantage (gold/finance) + official docs (coding).
    Returns context string to inject into the agent prompt.
    """
    parts = []
    gold_ctx = research_gold_finance(query)
    if gold_ctx:
        parts.append("[Research — Alpha Vantage]\n" + gold_ctx)
    docs_ctx = fetch_docs_for_coding(query)
    if docs_ctx:
        parts.append("[Research — Official docs]\n" + docs_ctx)
    return "\n\n".join(parts) if parts else ""
