import streamlit as st
import google.generativeai as genai
from fpdf import FPDF

st.set_page_config(page_title="Asset Auditor Pro", page_icon="🏢")
st.title("🏢 Аудитор Активов (Professional)")

api_key = st.sidebar.text_input("Введите Google Gemini API Key", type="password")

if api_key:
    try:
        # Сначала настраиваем ключ
        genai.configure(api_key=api_key)
        
        # Используем проверенную стабильную модель напрямую, без динамического списка
        model = genai.GenerativeModel('gemini-1.5-flash')
        st.sidebar.success("Модель успешно подключена!")
        
        object_name = st.text_input("Название/Адрес объекта:")
        user_input = st.text_area("Описание состояния актива (дефекты, оборудование):")
        
        if st.button("Сформировать Юридический Акт"):
            if user_input:
                with st.spinner('Аудит в процессе...'):
                    prompt = f"""Ты — элитный аудитор недвижимости. Составь Акт приема-передачи объекта '{object_name}'.
                    Основа: {user_input}.
                    Требования:
                    1. Строгий деловой стиль.
                    2. Таблица с дефектами.
                    3. Раздел 'Юридические риски'.
                    4. Места для подписей сторон.
                    Выдай только текст документа."""
                    
                    response = model.generate_content(prompt)
                    report_text = response.text
                    
                    st.markdown(report_text)
                    
                    # Генерация PDF
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    pdf.multi_cell(0, 10, txt=report_text.encode('latin-1', 'replace').decode('latin-1'))
                    
                    st.download_button("Скачать PDF", pdf.output(dest='S'), file_name="Audit_Report.pdf")
            else:
                st.warning("Введите описание состояния актива.")
                
    except Exception as err:
        st.error(f"Произошла ошибка: {err}")
else:
    st.info("Пожалуйста, введите ваш Google Gemini API Key в боковой панели слева.")
