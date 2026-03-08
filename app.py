import sys
import subprocess
import os
import streamlit as st
import base64
import re
from pathlib import Path

# --- 1. إعداد الصفحة وإخفاء زوائد Streamlit + تنسيق العرض الكامل ---
st.set_page_config(page_title="CORE AI", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stSidebar"] {display: none;}
        /* إزالة الهوامش والبادينج لجعل الواجهة تغطي كامل الشاشة */
        .stApp { padding: 0 !important; overflow: hidden; }
        .main .block-container { padding: 0 !important; max-width: 100% !important; margin: 0 !important; }
        iframe { width: 100% !important; border: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. محرك قراءة الصور وتحويلها لـ Base64 لضمان ظهورها داخل الـ iframe ---
def get_base64_image(image_path):
    p = Path(image_path)
    if p.exists():
        with open(p, "rb") as img_file:
            return f"data:image/{p.suffix[1:]};base64," + base64.b64encode(img_file.read()).decode()
    return None

ROOT = Path(__file__).resolve().parent
logo_uri = get_base64_image(ROOT / "logo.png") or get_base64_image(ROOT / "logo.jpg")
ico_uri = get_base64_image(ROOT / "CoreAI.ico")

# --- 3. ربط صندوق البحث بـ session_state عبر query_params ---
# التقاط السؤال من الرابط URL (?user_query=...)
if "user_query" not in st.session_state:
    st.session_state["user_query"] = None

query_params = st.query_params
if "user_query" in query_params:
    st.session_state["user_query"] = query_params["user_query"]
    # مسح المعامل من الرابط لعدم تكرار الطلب عند التحديث
    try:
        st.query_params.clear()
    except:
        # للدعم في الإصدارات الأقدم
        st.experimental_set_query_params()

# --- 4. تحميل وحقن الـ HTML المخصص ---
def load_and_inject_html():
    index_path = ROOT / "index.html"
    if not index_path.exists():
        return "<h1>index.html not found!</h1>"
    
    html_content = index_path.read_text(encoding="utf-8")
    
    # حقن اللوجو والأيقونة المحولة لـ Base64 داخل الكود
    if logo_uri:
        html_content = html_content.replace('src="logo.png"', f'src="{logo_uri}"')
        html_content = html_content.replace('src="logo.jpg"', f'src="{logo_uri}"')
    if ico_uri:
        html_content = html_content.replace('href="CoreAI.ico"', f'href="{ico_uri}"')
    
    # إضافة سكريبت الجافاسكريبت لربط زر الإرسال بالـ URL
    js_bridge = """
    <script>
    function sendToStreamlit() {
        const input = document.getElementById('searchInput');
        if (input.value.trim() !== "") {
            const url = new URL(window.location.href);
            url.searchParams.set('user_query', input.value);
            window.parent.location.href = url.href;
        }
    }
    document.getElementById('submitBtn').onclick = sendToStreamlit;
    document.getElementById('searchInput').onkeypress = function(e){
        if(e.key === 'Enter') sendToStreamlit();
    };
    </script>
    """
    return html_content + js_bridge

# عرض واجهة الـ HTML بارتفاع كامل
from streamlit.components.v1 import html as components_html
components_html(load_and_inject_html(), height=1000, scrolling=False)

# --- 5. محرك المعالجة والرد (بدون st.chat_input) ---
user_input = st.session_state.get("user_query")

if user_input:
    # هنا يوضع منطق الرد الخاص بك (Groq / Memory / etc.)
    with st.container():
        st.markdown(f"### جاري معالجة سؤالك: {user_input}")
        
        # مثال بسيط للرد (يمكنك ربطه بمحرك Groq الخاص بك هنا)
        # st.session_state["user_query"] = None # لتصفير المدخل بعد المعالجة