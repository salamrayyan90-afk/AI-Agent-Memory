import streamlit as st
from groq import Groq
import os

# --- إعدادات الصفحة والجماليات ---
st.set_page_config(page_title="CORE AI - Pro", page_icon="🤖", layout="wide")

# تصميم CSS مخصص لجعل الواجهة فخمة
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007bff; color: white; }
    .stTextInput>div>div>input { border-radius: 10px; }
    h1 { color: #007bff; text-align: center; font-family: 'Arial'; }
    </style>
    """, unsafe_allow_config=True)

# --- جلب مفتاح API من Secrets ---
# ملاحظة: Streamlit يقرأها تلقائياً من خانة Secrets التي ملأناها
api_key = st.secrets.get("GROQ_API_KEY")

if not api_key:
    st.error("❌ مفتاح API غير موجود! تأكد من وضعه في Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# --- واجهة المستخدم (UI) ---
st.title("🤖 CORE AI | المحرك الذكي")
st.markdown("---")

# القائمة الجانبية (Sidebar) للأيقونات والإعدادات
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=100) # أيقونة ذكاء اصطناعي
    st.header("⚙️ الإعدادات")
    st.info("تم الربط بنجاح مع سيرفرات Groq السحابية.")
    
    st.markdown("---")
    st.write("🌐 **تصفح المواقع (قريباً)**")
    url_input = st.text_input("أدخل رابط الموقع للتحليل:")
    if st.button("تحليل الموقع 🔍"):
        st.warning("جاري تفعيل هذه الميزة في التحديث القادم...")

# --- شاشة الدردشة الرئيسية ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# عرض الرسائل السابقة
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# إدخال المستخدم
if prompt := st.chat_input("بماذا يمكنني مساعدتك اليوم؟"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # جلب رد الذكاء الاصطناعي
    with st.chat_message("assistant"):
        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            )
            full_response = response.choices[0].message.content
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"حدث خطأ في الاتصال: {e}")