import streamlit as st
import streamlit.components.v1 as components
from groq import Groq

# إعدادات الصفحة
st.set_page_config(page_title="CORE AI", page_icon="🤖", layout="wide")

# جلب المفتاح الجديد من Secrets
api_key = st.secrets.get("GROQ_API_KEY")

# دمج واجهة HTML الاحترافية الخاصة بك
try:
    with open("index.html", "r", encoding="utf-8") as f:
        html_code = f.read()
    # عرض الواجهة بكامل الشاشة
    components.html(html_code, height=900, scrolling=False)
except FileNotFoundError:
    st.error("❌ ملف index.html غير موجود!")

# البرمجة الخلفية للمحرك (استخدام النموذج الأحدث Llama 3.3)
if api_key:
    client = Groq(api_key=api_key)
    if prompt := st.chat_input("بماذا يمكنني مساعدتك؟"):
        with st.chat_message("assistant"):
            try:
                # تحديث الموديل إلى llama-3.3-70b-versatile لضمان العمل
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                st.markdown(chat_completion.choices[0].message.content)
            except Exception as e:
                st.error(f"عذراً، حدث خطأ: {e}")