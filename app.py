import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os
import requests
import time
from PIL import Image

# ==========================================
# 1. LUXURY ENTERPRISE STYLING (CSS)
# ==========================================
st.set_page_config(
    page_title="Global Asset Auditor | Enterprise Platform", 
    page_icon="🏢", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    .stApp {
        background-color: #0B0C0E;
        color: #E2E8F0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    h1, h2, h3 {
        color: #D4AF37 !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    
    div[data-testid="stExpander"] {
        border: 1px solid #23252D !important;
        background-color: #141519 !important;
        border-radius: 10px !important;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #E6C200 0%, #B8860B 100%);
        color: #0A0A0C !important;
        font-weight: 800 !important;
        font-size: 16px !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 14px 28px !important;
        width: 100%;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 20px rgba(212, 175, 55, 0.25) !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(212, 175, 55, 0.45) !important;
        background: linear-gradient(135deg, #F0D000 0%, #C5930C 100%);
    }
    
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div {
        background-color: #141519 !important;
        color: #FFFFFF !important;
        border: 1px solid #2A2C36 !important;
        border-radius: 8px !important;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #D4AF37 !important;
        box-shadow: 0 0 10px rgba(212, 175, 55, 0.2) !important;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #0E0F12 !important;
        border-right: 1px solid #1E2028;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. НАДЕЖНАЯ ЗАГРУЗКА И НАСТРОЙКА ШРИФТА
# ==========================================
FONT_PATH = "DejaVuSans.ttf"

def get_validated_font():
    """Скачивает шрифт DejaVuSans.ttf с проверкой бинарных сигнатур."""
    if os.path.exists(FONT_PATH) and os.path.getsize(FONT_PATH) > 100000:
        try:
            with open(FONT_PATH, "rb") as f:
                if f.read(4) in [b'\x00\x01\x00\x00', b'OTTO', b'true']:
                    return FONT_PATH
        except Exception:
            pass

    urls = [
        "https://cdn.jsdelivr.net/npm/dejavu-fonts-ttf@2.37.0/ttf/DejaVuSans.ttf",
        "https://raw.githubusercontent.com/fpdf2/fpdf2/master/test/fonts/DejaVuSans.ttf",
        "https://raw.githubusercontent.com/matomo-org/travis-scripts/master/fonts/DejaVuSans.ttf"
    ]
    
    for url in urls:
        try:
            res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code == 200 and len(res.content) > 100000:
                if res.content[:4] in [b'\x00\x01\x00\x00', b'OTTO', b'true']:
                    with open(FONT_PATH, "wb") as f:
                        f.write(res.content)
                    return FONT_PATH
        except Exception:
            continue
    return None

class EnterprisePDF(FPDF):
    def __init__(self, company_name="GLOBAL ASSET AUDITOR", use_dejavu=True):
        super().__init__()
        self.company_name = company_name
        self.use_dejavu = use_dejavu

    def header(self):
        if self.use_dejavu:
            self.set_font("DejaVu", "", 8)
        else:
            self.set_font("Helvetica", "B", 8)
            
        self.set_text_color(160, 160, 160)
        self.cell(0, 5, f"{self.company_name.upper()} | AUDIT & COMPLIANCE REPORT", 0, 1, "R")
        self.set_draw_color(212, 175, 55)
        self.set_line_width(0.6)  # Исправлено имя метода
        self.line(10, 15, 200, 15)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        if self.use_dejavu:
            self.set_font("DejaVu", "", 8)
        else:
            self.set_font("Helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Страница {self.page_no()} | Официальный документ", 0, 0, "C")

# ==========================================
# 3. ИИ-ЯДРО (GEMINI AUDIT ENGINE)
# ==========================================
def run_ai_audit(api_key, prompt, image=None):
    genai.configure(api_key=api_key)
    
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    except Exception as e:
        raise Exception(f"Ошибка соединения с API: {e}")
        
    preferred_models = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-2.0-flash']
    candidates = [m for m in preferred_models if m in available_models] + [m for m in available_models if m not in preferred_models]
    
    last_err = None
    for model_name in candidates:
        try:
            model = genai.GenerativeModel(model_name)
            content = [prompt, image] if image else [prompt]
            response = model.generate_content(content)
            return response.text, model_name.replace("models/", "")
        except Exception as e:
            last_err = e
            time.sleep(1)
            continue
            
    raise last_err if last_err else Exception("Не удалось обратиться к ИИ-моделям.")

# ==========================================
# 4. ИНТЕРФЕЙС И ЛОГИКА
# ==========================================
st.sidebar.markdown("### 🏢 Auditor Control Panel")
api_key = st.sidebar.text_input("Google Gemini API Key", type="password", help="Введите ваш ключ Google AI Studio")

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Параметры отчета")
company_name = st.sidebar.text_input("Название вашей компании:", value="Global Asset Solutions")
inspector_name = st.sidebar.text_input("ФИО Старшего аудитора:", value="Сабит Фатизаде")
doc_lang = st.sidebar.selectbox("Язык акта:", ["Русский", "Азербайджанский (Azərbaycan)", "Английский (English)"])

# Главный заголовок
st.title("🏢 Global Asset Auditor")
st.markdown("##### *Платформа автоматизированного технико-юридического аудита и оценки недвижимости*")
st.markdown("---")

if api_key:
    st.sidebar.success("🔑 API Ключ подключен")
    
    col_main1, col_main2 = st.columns([1, 1])
    
    with col_main1:
        st.markdown("#### 1. Основные сведения")
        object_name = st.text_input("Объект / Адрес:", placeholder="например: БЦ 'Port Baku Tower', офис 1402")
        audit_type = st.selectbox("Цель аудита:", [
            "Прием-передача объекта недвижимости", 
            "Плановая инвентаризация и дефектовка", 
            "Предпродажный экспресс-аудит для инвестора"
        ])
        
    with col_main2:
        st.markdown("#### 2. Визуальный контроль")
        uploaded_image = st.file_uploader("Загрузить фото дефекта (Vision AI):", type=["jpg", "png", "jpeg"])
        image_obj = None
        if uploaded_image:
            image_obj = Image.open(uploaded_image)
            st.image(image_obj, caption="Загруженный снимок для ИИ-анализа", use_container_width=True)

    st.markdown("#### 3. Техническое описание и выявленные замечания")
    user_input = st.text_area("Вводные данные аудитора:", height=130, 
                              placeholder="Перечислите дефекты стен, инженерных сетей, сантехники, показания счетчиков и передаваемое имущество...")

    if st.button("🚀 Сформировать Комплексный Акт"):
        if object_name and user_input:
            with st.spinner('ИИ-Аудитор формирует экспертное юридическое заключение...'):
                
                full_prompt = f"""
Ты — Senior Asset Auditor и международный юрист.
Составь исчерпывающий 'ОФИЦИАЛЬНЫЙ АКТ ТЕХНИЧЕСКОГО АУДИТА И ПРИЕМА-ПЕРЕДАЧИ ОБЪЕКТА'.

ИСПОЛНИТЕЛИ И ОБЪЕКТ:
- Аудиторская компания: '{company_name}'
- Старший аудитор: '{inspector_name}'
- Объект аудита: '{object_name}'
- Категория: {audit_type}
- Язык документа: {doc_lang}
- Детальные вводные: {user_input}
{"- Проанализируй прикрепленное фото, определи дефекты и внеси их в соответствующую секцию." if uploaded_image else ""}

ОБЯЗАТЕЛЬНАЯ СТРУКТУРА ДОКУМЕНТА:
1. ЮРИДИЧЕСКАЯ ПРЕАМБУЛА (Место, дата, стороны, основание проверки).
2. ТЕХНИЧЕСКИЙ ПАСПОРТ И ПРИБОРЫ УЧЕТА (Ключи, карты доступа, показания электро/водосчетчиков).
3. ДЕФЕКТОВОЧНАЯ ВЕДОМОСТЬ (Покатегорийный разбор: Конструкции, HVAC/Инженерия, Сантехника, Отделка. Для каждого дефекта укажи КРИТИЧНОСТЬ: Высокая/Средняя/Низкая и рекомендации).
4. ЮРИДИЧЕСКИЙ АНАЛИЗ И ОЦЕНКА РИСКОВ (Фиксация условия "As Is" / "Как есть", ограничение ответственности).
5. РЕГЛАМЕНТ И СРОКИ УСТРАНЕНИЯ НЕДОСТАТКОВ (Порядок компенсаций и устранения).
6. РЕКВИЗИТЫ И ПОДПИСИ СТОРУН (Графы для подписей Передающей, Принимающей сторон и Инспектора: {inspector_name}).

Стиль: строго официальный, юридически бескомпромиссный. Выдай только готовый документ без вступительных реплик.
"""
                try:
                    report_text, used_model = run_ai_audit(api_key, full_prompt, image_obj)
                    
                    st.success(f"✅ Документ успешно сформирован (Модель: {used_model})")
                    
                    # Предпросмотр
                    with st.expander("📄 Просмотр сформированного документа", expanded=True):
                        st.markdown(report_text)
                    
                    # Сборка PDF
                    font_file = get_validated_font()
                    use_dejavu = font_file is not None
                    
                    pdf = EnterprisePDF(company_name=company_name, use_dejavu=use_dejavu)
                    
                    if use_dejavu:
                        pdf.add_font("DejaVu", "", font_file)
                    
                    pdf.add_page()
                    
                    if use_dejavu:
                        pdf.set_font("DejaVu", size=10)
                    else:
                        pdf.set_font("Helvetica", size=10)
                        
                    pdf.set_text_color(30, 30, 30)
                    
                    # Очистка текста от спецсимволов Markdown
                    clean_text = report_text.replace('**', '').replace('*', '-').replace('#', '')
                    pdf.multi_cell(0, 6, text=clean_text)
                    
                    pdf_data = pdf.output()
                    
                    st.download_button(
                        label="⬇️ Скачать Официальный PDF-Акт",
                        data=bytes(pdf_data),
                        file_name=f"Audit_Act_{object_name[:12].replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
                except Exception as err:
                    if "429" in str(err) or "Quota" in str(err):
                        st.error("⏳ **Превышен лимит запросов API.** Подождите 30 секунд или используйте другой ключ.")
                    else:
                        st.error(f"❌ Ошибка системы: {err}")
        else:
            st.warning("⚠️ Пожалуйста, укажите объект и описание состояния.")
else:
    st.info("👈 Введите ваш Google Gemini API Key в меню слева для активации платформы.")
