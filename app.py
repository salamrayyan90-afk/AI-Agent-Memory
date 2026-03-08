import streamlit as st
import streamlit.components.v1 as components
from groq import Groq

# --- إعدادات الصفحة ---
st.set_page_config(page_title="CORE AI", page_icon="🤖", layout="wide")

# --- جلب مفتاح API من Secrets ---
api_key = st.secrets.get("GROQ_API_KEY")

# --- عرض واجهة HTML/CSS/JS (الكود الذي أرفقته) ---
# قمنا بدمج كود الـ HTML الخاص بك هنا ليعرضه Streamlit كواجهة أساسية
with open("index.html", "r", encoding="utf-8") as f:
    html_code = f.read()

# عرض الواجهة (مع جعل الطول يغطي الصفحة بالكامل)
components.html(html_code, height=900, scrolling=False)

# --- البرمجة الخلفية (Logic) ---
# ملاحظة: لربط "صندوق البحث" في HTML بمحرك Python، سنحتاج في الخطوات القادمة 
# لاستخدام ميزة st.chat_input لضمان الاستجابة، أو تخصيص الـ Component.

if api_key:
    client = Groq(api_key=api_key)
    # هنا يتم استقبال الأوامر ومعالجتها
else:
    st.error("❌ مفتاح API غير موجود في Secrets!")