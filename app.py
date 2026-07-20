import streamlit as st
import google.generativeai as genai
from fpdf import FPDF

# Конфигурация страницы
st.set_page_config(page_title="Asset Auditor Pro", page_icon="🏢")
st.title("🏢 Азербайджанский Аудитор Активов (Professional)")

api_key = st.sidebar.text_input("Введите Google Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.5-flash')
    
    # Ввод данных
    object_name = st.text_input("Название/Адрес объекта:")
    user_input = st.text_area("Описание состояния актива (дефекты, оборудование):")
    
    if st.button("Сформировать Юридический Акт"):
        if user_input:
            with st.spinner('Подготовка юридического заключения...'):
                prompt = f"""Ты — элитный аудитор недвижимости в Азербайджане. 
                Составь Акт приема-передачи объекта '{object_name}' на основе данных: {user_input}. 
                Документ должен быть на русском языке, содержать таблицу дефектов, 
                ссылки на стандарты управления активами и раздел 'Юридические риски'. 
                Заверши блок строками для подписи сторон."""
                
                response = model.generate_content(prompt)
                report_text = response.text
                
                st.markdown(report_text)
                
                # Сохранение в PDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, report_text.encode('latin-1', 'replace').decode('latin-1'))
                pdf_output = pdf.output(dest='S').encode('latin-1')
                
                st.download_button("Скачать официальный PDF", pdf_output, file_name="Audit_Report.pdf")
        else:
            st.warning("Введите описание объекта.")
