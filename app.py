import streamlit as st
import google.generativeai as genai
from fpdf import FPDF

st.set_page_config(page_title="Asset Auditor Pro", page_icon="🏢")
st.title("🏢 Аудитор Активов (Gemini 1.5 Pro)")

api_key = st.sidebar.text_input("Введите Google Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
    # Используем 1.5 Pro для максимального качества юридического текста
    model = genai.GenerativeModel('gemini-1.5-pro')
    
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
                # Для поддержки кириллицы используем стандартный шрифт (в FPDF нужно загрузить TTF, 
                # но для начала используем латинскую транслитерацию или упрощенный подход)
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, txt=report_text.encode('latin-1', 'replace').decode('latin-1'))
                
                st.download_button("Скачать PDF", pdf.output(dest='S'), file_name="Audit_Report.pdf")
