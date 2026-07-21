import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os
import requests
import time
from PIL import Image

# ==========================================
# 1. КОНФИГУРАЦИЯ И ПРЕМИУМ-ДИЗАЙН (CSS)
# ==========================================
st.set_page_config(
    page_title="Global Asset Auditor | B2B Platform", 
    page_icon="🏢", 
    layout="centered"
)

# Скрытие служебных элементов Streamlit и премиум кастомизация
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background-color: #0E0E10;
        color: #E2E8F0;
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        color: #D4AF37 !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    
    div[data-testid="stExpander"] {
        border: 1px solid #2D2D35 !important;
        background-color: #16161A !important;
        border-radius: 8px !important;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #D4AF37 0%, #AA7C11 100%);
        color: #000000;
        font-weight: bold;
        border: none;
        border-radius: 6px;
        padding: 12px 24px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.2);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(212, 175, 55, 0.4);
        color: #000000;
    }
    
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div {
        background-color: #16161A !important;
        color: #FFFFFF !important;
        border: 1px solid #2D2D35 !important;
        border-radius: 6px !important;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #D4AF37 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ПРОВЕРКА И ЗАГРУЗКА ВАЛИДНОГО TTF-ШРИФТА
# ==========================================
FONT_PATH = "DejaVuSans.ttf"

def ensure_valid_font():
    """Проверяет заголовок файла на корректный сигнатурный байт TTF/OTF. 
    Если файл поврежден или является HTML, удаляет и скачивает заново."""
    
    def is_ttf(path):
        if not os.path.exists(path):
            return False
        try:
            with open(path, "rb") as f:
                header = f.read(4)
                # Подлинные TTF/OTF начинаются с \x00\x01\x00\x00 или b'OTTO' или b'true'
                return header in [b'\x00\x01\x00\x00', b'OTTO', b'true']
        except Exception:
            return False

    if not is_ttf(FONT_PATH):
        if os.path.exists(FONT_PATH):
            try:
                os.remove(FONT_PATH)
            except Exception:
                pass
                
        # Список надежных прямых источников
        urls = [
            "https://github.com/google/fonts/raw/main/ofl/dejavusans/DejaVuSans.ttf",
            "https://cdn.jsdelivr.net/gh/dejavu-fonts/dejavu-fonts@master/ttf/DejaVuSans.ttf",
            "https://raw.githubusercontent.com/dejavu-fonts/dejavu-fonts/master/ttf/DejaVuSans.ttf"
        ]
        
        for url in urls:
            try:
                res = requests.get(url, timeout=10, allow_redirects=True)
                if res.status_code == 200 and res.content[:4] in [b'\x00\x01\x00\x00', b'OTTO', b'true']:
                    with open(FONT_PATH, "wb") as f:
                        f.write(res.content)
                    break
            except Exception:
                continue

ensure_valid_font()

# Класс PDF с оформлением
class ProfessionalPDF(FPDF):
    def header(self):
        ensure_valid_font()
        self.add_font("DejaVu", "", FONT_PATH, uni=True)
        self.set_font("DejaVu", "", 9)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, "GLOBAL ASSET AUDITOR | OFFICIAL AUDIT REPORT", 0, 1, "R")
        self.set_draw_color(212, 175, 55)
        self.set_linewidth(0.5)
        self.line(10, 15, 200, 15)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        ensure_valid_font()
        self.add_font("DejaVu", "", FONT_PATH, uni=True)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Страница {self.page_no()}", 0, 0, "C")

# ==========================================
# 3. ИИ-ЯДРО С АВТОПЕРЕКЛЮЧЕНИЕМ И ПОДДЕРЖКОЙ ФОТО
# ==========================================
def generate_audit_report(api_key, prompt, image=None):
    genai.configure(api_key=api_key)
    
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    except Exception as e:
        raise Exception(f"Ошибка получения моделей: {e}")
        
    preferred_order = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-2.0-flash']
    candidate_models = [m for m in preferred_order if m in available_models] + [m for m in available_models if m not in preferred_order]
    
    last_error = None
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(model_name)
            contents = [prompt, image] if image else [prompt]
            response = model.generate_content(contents)
            return response.text, model_name.replace("models/", "")
        except Exception as e:
            last_error = e
            time.sleep(1)
            continue
            
    raise last_error if last_error else Exception("Все модели недоступны.")

# ==========================================
# 4. ИНТЕРФЕЙС ПЛАТФОРМЫ
# ==========================================
st.title("🏢 Global Asset Auditor")
st.markdown("### Корпоративная система технического и юридического аудита активов")

st.sidebar.markdown("## ⚙️ Панель управления")
api_key = st.sidebar.text_input("Введите Google Gemini API Key", type="password")
doc_lang = st.sidebar.selectbox("Язык итогового документа:", ["Русский", "Азербайджанский (Azərbaycan)", "Английский (English)"])
st.sidebar.markdown("---")

if api_key:
    st.sidebar.success("✅ Лицензия активна")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        object_name = st.text_input("Название / Адрес объекта:", placeholder="Например: Офисный блок 4A, Port Baku Tower")
    with col2:
        audit_type = st.selectbox("Тип аудита:", ["Прием-передача объекта", "Инвентаризация и дефектовка", "Экспресс-оценка для инвестора"])

    user_input = st.text_area("Детальное описание состояния и дефектов:", height=120, 
                              placeholder="Опишите состояние стен, инженерных сетей, сантехники, мебели...")
    
    uploaded_image = st.file_uploader("📷 Прикрепить фото объекта (необязательно):", type=["jpg", "png", "jpeg"])
    image_obj = None
    if uploaded_image:
        image_obj = Image.open(uploaded_image)
        st.image(image_obj, caption="Загруженное фото дефекта/объекта", use_container_width=True)

    if st.button("🚀 Сформировать Официальный Акт"):
        if object_name and user_input:
            with st.spinner('ИИ-Аудитор проводит комплексный анализ и верстку акта...'):
                
                full_prompt = f"""
Ты — Senior Asset Auditor и международный юрист по недвижимости.
Составь 'ОФИЦИАЛЬНЫЙ АКТ ТЕХНИЧЕСКОГО АУДИТА И ПРИЕМА-ПЕРЕДАЧИ ОБЪЕКТА'.

ДАННЫЕ ОБЪЕКТА:
- Объект: '{object_name}'
- Тип аудита: {audit_type}
- Язык документа: {doc_lang}
- Описание состояния: {user_input}
{"- Также проанализируй прикрепленное изображение и внеси выявленные на нем визуальные дефекты в дефектовочную ведомость." if uploaded_image else ""}

СТРУКТУРА ДОКУМЕНТА:
1. Юридическая преамбула (Стороны, Дата, Основания).
2. Технический паспорт и инвентаризационный список.
3. Дефектовочная ведомость (Степень критичности: Высокая/Средняя/Низкая + инженерное решение).
4. Раздел "Юридические риски и разграничение ответственности" (As Is).
5. Регламент устранения недостатков.
6. Блок подписей и печатей сторон.

Стиль: строго академический, юридически выверенный, без вводных приветствий.
"""
                try:
                    report_text, model_used = generate_audit_report(api_key, full_prompt, image_obj)
                    
                    st.success(f"✅ Акт успешно сформирован (Модель: {model_used})")
                    
                    with st.expander("📄 Предварительный просмотр документа", expanded=True):
                        st.markdown(report_text)
                    
                    # Генерация PDF
                    ensure_valid_font()
                    pdf = ProfessionalPDF()
                    pdf.add_page()
                    pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
                    pdf.set_font("DejaVu", size=10)
                    pdf.set_text_color(30, 30, 30)
                    
                    clean_text = report_text.replace('**', '').replace('*', '-').replace('#', '')
                    pdf.multi_cell(0, 6, text=clean_text)
                    
                    pdf_bytes = pdf.output()
                    
                    st.download_button(
                        label="⬇️ Скачать официальный PDF-отчет",
                        data=bytes(pdf_bytes),
                        file_name=f"Audit_Report_{object_name[:15]}.pdf",
                        mime="application/pdf"
                    )
                except Exception as err:
                    if "429" in str(err) or "Quota" in str(err):
                        st.error("⏳ Достигнут лимит запросов API. Подождите 30 секунд.")
                    else:
                        st.error(f"❌ Ошибка генерации: {err}")
        else:
            st.warning("⚠️ Пожалуйста, заполните наименование и описание объекта.")
else:
    st.info("👈 Для доступа к системе введите ваш API-ключ в левом меню.")
