import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os
import requests

# 1. Настройка страницы и премиального дизайна (Gold & Black)
st.set_page_config(page_title="Global Asset Auditor", page_icon="🏢", layout="centered")

st.markdown("""
    <style>
    .stApp {
        background-color: #121212;
        color: #E0E0E0;
    }
    h1, h2, h3 {
        color: #D4AF37 !important; /* Золотой цвет для заголовков */
    }
    .stButton>button {
        background-color: #D4AF37;
        color: #121212;
        font-weight: bold;
        border: none;
        border-radius: 5px;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #C5A028;
        color: #000000;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #1E1E1E;
        color: #FFFFFF;
        border: 1px solid #D4AF37;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏢 Global Asset Auditor")
st.markdown("### Профессиональная система оценки и юридической фиксации активов")

# 2. Автоматическая загрузка шрифта для поддержки кириллицы в PDF
FONT_PATH = "DejaVuSans.ttf"
@st.cache_resource
def load_font():
    if not os.path.exists(FONT_PATH):
        url = "https://github.com/matomo-org/travis-scripts/raw/master/fonts/DejaVuSans.ttf"
        response = requests.get(url, allow_redirects=True)
        with open(FONT_PATH, 'wb') as file:
            file.write(response.content)
load_font()

# 3. Боковая панель для настроек
st.sidebar.markdown("## ⚙️ Настройки системы")
api_key = st.sidebar.text_input("Введите Google Gemini API Key", type="password")
st.sidebar.markdown("---")
st.sidebar.info("Система использует модель **Gemini 1.5 Flash** для обеспечения высокой скорости и безупречной юридической логики.")

# 4. Основная логика приложения
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        st.markdown("---")
        object_name = st.text_input("Название или точный адрес объекта:", placeholder="Например: Офис 150 кв.м., БЦ 'Port Baku'")
        user_input = st.text_area("Детальное описание состояния (дефекты, оборудование, инвентарь):", height=150, 
                                  placeholder="Перечислите все недостатки, состояние потолков, полов, техники...")
        
        if st.button("Сформировать Официальный Акт"):
            if object_name and user_input:
                with st.spinner('ИИ-Аудитор формирует юридический документ...'):
                    # Строгий системный промпт
                    prompt = f"""Ты — элитный корпоративный юрист и аудитор активов. 
                    Составь строгий Акт приема-передачи (аудита) для объекта: '{object_name}'.
                    На основе этих данных: {user_input}
                    
                    Структура документа:
                    1. Заголовок (Акт технического аудита и приема-передачи).
                    2. Преамбула (дата, стороны - оставь места для заполнения).
                    3. Детальная таблица/список выявленных дефектов и состояния оборудования.
                    4. Блок "Юридические последствия и риски" (ограничение ответственности передающей стороны).
                    5. Места для подписей (Передал / Принял).
                    
                    Текст должен быть на профессиональном русском языке, без лишних эмоций."""
                    
                    response = model.generate_content(prompt)
                    report_text = response.text
                    
                    st.success("✅ Акт успешно сформирован!")
                    
                    # Вывод на экран
                    with st.expander("📄 Просмотр документа", expanded=True):
                        st.markdown(report_text)
                    
                    # 5. Генерация идеального PDF
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
                    pdf.set_font("DejaVu", size=11)
                    
                    # Очистка текста от Markdown символов (звездочек) для чистого PDF
                    clean_text = report_text.replace('**', '').replace('*', '-')
                    pdf.multi_cell(0, 8, text=clean_text)
                    
                    pdf_bytes = pdf.output()
                    
                    st.download_button(
                        label="⬇️ Скачать документ в формате PDF",
                        data=bytes(pdf_bytes),
                        file_name="Asset_Audit_Report.pdf",
                        mime="application/pdf"
                    )
            else:
                st.warning("⚠️ Пожалуйста, заполните оба поля: название объекта и его описание.")
    except Exception as err:
        st.error(f"❌ Критическая ошибка соединения: {err}. Проверьте правильность API ключа.")
else:
    st.info("👈 Для начала работы введите ваш API ключ в меню слева.")
