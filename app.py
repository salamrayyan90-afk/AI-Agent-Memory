import streamlit as st
from pathlib import Path

# إعداد الصفحة لتكون بعرض كامل وتختفي منها كل هوامش ستريمليت
st.set_page_config(page_title="CORE AI", layout="wide", initial_sidebar_state="collapsed")

# كود سحري يصفر المسافات ويخلي ملفك يفرش على كل الشاشة
st.markdown("""
    <style>
        #MainMenu, footer, header, [data-testid="stSidebar"] {display: none !important;}
        .stApp {background-color: #191a1a;}
        .main .block-container {padding: 0 !important; max-width: 100% !important; margin: 0 !important;}
        iframe {position: fixed; top: 0; left: 0; width: 100vw !important; height: 100vh !important; border: none !important;}
    </style>
""", unsafe_allow_html=True)

# قراءة ملفك الـ HTML الأصلي اللي فيه الخلفية المتحركة
ROOT = Path(__file__).resolve().parent
index_path = ROOT / "index.html"

if index_path.exists():
    html_content = index_path.read_text(encoding="utf-8")
    # عرض الملف كـ iframe يغطي الشاشة 100%
    st.components.v1.html(html_content, height=2000)
else:
    st.error("يا غالي، ملف index.html مش موجود بنفس المجلد، تأكد منه!")