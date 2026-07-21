import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os
import requests
import time

# 1. Настройка страницы и стильного интерфейса (Gold & Black)
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

# 2. Безопасная загрузка шрифта для PDF
FONT_PATH = "DejaVuSans.ttf"
@st.cache_resource
def load_font():
    if not os.path.exists(FONT_PATH):
        url = "https://github.com/matomo-org/travis-scripts/raw/master/fonts/DejaVuSans.ttf"
        response = requests.get(url, allow_redirects=True)
        with open(FONT_PATH, 'wb') as file:
            file.write(response.content)
load_font()

# 3. Динамическая генерация: запрашиваем реальный список доступных моделей у Google
def generate_report_safely(api_key, prompt):
    genai.configure(api_key=api_key)
    
    # Запрашиваем у сервера Google список всех моделей, поддерживающих generateContent
    try:
        available_models = [
            m.name for m in genai.list_models() 
            if 'generateContent' in m.supported_generation_methods
        ]
    except Exception as e:
        raise Exception(f"Не удалось получить список моделей: {e}")
        
    if not available_models:
        raise Exception("Для вашего API-ключа не найдено доступных текстовых моделей.")

    # Выставляем приоритет для стандартных стабильных версий
    preferred_order = [
        'models/gemini-1.5-flash',
        'models/gemini-1.5-pro',
        'models/gemini-2.0-flash',
        'models/gemini-1.0-pro'
    ]
    
    # Сортируем: сначала рекомендуемые модели (если есть у ключа), затем остальные доступные
    candidate_models = [m for m in preferred_order if m in available_models]
    for m in available_models:
        if m not in candidate_models:
            candidate_models.append(m)
            
    last_error = None
    
    # Пробуем по очереди только реально существующие модели
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            clean_name = model_name.replace("models/", "")
            return response.text, clean_name
        except Exception as e:
            last_error = e
            time.sleep(1) # Небольшая пауза при переключении
            continue
            
    if last_error:
        raise last_error
    else:
        raise Exception("Не удалось сгенерировать документ ни одной из доступных моделей.")

# 4. Боковая панель
st.sidebar.markdown("## ⚙️ Настройки системы")
api_key = st.sidebar.text_input("Введите Google Gemini API Key", type="password")
st.sidebar.markdown("---")

# 5. Основной интерфейс
if api_key:
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
                try:
                    report_text, used_model = generate_report_safely(api_key, prompt)
                    
                    st.success(f"✅ Акт успешно сформирован (использована модель: {used_model})!")
                    
                    with st.expander("📄 Просмотр документа", expanded=True):
                        st.markdown(report_text)
                    
                    # Генерация PDF
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
                    pdf.set_font("DejaVu", size=11)
                    
                    clean_text = report_text.replace('**', '').replace('*', '-').replace('#', '')
                    pdf.multi_cell(0, 8, text=clean_text)
                    
                    pdf_bytes = pdf.output()
                    
                    st.download_button(
                        label="⬇️ Скачать документ в формате PDF",
                        data=bytes(pdf_bytes),
                        file_name="Asset_Audit_Report.pdf",
                        mime="application/pdf"
                    )
                except Exception as err:
                    if "429" in str(err) or "Quota" in str(err):
                        st.error("⏳ **Достигнут лимит запросов Google API.** Подождите 30–60 секунд или используйте другой API-ключ.")
                    else:
                        st.error(f"❌ Ошибка при генерации: {err}")
        else:
            st.warning("⚠️ Пожалуйста, заполните оба поля: название объекта и его описание.")
else:
    st.info("👈 Для начала работы введите ваш API ключ в меню слева.")
