"""
Smart Summarization: extract only actionable points from each interaction (no full chat).
Uses Groq Llama-3 to extract: New Code Snippets, Verified Data, User Decisions.
Output is appended to knowledge_base.md under ## Learned Context - 2026-03-07.
"""
from typing import Optional

try:
    from core.groq_client import get_groq_client, get_reasoning_model
except ImportError:
    get_groq_client = lambda: None
    get_reasoning_model = lambda: "llama-3.1-8b-instant"

LEARNED_CONTEXT_DATE = "2026-03-07"  # Strict date for Learned Context section

EXTRACTION_SYSTEM = """You are an extractor. From the given User message and Assistant response, output ONLY the following (if any). Use plain text; no Markdown headers (#). Use **bold** only for labels.

1. **New Code Snippets:** Optimized functions or logic changes (paste only the relevant snippet, not the full chat).
2. **Verified Data:** Confirmed prices (e.g. Gold 545 SAR), tech specs, or numbers that were verified from a source.
3. **User Decisions:** Specific preferences the user mentioned (e.g. preference for 'White Dialect', language, tool choice).

If there is nothing to extract (no code, no verified data, no user preference), output exactly: NONE.
Keep each item concise. One line per bullet. Do not include greetings or filler."""


def extract_learned_context(user_message: str, assistant_response: str) -> Optional[str]:
    """
    Use Groq Llama-3 to extract only: New Code Snippets, Verified Data, User Decisions.
    Returns structured text to append to knowledge_base.md, or None if nothing to save.
    """
    if not user_message and not assistant_response:
        return None
    client = get_groq_client() if callable(get_groq_client) else None
    if not client:
        return None
    prompt = f"User message:\n{user_message.strip()[:3000]}\n\nAssistant response:\n{(assistant_response or '')[:4000]}"
    try:
        resp = client.chat.completions.create(
            model=get_reasoning_model(),
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )
        text = (resp.choices[0].message.content or "").strip()
        if not text or text.upper() == "NONE":
            return None
        return text
    except Exception:
        return None
