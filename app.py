import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Global Asset Auditor", page_icon="🏢")
st.title("🏢 Глобальный Аудитор Активов (Expert)")

api_key = st.sidebar.text_input("Введите Google Gemini API Key", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3.5-flash')
        
        user_input = st.text_area("Введите описание объекта для аудита:")
        
        if st.button("Сформировать Акт"):
            if user_input:
                with st.spinner('Аудит в процессе...'):
                    # Формируем строгий системный промпт
                    system_instruction = "Ты — элитный аудитор активов. Твоя задача: составить юридически безупречный Акт приема-передачи объекта недвижимости/техники. Стиль: деловой, строгий."
                    response = model.generate_content(system_instruction + " Данные: " + user_input)
                    
                    st.markdown("### Результат аудита:")
                    st.markdown(response.text)
                    st.download_button("Скачать отчет", response.text, file_name="audit_report.txt")
            else:
                st.warning("Пожалуйста, введите данные объекта.")
    except Exception as e:
        st.error(f"Ошибка инициализации Gemini: {e}")
