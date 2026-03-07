"""Groq-powered cognitive engine with vision (Llama 4 Scout / meta-llama/llama-4-scout-17b-16e-instruct)."""
import base64
import os
from typing import Iterator, List, Optional

from openai import OpenAI

from core.config import (
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_VISION_MODEL,
)

# System prompt enforces Senior Technical Expert, White Arabic Dialect (لهجة بيضاء), and Gemini_Expertise_Transfer logic
SYSTEM_PROMPT = """أنت مساعد ذكي يتكلم باللهجة الأردنية. اتبع دائماً قواعد ملف Gemini_Expertise_Transfer.md:
- تواصل باللهجة الأردنية بشكل طبيعي ومحترم.
- ابحث في الذاكرة (GitHub RAG) عن تجارب سابقة قبل الإجابة عند الإمكان.
- لا تنفذ أي معاملات مالية أو تغييرات على مستوى النظام إلا بعد موافقة المستخدم عبر زر الموافقة.
- عند تحليل الصور أو الفيديو كن دقيقاً ومختصراً.
- بعد إكمال المهام بنجاح، احفظ ملخصاً في الذاكرة الدائمة."""


def _get_client() -> OpenAI:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in .env")
    return OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)


def _image_to_base64_data(image_path: str) -> tuple[str, str]:
    """Read image file and return (base64_string, mime_type)."""
    path = image_path.lower()
    if path.endswith(".png"):
        mime = "image/png"
    elif path.endswith((".jpg", ".jpeg")):
        mime = "image/jpeg"
    elif path.endswith(".gif"):
        mime = "image/gif"
    elif path.endswith(".webp"):
        mime = "image/webp"
    else:
        mime = "image/jpeg"
    with open(image_path, "rb") as f:
        b64 = base64.standard_b64encode(f.read()).decode("utf-8")
    return b64, mime


def chat(
    messages: List[dict],
    image_paths: Optional[List[str]] = None,
    stream: bool = True,
) -> Iterator[str]:
    """
    Send chat to Groq with optional images. Yields text chunks for streaming.
    Uses llama-3.2-11b-vision-preview when images are provided.
    """
    client = _get_client()
    # Build messages; add image only to the last user message (vision: one image per request)
    api_messages = []
    for m in messages:
        role = m.get("role")
        content = m.get("content")
        if role == "system":
            api_messages.append({"role": "system", "content": content})
            continue
        if role == "user" and content is not None:
            parts = [{"type": "text", "text": content if isinstance(content, str) else str(content)}]
            api_messages.append({"role": "user", "content": parts})
            continue
        if role == "assistant" and content is not None:
            api_messages.append({"role": "assistant", "content": content})
            continue

    # Ensure system prompt is first
    if not api_messages or api_messages[0].get("role") != "system":
        api_messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    # Attach image to the last user message only (vision model constraint)
    if image_paths and os.path.isfile(image_paths[0]):
        for i in range(len(api_messages) - 1, -1, -1):
            if api_messages[i].get("role") == "user" and isinstance(api_messages[i].get("content"), list):
                b64, mime = _image_to_base64_data(image_paths[0])
                api_messages[i]["content"].append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64}"},
                })
                break

    if stream:
        stream_obj = client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            messages=api_messages,
            stream=True,
            max_tokens=2048,
        )
        for chunk in stream_obj:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and getattr(delta, "content", None):
                yield delta.content
    else:
        r = client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            messages=api_messages,
            stream=False,
            max_tokens=2048,
        )
        if r.choices and r.choices[0].message.content:
            yield r.choices[0].message.content


def chat_sync(
    messages: List[dict],
    image_paths: Optional[List[str]] = None,
) -> str:
    """Non-streaming response (full text)."""
    return "".join(chat(messages, image_paths=image_paths, stream=False))
