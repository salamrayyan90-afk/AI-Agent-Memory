import streamlit as st
import os
from groq import Groq

# 1. إعداد الصفحة
st.set_page_config(page_title="CORE AI - Connection Test", page_icon="⚡")

st.title("🛠️ فحص اتصالات CORE AI")
st.markdown("---")

# --- الاختبار الأول: فحص المكتبات ---
st.subheader("1. فحص المكتبات والبيئة")
try:
    import requests
    from bs4 import BeautifulSoup
    st.success("✅ المكتبات الأساسية (Streamlit, Groq, BeautifulSoup) مثبتة وجاهزة.")
except ImportError as e:
    st.error(f"❌ هناك مكتبة ناقصة: {e}")

# --- الاختبار الثاني: فحص مفتاح الـ API (Secrets) ---
st.subheader("2. فحص مفتاح الأمان (Secrets)")
api_key = st.secrets.get("GROQ_API_KEY")

if api_key:
    st.success("✅ تم العثور على مفتاح GROQ_API_KEY في الإعدادات المتقدمة.")
    # إظهار أول 5 رموز فقط للتأكيد دون كشف المفتاح كاملاً
    st.code(f"المفتاح يبدأ بـ: {api_key[:7]}...", language="text")
else:
    st.error("❌ المفتاح غير موجود! تأكد من وضعه في Advanced Settings > Secrets بصيغة TOML.")

# --- الاختبار الثالث: فحص الاتصال بـ Groq (عقل الذكاء الاصطناعي) ---
st.subheader("3. فحص الاتصال بالسيرفر (Groq API)")
if api_key:
    try:
        client = Groq(api_key=api_key)
        # إرسال رسالة تجريبية صغيرة جداً
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": "test"}],
        )
        st.success("✅ تم الاتصال بسيرفر Groq بنجاح واستلام رد!")
    except Exception as e:
        st.error(f"❌ فشل الاتصال بسيرفر Groq. السبب: {e}")
else:
    st.warning("⚠️ لا يمكن فحص الاتصال بدون المفتاح.")

# --- الاختبار الرابع: فحص ملف الواجهة ---
st.subheader("4. فحص ملفات التصميم")
if os.path.exists("index.html"):
    st.success("✅ ملف index.html موجود وجاهز للعرض.")
else:
    st.error("❌ ملف index.html مفقود من المجلد الرئيسي!")

st.markdown("---")
st.info("إذا كانت جميع العلامات أعلاه خضراء ✅، فموقعك سيعمل فوراً عند فتحه.")