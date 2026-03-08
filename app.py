import streamlit as st
import base64
from pathlib import Path

# --- 1. إعداد الصفحة (إخفاء كل شيء فعلياً) ---
st.set_page_config(page_title="CORE AI", layout="wide", initial_sidebar_state="collapsed")

# --- 2. كود CSS "السيطرة المطلقة" ---
# هذا الكود بيشيل أي padding أو مارجن من ستريمليت وبيخلي الـ iframe يطير فوق كل شي
st.markdown("""
    <style>
        #MainMenu, footer, header, [data-testid="stSidebar"] {display: none !important;}
        .stApp { background-color: #191a1a !important; padding: 0 !important; }
        .main .block-container { padding: 0 !important; max-width: 100% !important; margin: 0 !important; }
        
        /* إجبار الإطار على أخذ كامل مساحة المتصفح بصرف النظر عن أي شيء */
        iframe {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            border: none !important;
            z-index: 999999 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. دالة تحويل الصور ---
def get_base64(path):
    if Path(path).exists():
        return base64.b64encode(open(path, "rb").read()).decode()
    return ""

ROOT = Path(__file__).resolve().parent
logo_b64 = get_base64(ROOT / "logo.png") or get_base64(ROOT / "logo.jpg")

# --- 4. حقن الملف وعرضه ---
index_path = ROOT / "index.html"
if index_path.exists():
    html_content = index_path.read_text(encoding="utf-8")
    
    # حقن اللوجو
    if logo_b64:
        html_content = html_content.replace('src="logo.png"', f'src="data:image/png;base64,{logo_b64}"')
        html_content = html_content.replace('src="logo.jpg"', f'src="data:image/jpeg;base64,{logo_b64}"')

    # عرض الملف بـ "قوة" الـ components
    st.components.v1.html(html_content, height=2000) 
else:
    st.error("Check index.html path!")