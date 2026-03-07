"""
Core AI — تفعيل العقل (Groq) والذاكرة (GitHub) والبحث الحي (DuckDuckGo).
Single entry point: CoreAI (sync/self_update), CoreAI_Engine (web_verify, update_knowledge, generate_response).
جميع الاتصالات بـ GitHub تستخدم core.config (GITHUB_TOKEN, GITHUB_REPO) كمصدر واحد.
"""
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load credentials from .env (GroqCloud + GitHub)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

try:
    from core.config import GITHUB_TOKEN as _GH_TOKEN, GITHUB_REPO as _GH_REPO
except ImportError:
    _GH_TOKEN = os.getenv("GITHUB_TOKEN", "")
    _GH_REPO = os.getenv("GITHUB_REPO", "")

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from github import Github
except ImportError:
    Github = None

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None


class CoreAI:
    """
    تفعيل النظام: العقل (Groq Llama-3) والذاكرة (GitHub knowledge_base.md).
    """

    def __init__(self):
        # تفعيل العقل (Groq)
        api_key = os.getenv("GROQ_API_KEY", "")
        self.brain = Groq(api_key=api_key) if Groq and api_key else None

        # تفعيل الذاكرة (GitHub) — مصدر واحد من core.config
        token = _GH_TOKEN or os.getenv("GITHUB_TOKEN", "")
        repo_name = _GH_REPO or os.getenv("GITHUB_REPO", "")
        self.memory_client = Github(token) if Github and token else None
        self.repo = None
        if self.memory_client and repo_name:
            try:
                self.repo = self.memory_client.get_repo(repo_name)
            except Exception:
                self.repo = None

    def sync_knowledge(self) -> str:
        """قراءة الذاكرة من GitHub قبل البدء. Returns content of knowledge_base.md or empty string."""
        if not self.repo:
            return ""
        try:
            content = self.repo.get_contents("knowledge_base.md")
            return content.decoded_content.decode("utf-8", errors="replace")
        except Exception:
            return ""

    def self_update(self, new_fact: str) -> bool:
        """تحديث الذاكرة تلقائياً (التطور الذاتي). Appends to knowledge_base.md and pushes to GitHub."""
        if not new_fact or not str(new_fact).strip():
            return False
        if not self.repo:
            return False
        try:
            file = self.repo.get_contents("knowledge_base.md")
            new_content = file.decoded_content.decode("utf-8", errors="replace") + f"\n- {new_fact.strip()[:3000]}"
            self.repo.update_file(file.path, "Autonomous Memory Update", new_content, file.sha)
            return True
        except Exception:
            try:
                self.repo.create_file(
                    "knowledge_base.md",
                    "Autonomous Memory Update",
                    f"- {new_fact.strip()[:3000]}",
                    branch=None,
                )
                return True
            except Exception:
                return False


class CoreAI_Engine:
    """
    محرك كامل: عقل (Groq) + ذاكرة (GitHub) + بحث حي (DuckDuckGo).
    قاعدة عدم التخمين: البحث الحي أولاً ثم الرد بناءً على البيانات الحية فقط.
    """

    KNOWLEDGE_PATH = "knowledge_base.md"

    def __init__(self, today: Optional[str] = None):
        # تفعيل الاتصال بالعقل (Groq) والذاكرة (GitHub)
        api_key = os.getenv("GROQ_API_KEY", "")
        self.brain = Groq(api_key=api_key) if Groq and api_key else None

        token = _GH_TOKEN or os.getenv("GITHUB_TOKEN", "")
        repo_name = _GH_REPO or os.getenv("GITHUB_REPO", "")
        gh = Github(token) if Github and token else None
        self.memory = None
        if gh and repo_name:
            try:
                self.memory = gh.get_repo(repo_name)
            except Exception:
                self.memory = None

        # التاريخ الثابت لضمان الدقة (أو اليوم الفعلي)
        self.today = today or "2026-03-07"

    def web_verify(self, query: str) -> str:
        """قنص المعلومات الحية بتاريخ اليوم (7 مارس 2026)."""
        if not query or not str(query).strip():
            return ""
        if not DDGS:
            return ""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(f"{query.strip()} {self.today}", max_results=3))
                return "\n".join([r.get("body", "") for r in results if isinstance(r, dict)])
        except Exception:
            return ""

    def update_knowledge(self, new_fact: str) -> bool:
        """تحديث المستودع تلقائياً ليتعلم البرنامج من أخطائه."""
        if not new_fact or not str(new_fact).strip():
            return False
        if not self.memory:
            return False
        try:
            file = self.memory.get_contents(self.KNOWLEDGE_PATH)
            updated_content = file.decoded_content.decode("utf-8", errors="replace") + f"\n- [{self.today}] {new_fact.strip()[:3000]}"
            self.memory.update_file(file.path, "Autonomous Learning Update", updated_content, file.sha)
            return True
        except Exception:
            try:
                self.memory.create_file(
                    self.KNOWLEDGE_PATH,
                    "Autonomous Learning Update",
                    f"- [{self.today}] {new_fact.strip()[:3000]}",
                    branch=None,
                )
                return True
            except Exception:
                return False

    def generate_response(self, user_input: str) -> str:
        """منطق التفكير الاحترافي (Reasoning): بحث حي أولاً ثم رد بناءً على البيانات فقط."""
        if not user_input or not str(user_input).strip():
            return ""
        # 1. البحث الحي أولاً (قاعدة عدم التخمين)
        live_data = self.web_verify(user_input)
        # 2. بناء السياق للـ Groq
        prompt = (
            f"System Date: {self.today}\nLive Data: {live_data}\nUser Query: {user_input}\n"
            "Instruction: Provide a professional response based ONLY on live data. Use 18px font. No headers (#)."
        )
        # 3. جلب الرد من Groq
        if not self.brain:
            return live_data or "لا يتوفر عقل (Groq) أو بيانات حية."
        try:
            response = self.brain.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content or ""
        except Exception:
            return live_data or "تعذر الاتصال بـ Groq. اعتمد على البيانات الحية أعلاه فقط."


# تفعيل النظام (singleton optional)
_core_instance: Optional[CoreAI] = None


def get_core() -> CoreAI:
    """Return the shared CoreAI instance."""
    global _core_instance
    if _core_instance is None:
        _core_instance = CoreAI()
    return _core_instance


# تفعيل النظام — use: from core.core_ai import core, core_engine
core = get_core()

_engine_instance: Optional[CoreAI_Engine] = None


def get_core_engine(today: Optional[str] = None) -> CoreAI_Engine:
    """Return the shared CoreAI_Engine instance (optional today override)."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = CoreAI_Engine(today=today)
    return _engine_instance


core_engine = get_core_engine()
