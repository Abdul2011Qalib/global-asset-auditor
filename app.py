import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Free Asset Auditor", page_icon="🏢")
st.title("🏢 Глобальный Аудитор Активов (Free Expert)")

# Ввод ключа Google API
api_key = st.sidebar.text_input("Введите Google Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    user_input = st.text_area("Введите описание объекта для аудита:")
    
    if st.button("Сформировать Акт"):
        if user_input:
            with st.spinner('Аудит в процессе...'):
                prompt = f"Ты — элитный аудитор. Составь строго юридический акт на основе данных: {user_input}"
                response = model.generate_content(prompt)
                st.markdown(response.text)
                st.download_button("Скачать отчет", response.text, file_name="audit_free.txt")
