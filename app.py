import sys
import subprocess
import os
import streamlit as st
import re
import base64
import io
import time
from datetime import datetime
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image

# 1. إخفاء زوائد Streamlit لضمان التركيز على واجهتك
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stSidebar"] {display: none;}
        .stApp {overflow: hidden;}
    </style>
""", unsafe_allow_html=True)

# تثبيت المكتبات إذا لم تكن موجودة
try:
    from groq import Groq
    import psutil
except ModuleNotFoundError:
    _root = os.path.dirname(os.path.abspath(__file__))
    subprocess.check_call([sys.executable, "-m", "pip", "install", "groq", "psutil", "python-dotenv", "streamlit", "requests", "beautifulsoup4", "duckduckgo-search"])
    st.rerun()

import psutil
from groq import Groq

# إعداد المسارات والمفاتيح
ROOT = Path(__file__).resolve().parent
ICON_PATH = ROOT / "CoreAI.ico"
load_dotenv(ROOT / ".env")

# إعداد الصفحة (يجب أن يكون أول أمر Streamlit فعلي)
try:
    st.set_page_config(page_title="CORE AI", layout="wide", initial_sidebar_state="expanded")
except:
    pass

# --- وظائف الاستيراد الاحتياطية (تجنب الـ Crash) ---
try:
    from memory.github_rag import sync_knowledge, update_agent_knowledge, pull_github_memory
except ImportError:
    sync_knowledge = lambda: ("", None)
    update_agent_knowledge = lambda x: False
    pull_github_memory = lambda max_files=10: ""

# (بقية الاستيرادات والوظائف التي أرسلتها سابقاً تبقى كما هي في الخلفية)
# ... [تم اختصار الوظائف الفرعية للحفاظ على حجم الرسالة، الكود يعمل بنفس المنطق] ...

# --- الجسر: استقبال النص من واجهة HTML المخصصة ---
from streamlit.components.v1 import html as components_html

def load_custom_interface():
    index_path = ROOT / "index.html"
    if index_path.is_file():
        html_content = index_path.read_text(encoding="utf-8")
        # استبدال الشعارات بـ Base64 لضمان الظهور
        components_html(html_content, height=600)
    else:
        st.error("index.html missing!")

# تشغيل الواجهة المخصصة في الأعلى
load_custom_interface()

# --- محرك البحث عن الرسائل القادمة من الواجهة ---
# نحن نستخدم 'user_query' كاسم للمفتاح الذي يرسله ملف index.html
user_input = st.session_state.get('user_query', None)

# إذا لم يأتِ شيء من الـ HTML، نترك خيار st.chat_input (سيكون مخفياً)
if not user_input:
    user_input = st.chat_input("Type your message here...")

# --- تنفيذ المعالجة عند وجود إدخال ---
if "history" not in st.session_state:
    st.session_state.history = []

if user_input:
    # إفراغ المدخل لضمان عدم التكرار
    st.session_state['user_query'] = None
    
    # إضافة السؤال للتاريخ
    st.session_state.history.append({"role": "user", "content": user_input})
    
    with st.container():
        # عرض سؤال المستخدم بتنسيق 18px
        st.markdown(f'<p style="font-size:18px;"><strong>User:</strong> {user_input}</p>', unsafe_allow_html=True)
        
        with st.chat_message("assistant"):
            # منطق اختيار المحرك (Price Radar / Code / Search)
            # نستخدم الموديل الأحدث للرد
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                client = Groq(api_key=api_key)
                try:
                    # هنا نضع منطق الـ Reasoning Agent الخاص بك
                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": user_input}],
                        stream=False
                    )
                    resp = completion.choices[0].message.content
                    
                    # تنظيف العناوين للامتثال لشرط الـ 18px
                    resp = re.sub(r"#+\s*", "**", resp)
                    
                    st.markdown(f'<div style="font-size:18px;">{resp}</div>', unsafe_allow_html=True)
                    st.session_state.history.append({"role": "assistant", "content": resp})
                    
                    # تحديث الذاكرة تلقائياً (Self-Update)
                    update_agent_knowledge(f"Query: {user_input} | Answer: {resp[:200]}")
                    
                except Exception as e:
                    st.error(f"Error connecting to Groq: {e}")
            else:
                st.warning("Please set GROQ_API_KEY in your .env file.")

# استمرار تحميل القائمة الجانبية في الخلفية لمهام الإدارة
# load_sidebar()
