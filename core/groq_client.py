"""
Core AI — Groq integration for reasoning.
Uses the latest Llama-3 models for high-speed processing.
"""
import os
from typing import Optional

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from core.config import GROQ_API_KEY, GROQ_TEXT_MODEL, GROQ_VISION_MODEL, GROQ_BASE_URL
except ImportError:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_TEXT_MODEL = "llama-3.1-8b-instant"
    GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
    GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# High-speed reasoning: Llama 3.1 8B (instant) or Llama 3.3 70B (versatile)
REASONING_MODEL = os.getenv("GROQ_REASONING_MODEL", GROQ_TEXT_MODEL)

_client: Optional["Groq"] = None


def get_groq_client() -> Optional["Groq"]:
    """Return the Groq API client for reasoning and chat. Initialized once."""
    global _client
    if _client is not None:
        return _client
    if not Groq or not GROQ_API_KEY:
        return None
    try:
        _client = Groq(api_key=GROQ_API_KEY)
        return _client
    except Exception:
        return None


def get_reasoning_model() -> str:
    """Return the model id used for high-speed reasoning (Llama-3 family)."""
    return REASONING_MODEL


def get_vision_model() -> str:
    """Return the model id used for vision/multimodal."""
    return GROQ_VISION_MODEL
