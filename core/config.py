"""Configuration and environment for Core AI. Load credentials from .env for GroqCloud and GitHub."""
import os
from pathlib import Path
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# GroqCloud (Llama-3), GitHub, Gemini — load from .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
# Vision: llama-3.2-11b-vision-preview was decommissioned; use Llama 4 Scout (vision)
GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_TEXT_MODEL = "llama-3.1-8b-instant"  # fallback text-only

# UI
BACKGROUND_COLOR = "#0e1117"

# Safety: actions that require Approve/Run
FINANCIAL_KEYWORDS = ["دفع", "شراء", "payment", "purchase", "تحويل", "transfer", "سعر", "price"]
OS_LEVEL_KEYWORDS = ["حذف", "delete", "نظام", "system", "تسجيل", "registry", "تثبيت", "install"]
