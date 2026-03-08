import streamlit as st
import base64
from pathlib import Path

# --- 1. إعدادات الصفحة (عرض كامل وتعتيم) ---
st.set_page_config(page_title="CORE AI", layout="wide", initial_sidebar_state="collapsed")

# تنظيف شامل لكل زوائد ستريمليت
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stSidebar"] {display: none;}
        .stApp { background-color: #191a1a; padding: 0 !important; }
        .main .block-container { padding: 0 !important; max-width: 100% !important; margin: 0 !important; }
        iframe { border: none !important; width: 100vw !important; height: 100vh !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. تحويل اللوجو لـ Base64 لضمان ظهوره وسط الخلفية المتحركة ---
def get_image_base64(path):
    if Path(path).exists():
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

ROOT = Path(__file__).resolve().parent
logo_b64 = get_image_base64(ROOT / "logo.png") or get_image_base64(ROOT / "logo.jpg")

# --- 3. قراءة الـ HTML الأصلي (مع الفيزيائية) وحقن التعديلات ---
index_path = ROOT / "index.html"
if index_path.exists():
    html_content = index_path.read_text(encoding="utf-8")
    
    # تأمين ظهور اللوجو
    if logo_b64:
        html_content = html_content.replace('src="logo.png"', f'src="data:image/png;base64,{logo_b64}"')
        html_content = html_content.replace('src="logo.jpg"', f'src="data:image/jpeg;base64,{logo_b64}"')

    # جافاسكريبت لربط المربع بـ Streamlit (الجسر)
    bridge_script = """
    <script>
    function sendToStreamlit() {
        const input = document.getElementById('searchInput');
        if (input.value.trim() !== "") {
            const url = new URL(window.location.origin + window.parent.location.pathname);
            url.searchParams.set('user_query', input.value);
            window.parent.location.href = url.href;
        }
    }
    // ربط الزر والإنتر
    document.getElementById('submitBtn').addEventListener('click', sendToStreamlit);
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
        if(e.key === 'Enter') sendToStreamlit();
    });
    </script>
    """
    
    # دمج السكريبت قبل نهاية الـ body
    final_html = html_content.replace('</body>', bridge_script + '</body>')
    
    # العرض النهائي
    st.components.v1.html(final_html, height=1000, scrolling=False)