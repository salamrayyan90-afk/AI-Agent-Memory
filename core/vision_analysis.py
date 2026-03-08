"""
Core Vision — Image analysis using Groq Llama Vision.
Analyzes resolution, lighting, 3D-depth potential; suggests OpenCV/PyTorch enhancement code;
identifies Visual Errors and provides Auto-Fix script. Output: 18px, Zero Headers.
"""
import base64
import io
import re
from typing import Any, Dict, List, Optional, Tuple

try:
    from groq import Groq
except ImportError:
    Groq = None

import os
try:
    from core.groq_client import get_groq_client, get_vision_model
    from core.config import GROQ_API_KEY
except ImportError:
    get_groq_client = None
    get_vision_model = lambda: "meta-llama/llama-4-scout-17b-16e-instruct"
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

CORE_VISION_SYSTEM = """You are Core Vision. Analyze 2D images for technical and creative use.
Output format (use these exact section labels). Use **bold** for emphasis only; NO Markdown headers (#).

**REPORT:** (Visual analysis in one block)
- Resolution: dimensions and quality assessment.
- Lighting: exposure, shadows, contrast.
- 3D-depth potential: suitability for depth estimation or 3D conversion (e.g. stereo, structure, texture).
Use 18px-style prose; no # headers.

**VISUAL_ERRORS:** List any issues (noise, blur, overexposure, distortion). One line, semicolon-separated, or "None" if none.

**ENHANCEMENT_CODE:** Python code using OpenCV or PyTorch to enhance the image for 3D conversion (e.g. denoise, contrast, edge enhancement). One code block only.

**AUTO_FIX_SCRIPT:** A complete, runnable Python script that fixes the visual errors you listed. Save as a single script (imports + main logic). One code block only.

If the image is not suitable for enhancement, say so in REPORT and leave ENHANCEMENT_CODE/AUTO_FIX_SCRIPT as minimal placeholder comments."""


def _pil_to_data_url(pil_img) -> str:
    """Convert PIL Image to base64 data URL for Vision API."""
    buf = io.BytesIO()
    fmt = "PNG" if (getattr(pil_img, "mode", "") == "RGBA") else "PNG"
    pil_img.save(buf, format=fmt)
    b64 = base64.standard_b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def _extract_section(text: str, label: str) -> Optional[str]:
    """Extract content after **LABEL:** until next **SECTION:** or end."""
    if not text:
        return None
    pattern = rf"\*\*{re.escape(label)}\*\*[:\s]*([\s\S]*?)(?=\*\*[A-Z_]+\*\*|\Z)"
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return None
    return m.group(1).strip()


def _extract_code_block(text: str) -> Optional[str]:
    """Extract first ```python ... ``` or ``` ... ``` block."""
    if not text:
        return None
    m = re.search(r"```(?:python)?\s*([\s\S]*?)```", text)
    return m.group(1).strip() if m else None


def run_core_vision_analysis(pil_img, user_question: str = "") -> Dict[str, Any]:
    """
    Process image with Groq Vision. Returns:
    - report: str (visual analysis, 18px-style)
    - enhancement_code: str (Python for OpenCV/PyTorch)
    - visual_errors: list of str
    - auto_fix_script: str (full script to save)
    - raw: str (full model response)
    """
    out = {
        "report": "",
        "enhancement_code": "",
        "visual_errors": [],
        "auto_fix_script": "",
        "raw": "",
    }
    client = get_groq_client() if callable(get_groq_client) else None
    if not client or not GROQ_API_KEY:
        return out
    try:
        data_url = _pil_to_data_url(pil_img)
        model = get_vision_model() if callable(get_vision_model) else get_vision_model
        model_name = model() if callable(model) else str(model)
        prompt = "Analyze this 2D image: resolution, lighting, 3D-depth potential. Suggest enhancement code and list visual errors with an Auto-Fix script."
        if user_question and user_question.strip():
            prompt += f"\nUser request: {user_question.strip()[:500]}"
        comp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": CORE_VISION_SYSTEM},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ]},
            ],
            stream=False,
        )
        raw = (comp.choices[0].message.content or "").strip()
        out["raw"] = raw
        out["report"] = _extract_section(raw, "REPORT") or raw.split("**VISUAL_ERRORS**")[0].strip() or raw[:2000]
        err_text = _extract_section(raw, "VISUAL_ERRORS")
        if err_text and err_text.lower() != "none":
            out["visual_errors"] = [e.strip() for e in err_text.replace(";", "\n").split("\n") if e.strip()]
        enh = _extract_section(raw, "ENHANCEMENT_CODE")
        if enh:
            out["enhancement_code"] = _extract_code_block(enh) or enh
        auto = _extract_section(raw, "AUTO_FIX_SCRIPT")
        if auto:
            out["auto_fix_script"] = _extract_code_block(auto) or auto
    except Exception:
        pass
    return out


def push_visual_insights_to_github(report_summary: str, code_snippet: str, file_path: str = "") -> bool:
    """Push Visual Insights and generated enhancement code to knowledge_base.md."""
    try:
        from memory.github_rag import update_agent_knowledge
    except ImportError:
        return False
    snippet = (code_snippet or "")[:2500]
    entry = f"[Visual Insights] {report_summary.strip()[:1500]} (18px / Zero Headers)."
    if file_path:
        entry += f" Auto-Fix script: {file_path}."
    if snippet:
        entry += f"\n```\n{snippet}\n```"
    return update_agent_knowledge(entry)
