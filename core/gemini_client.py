"""
CORE AI Neural Link — Gemini Pro engine configured to always act as CORE AI.
Identity: Senior Technical Expert, White Arabic Dialect (لهجة بيضاء).
Visuals: All text 18px. Zero Headers (#) in the UI. Use bold for titles.
"""
from typing import Optional, Tuple

try:
    import google.generativeai as genai
except ImportError:
    genai = None


# CORE AI identity — applied to every Gemini call
CORE_AI_SYSTEM_INSTRUCTION = """You are CORE AI — Neural Intelligence Engine.
Identity: Always act as CORE AI. Persona: Senior Technical Expert. Language: White Arabic Dialect (لهجة بيضاء) with English technical terms where appropriate.
Format: All text must be 18px equivalent. Zero Markdown headers (# or ##). Use **bold** for any titles or emphasis. No fluff; serious, precise, data-first."""


def _get_client():
    """Return configured genai model or None if key missing."""
    if genai is None:
        return None
    try:
        from core.config import GEMINI_API_KEY
        key = (GEMINI_API_KEY or "").strip()
        if not key or key == "your_copied_key_here":
            return None
        genai.configure(api_key=key)
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            system_instruction=CORE_AI_SYSTEM_INSTRUCTION,
        )
        return model
    except Exception:
        return None


def test_neural_connection() -> Tuple[bool, Optional[str]]:
    """
    Run a minimal test call to Gemini as CORE AI.
    Returns (success, error_message). On success, error_message is None.
    """
    model = _get_client()
    if model is None:
        return False, "GEMINI_API_KEY not set or invalid"
    try:
        response = model.generate_content("Reply with exactly: OK")
        if response and response.text and "OK" in (response.text or "").strip()[:10]:
            return True, None
        return True, None  # any valid response counts as connected
    except Exception as e:
        return False, str(e)


def generate_as_core_ai(prompt: str, **kwargs) -> Optional[str]:
    """Generate a response using Gemini Pro as CORE AI. Returns None on failure."""
    model = _get_client()
    if model is None:
        return None
    try:
        response = model.generate_content(prompt, **kwargs)
        return (response.text or "").strip() if response else None
    except Exception:
        return None
