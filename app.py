import streamlit as st
import base64
from pathlib import Path

# --- 1. إعداد الصفحة بأقصى عرض ممكن ---
st.set_page_config(page_title="CORE AI", layout="wide", initial_sidebar_state="collapsed")

# --- 2. كود السحر لقتل هوامش ستريمليت نهائياً ---
st.markdown("""
    <style>
        /* إخفاء كل زوائد ستريمليت بصرياً وبرمجياً */
        #MainMenu, footer, header, [data-testid="stSidebar"] {display: none !important;}
        
        /* تصفير الحواف والمساحات البيضاء */
        .stApp { background-color: #191a1a !important; padding: 0 !important; }
        .main .block-container { padding: 0 !important; max-width: 100% !important; margin: 0 !important; }
        
        /* إجبار الإطار على أخذ كامل مساحة المتصفح بصرف النظر عن أي شيء */
        iframe {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw !important;
            height: 100vh !important;
            border: none !important;
            z-index: 1;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. قراءة وحقن ملف index.html ---
ROOT = Path(__file__).resolve().parent
index_path = ROOT / "index.html"

def get_base64_img(path):
    if Path(path).exists():
        return base64.b64encode(open(path, "rb").read()).decode()
    return ""

if index_path.exists():
    html_content = index_path.read_text(encoding="utf-8")
    
    # تأمين ظهور اللوجو داخل الإطار
    logo_b64 = get_base64_img(ROOT / "logo.png") or get_base64_img(ROOT / "logo.jpg")
    if logo_b64:
        html_content = html_content.replace('src="logo.png"', f'src="data:image/png;base64,{logo_b64}"')
        html_content = html_content.replace('src="logo.jpg"', f'src="data:image/jpeg;base64,{logo_b64}"')

    # عرض الملف كـ Full Viewport Component
    st.components.v1.html(html_content, height=2000) # ارتفاع كبير لمنع التقطيع
else:
    st.error("Error: index.html not found in ROOT directory.")