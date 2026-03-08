"""
Core AI — UI Version 3.0: Blueprint from HTML/CSS.
Exact tokens: --bg-color #191a1a, --card-bg #202222, glassmorphism, 18px, Zero Headers.
"""
from pathlib import Path
from typing import Optional

try:
    from core.config import BACKGROUND_COLOR
except ImportError:
    BACKGROUND_COLOR = "#191a1a"

# Blueprint design tokens (from provided HTML)
FONT_SIZE_PX = 18
BG_COLOR = "#191a1a"
SIDEBAR_BG = "#191a1a"
SIDEBAR_WIDTH = "260px"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#a3a3a3"
BORDER_COLOR = "#2d2e2e"
ACCENT_COLOR = "#20b2aa"
CARD_BG = "#202222"
HOVER_BG = "#2d2e2e"


def get_streamlit_dark_css(font_size_px: Optional[int] = None) -> str:
    """
    Return Streamlit CSS matching the HTML blueprint: #191a1a, glassmorphism,
    search-container, sidebar, hero glow, floating background icons (CSS-only).
    All dynamic AI text stays 18px; Zero Headers (use bold only).
    """
    px = font_size_px if font_size_px is not None else FONT_SIZE_PX
    return f"""
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" rel="stylesheet">
    <style>
    :root {{
        --bg-color: {BG_COLOR};
        --text-primary: {TEXT_PRIMARY};
        --text-secondary: {TEXT_SECONDARY};
        --border-color: {BORDER_COLOR};
        --accent-color: {ACCENT_COLOR};
        --sidebar-width: {SIDEBAR_WIDTH};
        --card-bg: {CARD_BG};
        --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}

    * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: var(--font-family); }}
    body, .stApp {{
        background-color: var(--bg-color) !important;
        color: var(--text-primary) !important;
        font-family: var(--font-family) !important;
        font-size: {px}px !important;
    }}

    /* Sidebar — blueprint */
    [data-testid="stSidebar"] {{
        width: var(--sidebar-width) !important;
        min-width: var(--sidebar-width) !important;
        background: var(--bg-color) !important;
        border-right: 1px solid var(--border-color) !important;
        font-family: var(--font-family) !important;
    }}
    [data-testid="stSidebar"] .stMarkdown {{ color: var(--text-primary) !important; }}
    [data-testid="stSidebar"] .stMarkdown p {{ font-size: {px}px !important; }}

    /* Main content: margin-left per blueprint so sidebar does not overlap */
    [data-testid="stAppViewContainer"] > section.main {{
        margin-left: var(--sidebar-width);
        transition: margin-left 0.3s ease;
    }}
    .main .block-container {{
        max-width: 800px;
        margin: 0 auto;
        padding: 0 20px;
        font-size: {px}px !important;
        text-align: center;
    }}
    .main .block-container > div {{ display: flex; flex-direction: column; align-items: center; }}

    /* index.html exact: .code-background */
    .code-background {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 0;
        overflow: hidden;
    }}
    /* index.html exact: .bg-icon opacity 0.15, transition 0.1s linear */
    .bg-icon {{
        position: absolute;
        color: var(--text-secondary);
        opacity: 0.15;
        transition: transform 0.1s linear, opacity 0.3s ease;
        pointer-events: none;
        font-size: 18px;
    }}

    /* Header — Log In / Sign Up */
    .blueprint-header {{
        height: 64px;
        padding: 0 24px;
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 16px;
        position: relative;
        z-index: 1;
    }}
    .btn-outline {{
        padding: 6px 16px;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        background: transparent;
        color: var(--text-primary);
        cursor: pointer;
        font-size: 0.9rem;
    }}
    .btn-dark {{
        padding: 6px 16px;
        border: none;
        border-radius: 6px;
        background: #ffffff;
        color: #191919;
        cursor: pointer;
        font-size: 0.9rem;
    }}

    /* Hero — logo container + glow (exact index.html) */
    .logo-container {{
        position: relative;
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
        z-index: 1;
    }}
    @keyframes glow {{
        0% {{ filter: drop-shadow(0 0 10px rgba(32, 178, 170, 0.4)); transform: scale(1); }}
        50% {{ filter: drop-shadow(0 0 30px rgba(32, 178, 170, 0.8)); transform: scale(1.02); }}
        100% {{ filter: drop-shadow(0 0 10px rgba(32, 178, 170, 0.4)); transform: scale(1); }}
    }}
    .logo-container img {{
        width: 280px;
        height: auto;
        object-fit: contain;
        animation: glow 3s ease-in-out infinite;
    }}
    .hero-title {{
        font-size: 2.5rem;
        margin-bottom: 8px;
        font-weight: 500;
        letter-spacing: 2px;
        z-index: 1;
    }}
    .hero-subtitle {{
        color: var(--text-secondary);
        margin-bottom: 32px;
        font-size: 1.1rem;
        z-index: 1;
    }}

    /* Proactive Suggestions: spacing per blueprint to separate from main input */
    [data-testid="stExpander"] {{
        margin-top: 24px;
        margin-bottom: 24px;
        z-index: 1;
    }}

    /* Search container — exact index.html */
    .search-container {{
        width: 100%;
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        margin-bottom: 16px;
        position: relative;
        z-index: 1;
    }}
    .search-input-wrapper {{ display: flex; align-items: center; margin-bottom: 12px; }}
    .search-controls {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
    }}
    .control-group {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
    .control-item {{
        display: flex;
        align-items: center;
        gap: 6px;
        color: var(--text-secondary);
        font-size: 0.85rem;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 4px;
    }}
    .control-item:hover {{ background: #2d2e2e; }}


    /* Quick actions */
    .quick-actions {{
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 10px;
        margin-top: 16px;
        z-index: 1;
    }}
    .action-chip {{
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 12px;
        border: 1px solid var(--border-color);
        border-radius: 20px;
        font-size: 0.85rem;
        color: var(--text-secondary);
        cursor: pointer;
        background: var(--card-bg);
    }}
    .action-chip:hover {{ background: #2d2e2e; }}

    /* Footer */
    .footer-text {{
        font-size: 0.7rem;
        color: #999;
        margin-top: 24px;
        line-height: 1.4;
        z-index: 1;
    }}
    .footer-text a {{ color: #777; text-decoration: none; }}

    /* Chat messages: 18px, no Markdown headers */
    .stMarkdown, .stMarkdown p, .main .block-container {{ font-size: {px}px !important; }}
    [data-testid="stChatMessage"] .stMarkdown,
    [data-testid="stChatMessage"] .stMarkdown p,
    [data-testid="stChatMessage"] .stMarkdown h1, [data-testid="stChatMessage"] .stMarkdown h2,
    [data-testid="stChatMessage"] .stMarkdown h3, [data-testid="stChatMessage"] .stMarkdown h4,
    [data-testid="stChatMessage"] .stMarkdown h5, [data-testid="stChatMessage"] .stMarkdown h6 {{
        font-size: {px}px !important; font-weight: inherit; margin: 0.5em 0; line-height: 1.5;
    }}
    [data-testid="stChatMessage"] .stMarkdown strong {{ font-weight: 700; }}
    /* Zero Headers: never use #; render as bold same size */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {{
        font-size: {px}px !important; font-weight: 700; margin: 0.5em 0; line-height: 1.4;
    }}

    /* Streamlit chat input inside search container */
    .search-container [data-testid="stChatInput"] {{
        background: transparent !important;
        border: none !important;
    }}
    .search-container [data-testid="stChatInput"] textarea {{
        background: transparent !important;
        color: var(--text-primary) !important;
        font-size: 1rem !important;
        border: none !important;
    }}
    header[data-testid="stHeader"] {{ display: none; }}

    /* Physics iframe: fixed behind main content (index.html script runs inside) */
    .stApp [data-testid="stFrame"]:first-of-type {{
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        z-index: 0 !important;
        pointer-events: none !important;
    }}
    .stApp [data-testid="stFrame"]:first-of-type iframe {{
        width: 100% !important;
        height: 100% !important;
        border: none !important;
    }}
    </style>
    """


# Icons from index.html script (exact list)
_BG_ICONS_INDEX = [
    "fas fa-code", "fas fa-terminal", "fas fa-database", "fas fa-microchip",
    "fas fa-network-wired", "fas fa-file-code", "fab fa-python", "fab fa-js-square",
    "fab fa-html5", "fab fa-css3-alt", "fas fa-cube", "fas fa-robot",
    "fas fa-brain", "fas fa-cogs", "fas fa-eye", "fas fa-language",
    "fas fa-project-diagram", "fas fa-microscope", "fas fa-flask",
]


def get_blueprint_background_html() -> str:
    """Return HTML for code-background div (static fallback when JS not used)."""
    parts = ['<div class="code-background" id="codeBg">']
    for i, icon_class in enumerate(_BG_ICONS_INDEX * 3):
        left = (7 + i * 11) % 91 + 2
        top = (13 + i * 17) % 88 + 2
        parts.append(f'<i class="{icon_class} bg-icon" style="left:{left}%;top:{top}%;"></i>')
    parts.append("</div>")
    return "".join(parts)


def get_physics_background_full_html() -> str:
    """Return full HTML document for physics background (index.html script). For st.components.v1.html()."""
    icon_list = ", ".join(f"'{c}'" for c in _BG_ICONS_INDEX)
    return f"""<!DOCTYPE html><html><head><link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" rel="stylesheet"><style>
:root {{ --text-secondary: #a3a3a3; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
.code-background {{ position: absolute; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:0; overflow:hidden; }}
.bg-icon {{ position: absolute; color: var(--text-secondary); opacity: 0.15; transition: transform 0.1s linear, opacity 0.3s ease; pointer-events: none; }}
.collision-flash {{ position: absolute; width: 4px; height: 4px; background: white; border-radius: 50%; box-shadow: 0 0 10px white; pointer-events: none; z-index: 1; animation: flash-out 0.4s ease-out forwards; }}
@keyframes flash-out {{ 0% {{ transform: scale(1); opacity: 1; }} 100% {{ transform: scale(4); opacity: 0; }} }}
</style></head><body style="margin:0;overflow:hidden;"><div class="code-background" id="codeBg"></div>
<script>
var iconClasses = [{icon_list}];
var particles = [];
var particleCount = 60;
var codeBg = document.getElementById('codeBg');
for (var i = 0; i < particleCount; i++) {{
    var iconEl = document.createElement('i');
    iconEl.className = iconClasses[Math.floor(Math.random() * iconClasses.length)] + ' bg-icon';
    codeBg.appendChild(iconEl);
    particles.push({{ el: iconEl, x: Math.random() * window.innerWidth, y: Math.random() * window.innerHeight, vx: (Math.random() - 0.5) * 4, vy: (Math.random() - 0.5) * 4, radius: 15 }});
}}
function createFlash(x, y) {{
    var flash = document.createElement('div');
    flash.className = 'collision-flash';
    flash.style.left = x + 'px';
    flash.style.top = y + 'px';
    codeBg.appendChild(flash);
    setTimeout(function() {{ flash.remove(); }}, 400);
}}
function updatePhysics() {{
    for (var i = 0; i < particles.length; i++) {{
        var p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > window.innerWidth) p.vx *= -1;
        if (p.y < 0 || p.y > window.innerHeight) p.vy *= -1;
        for (var j = i + 1; j < particles.length; j++) {{
            var p2 = particles[j];
            var dx = p2.x - p.x, dy = p2.y - p.y;
            var distance = Math.sqrt(dx * dx + dy * dy);
            if (distance < p.radius + p2.radius) {{
                var tempVx = p.vx, tempVy = p.vy;
                p.vx = p2.vx; p.vy = p2.vy;
                p2.vx = tempVx; p2.vy = tempVy;
                createFlash((p.x + p2.x) / 2, (p.y + p2.y) / 2);
                p.x += p.vx; p.y += p.vy;
            }}
        }}
        p.el.style.transform = 'translate(' + p.x + 'px, ' + p.y + 'px)';
    }}
    requestAnimationFrame(updatePhysics);
}}
updatePhysics();
</script></body></html>"""


def get_logo_data_uri(root: Path) -> Optional[str]:
    """Return data URI for CoreAI.ico (asset lock), then logo.png/logo.jpg for use in HTML img src."""
    import base64
    # Asset lock: CoreAI.ico for logo and favicon
    ico = root / "CoreAI.ico"
    if ico.is_file():
        try:
            b = ico.read_bytes()
            return f"data:image/x-icon;base64,{base64.b64encode(b).decode()}"
        except Exception:
            pass
    for name in ("logo.png", "logo.jpg"):
        p = root / name
        if p.is_file():
            try:
                b = p.read_bytes()
                ext = "png" if name.endswith(".png") else "jpeg"
                return f"data:image/{ext};base64,{base64.b64encode(b).decode()}"
            except Exception:
                pass
    return None


def apply_dark_theme(streamlit_module, font_size_px: Optional[int] = None) -> None:
    """Apply Core AI blueprint theme."""
    streamlit_module.markdown(get_streamlit_dark_css(font_size_px), unsafe_allow_html=True)
