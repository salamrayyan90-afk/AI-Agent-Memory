import streamlit as st
import base64
from pathlib import Path

# --- 1. تصفير إعدادات الصفحة تماماً ---
st.set_page_config(page_title="CORE AI", layout="wide", initial_sidebar_state="collapsed")

# --- 2. كود CSS جبار لإلغاء وجود ستريمليت بصرياً ---
st.markdown("""
    <style>
        /* إخفاء كل شيء يخص ستريمليت */
        #MainMenu, footer, header, [data-testid="stSidebar"] {display: none !important;}
        
        /* جعل الحاوية الأساسية بدون أي هوامش أو مسافات */
        .stApp { background-color: #191a1a !important; }
        .main .block-container { padding: 0 !important; max-width: 100% !important; margin: 0 !important; }
        
        /* إجبار الإطار (iframe) على ملء الشاشة بالكامل كخلفية ثابتة */
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

# --- 3. تجهيز اللوجو (Base64) لضمان ظهوره ---
def get_image_base64(path):
    p = Path(path)
    if p.exists():
        with open(p, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

ROOT = Path(__file__).resolve().parent
logo_b64 = get_image_base64(ROOT / "logo.png") or get_image_base64(ROOT / "logo.jpg")

# --- 4. عرض ملف index.html الأصلي بكامل قوته ---
index_path = ROOT / "index.html"
if index_path.exists():
    html_content = index_path.read_text(encoding="utf-8")
    
    # حقن اللوجو في مكانه الصحيح
    if logo_b64:
        html_content = html_content.replace('src="logo.png"', f'src="data:image/png;base64,{logo_b64}"')
        html_content = html_content.replace('src="logo.jpg"', f'src="data:image/jpeg;base64,{logo_b64}"')

    # عرض الملف كـ Component وحيد يسيطر على المتصفح
    st.components.v1.html(html_content, height=2000) # ارتفاع كبير لضمان عدم ظهور فراغ
else:
    st.error("تأكد أن ملف index.html موجود في نفس المجلد!")

# --- 5. محرك استقبال الرسائل ---
query = st.query_params.get("user_query")
if query:
    st.toast(f"جاري معالجة طلبك: {query}")