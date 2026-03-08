import streamlit as st
import base64
from pathlib import Path

# --- 1. إعداد الصفحة (إخفاء كل شيء فعلياً) ---
st.set_page_config(page_title="CORE AI", layout="wide", initial_sidebar_state="collapsed")

# هذا الجزء يقتل أي هوامش بيضاء من ستريمليت نهائياً
st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] { background-color: #191a1a !important; }
        .main .block-container { padding: 0 !important; max-width: 100% !important; margin: 0 !important; }
        iframe { position: fixed; top: 0; left: 0; width: 100vw !important; height: 100vh !important; border: none !important; z-index: 999; }
        #MainMenu, footer, header, [data-testid="stSidebar"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. دالة تحويل الصور (لضمان ظهور اللوجو وسط الأيقونات المتحركة) ---
def get_image_base64(path):
    p = Path(path)
    if p.exists():
        with open(p, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

ROOT = Path(__file__).resolve().parent
logo_b64 = get_image_base64(ROOT / "logo.png") or get_image_base64(ROOT / "logo.jpg")

# --- 3. حقن ملف index.html الأصلي ---
index_path = ROOT / "index.html"
if index_path.exists():
    html_content = index_path.read_text(encoding="utf-8")
    
    # تحديث اللوجو ليعمل داخل السيرفر
    if logo_b64:
        html_content = html_content.replace('src="logo.png"', f'src="data:image/png;base64,{logo_b64}"')
        html_content = html_content.replace('src="logo.jpg"', f'src="data:image/jpeg;base64,{logo_b64}"')

    # الجسر لربط صندوق البحث (تحديث الرابط العلوي)
    bridge = """
    <script>
    function send() {
        var val = document.getElementById('searchInput').value;
        if(val.trim() != "") {
            var url = new URL(window.parent.location.href);
            url.searchParams.set('user_query', val);
            window.parent.location.href = url.href;
        }
    }
    document.getElementById('submitBtn').onclick = send;
    document.getElementById('searchInput').onkeypress = function(e){ if(e.key=='Enter') send(); };
    </script>
    """
    html_with_bridge = html_content.replace('</body>', bridge + '</body>')
    
    # عرض الملف كـ Full Screen Component
    st.components.v1.html(html_with_bridge, height=2000) # ارتفاع كبير لضمان التغطية
else:
    st.error("Check if index.html is in the same folder!")

# --- 4. استقبال السؤال ---
query = st.query_params.get("user_query")
if query:
    st.toast(f"جاري البحث عن: {query}")