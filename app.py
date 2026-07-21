import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, NotFound
from fpdf import FPDF
import os
import requests
import time

# 1. Настройка страницы и премиального дизайна (Gold & Black)
st.set_page_config(page_title="Global Asset Auditor", page_icon="🏢", layout="centered")

st.markdown("""
    <style>
    .stApp {
        background-color: #121212;
        color: #E0E0E0;
    }
    h1, h2, h3 {
        color: #D4AF37 !important;
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

# 2. Загрузка шрифта для поддержки кириллицы в PDF
FONT_PATH = "DejaVuSans.ttf"
@st.cache_resource
def load_font():
    if not os.path.exists(FONT_PATH):
        url = "https://github.com/matomo-org/travis-scripts/raw/master/fonts/DejaVuSans.ttf"
        response = requests.get(url, allow_redirects=True)
        with open(FONT_PATH, 'wb') as file:
            file.write(response.content)
load_font()

# 3. Функция генерации с защитой от пустых ошибок
def generate_report_with_fallback(prompt):
    candidate_models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.5-flash-8b']
    last_exception = None
    
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text, model_name
        except Exception as e:
            last_exception = e
            time.sleep(1)
            continue
            
    if last_exception is None:
        raise RuntimeError("Ни одна из доступных моделей не ответила. Проверьте правильность API ключа.")
    
    raise last_exception

# 4. Боковая панель
st.sidebar.markdown("## ⚙️ Настройки системы")
api_key = st.sidebar.text_input("Введите Google Gemini API Key", type="password")
st.sidebar.markdown("---")

# 5. Основная логика приложения
if api_key:
    try:
        genai.configure(api_key=api_key)
        st.sidebar.success("✅ Ключ API активирован")
        
        st.markdown("---")
        object_name = st.text_input("Название или точный адрес объекта:", placeholder="Например: Офис 150 кв.м., БЦ 'Port Baku'")
        user_input = st.text_area("Детальное описание состояния (дефекты, оборудование, инвентарь):", height=150, 
                                  placeholder="Перечислите все недостатки, состояние потолков, полов, техники...")
        
        if st.button("Сформировать Официальный Акт"):
            if object_name and user_input:
                with st.spinner('ИИ-Аудитор формирует юридический документ...'):
                    
                    prompt = f"""
Ты — ведущий международный эксперт по техническому и юридическому аудиту недвижимости и коммерческих активов (Senior Asset Auditor).

Твоя задача — на основе кратких данных пользователя сформировать исчерпывающий, профессиональный «ОФИЦИАЛЬНЫЙ АКТ ТЕХНИЧЕСКОГО АУДИТА И ПРИЕМА-ПЕРЕДАЧИ ОБЪЕКТА».

ДАННЫЕ ОБЪЕКТА:
- Наименование/Адрес: '{object_name}'
- Фактическое состояние и вводные: {user_input}

ОФОРМИ ДОКУМЕНТ СТРОГО ПО СЛЕДУЮЩИМ РАЗДЕЛАМ:

1. ШАПКА И ЮРИДИЧЕСКАЯ ПРЕАМБУЛА
   - Официальное наименование документа, номер акта, город, дата.
   - Реквизиты Передающей и Принимающей сторон (шаблоны под заполнение ФИО, Должности, Основания полномочий).

2. ТЕХНИЧЕСКИЙ ПАСПОРТ И ИНВЕНТАРИЗАЦИЯ
   - Полное описание объекта (категория, площадь, назначение).
   - Фиксация передаваемых ключей, пультов и карт доступа.
   - Блок фиксации показаний приборов учета (Электроэнергия, Вода, Хладагенты/Газ).

3. ДЕФЕКТОВОЧНАЯ ВЕДОМОСТЬ (ПОСЕКТОРНЫЙ АНАЛИЗ)
   Детализируй состояние по категориям (опиши подробно, расширяя данные пользователя до инженерных терминов):
   - Ограждающие и внутренние конструкции (потолки, стены, напольные покрытия).
   - Инженерные сети (HVAC/кондиционирование, электрика, розетки, освещение, сантехника).
   - Специализированное оборудование и мебель.
   * Для каждого дефекта укажи: Степень критичности (Критическая / Средняя / Низкая) и Рекомендуемое действие.

4. ЮРИДИЧЕСКИЙ АНАЛИЗ И ОЦЕНКА РИСКОВ
   - Разграничение ответственности за выявленные недостатки.
   - Фиксация принципа «как есть» (As Is) для известных дефектов (чтобы исключить иски о «скрытых недостатках»).
   - Ограничение эксплуатации объектов, имеющих критические дефекты.

5. ПОРЯДОК И РЕГЛАМЕНТ УСТРАНЕНИЯ НЕДОСТАТКОВ
   - Четкие варианты урегулирования (Вариант А: устранение силами передающей стороны; Вариант Б: финансовая компенсация/скидка; Вариант В: принятие с дефектами).

6. РЕКВИЗИТЫ, ПОДПИСИ И ПЕЧАТИ СТОРУН
   - Графа подписей с местами для печати (М.П.) и комментариями аудитора.

Стиль документа: строго деловой, академический, юридически выверенный. Выдай сразу готовый документ без вводных фраз.
"""
                    
                    report_text, used_model = generate_report_with_fallback(prompt)
                    
                    st.success(f"✅ Акт успешно сформирован (модель: {used_model})!")
                    
                    with st.expander("📄 Просмотр документа", expanded=True):
                        st.markdown(report_text)
                    
                    # Генерация PDF
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
                    pdf.set_font("DejaVu", size=11)
                    
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
    except ResourceExhausted:
        st.error("⏳ **Превышен лимит запросов Google API.** Подождите 30 секунд и повторите попытку.")
    except Exception as err:
        st.error(f"❌ Ошибка подключения: {err}")
else:
    st.info("👈 Для начала работы введите ваш API ключ в меню слева.")
