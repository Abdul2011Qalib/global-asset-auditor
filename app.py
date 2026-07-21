import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os
import requests
import time
import hashlib
import datetime
from PIL import Image
import io

# Опциональный импорт для Word и QR-кодов
try:
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import qrcode
    HAS_QR = True
except ImportError:
    HAS_QR = False

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

# ==========================================
# 3. ENTERPRISE PDF & DOCX GENERATORS
# ==========================================
def generate_qr_code(data_str):
    if not HAS_QR:
        return None
    qr = qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(data_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    path = "temp_qr.png"
    img.save(path)
    return path

class UltraPDF(FPDF):
    def __init__(self, company_name="GLOBAL ASSET AUDITOR", doc_hash="", use_dejavu=True):
        super().__init__()
        self.company_name = company_name
        self.doc_hash = doc_hash
        self.use_dejavu = use_dejavu

    def header(self):
        if self.use_dejavu:
            self.set_font("DejaVu", "", 8)
        else:
            self.set_font("Helvetica", "B", 8)
            
        self.set_text_color(140, 140, 140)
        self.cell(0, 5, f"{self.company_name.upper()} | OFFICIAL VERIFIED REPORT", 0, 1, "R")
        self.set_draw_color(212, 175, 55)
        self.set_line_width(0.6)
        self.line(10, 15, 200, 15)
        self.ln(6)

    def footer(self):
        self.set_y(-18)
        if self.use_dejavu:
            self.set_font("DejaVu", "", 7)
        else:
            self.set_font("Helvetica", "", 7)
        self.set_text_color(120, 120, 120)
        
        # Информационная строка подписи
        self.cell(130, 4, f"Страница {self.page_no()} | Хэш подлинности: {self.doc_hash[:24]}...", 0, 0, "L")
        self.cell(60, 4, "Защищено стандартом SHA-256", 0, 1, "R")


def build_docx_report(company_name, inspector_name, object_name, report_text, image_path=None):
    if not HAS_DOCX:
        return None
    
    doc = docx.Document()
    
    # Заголовок
    p = doc.add_paragraph()
    run = p.add_run(f"{company_name.upper()} — ОФИЦИАЛЬНЫЙ АКТ")
    run.font.bold = True
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor(184, 134, 11)
    
    doc.add_paragraph(f"Инспектор: {inspector_name} | Объект: {object_name}")
    doc.add_paragraph("="*50)
    
    # Текст
    for line in report_text.split('\n'):
        if line.startswith('#'):
            clean_line = line.replace('#', '').strip()
            p = doc.add_paragraph()
            r = p.add_run(clean_line)
            r.font.bold = True
            r.font.size = Pt(13)
            r.font.color.rgb = RGBColor(184, 134, 11)
        else:
            doc.add_paragraph(line)
            
    # Приложение фото
    if image_path and os.path.exists(image_path):
        doc.add_page_break()
        doc.add_heading('ПРИЛОЖЕНИЕ № 1: ФОТОФИКСАЦИЯ ДЕФЕКТОВ', level=1)
        doc.add_picture(image_path, width=Inches(5.5))
        
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# ==========================================
# 4. ИИ-ЯДРО (GEMINI AUDIT ENGINE)
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
# 5. ИНТЕРФЕЙС И ЛОГИКА
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
        object_name = st.text_input("Объект / Адрес:", value="Офис №1402, БЦ 'Port Baku Tower', г. Баку")
        audit_type = st.selectbox("Цель аудита:", [
            "Прием-передача объекта недвижимости", 
            "Плановая инвентаризация и дефектовка", 
            "Предпродажный экспресс-аудит для инвестора"
        ])
        
    with col_main2:
        st.markdown("#### 2. Визуальный контроль (Vision AI)")
        uploaded_image = st.file_uploader("Загрузить фото дефекта:", type=["jpg", "png", "jpeg"])
        image_obj = None
        temp_img_path = None
        if uploaded_image:
            image_obj = Image.open(uploaded_image)
            temp_img_path = "temp_audit_defect.jpg"
            image_obj.convert('RGB').save(temp_img_path)
            st.image(image_obj, caption="Загруженный снимок для ИИ-анализа и вшивания в PDF", use_container_width=True)

    st.markdown("#### 3. Техническое описание и выявленные замечания")
    user_input = st.text_area("Вводные данные аудитора:", height=130, 
                              value="Отделка: Микротрещины на гипсокартоне (ресепшн), следы протечек на Armstrong (сектор B), царапины на ламинате. HVAC: Шум кондиционера, требуется чистка фильтров. Электрика: Щит №2 без маркировки. Сантехника: Шатается смеситель. Ресурсы: Э/Э 48512 кВт·ч, ХВ 412 м³, ГВ 189 м³. Ключи: 4 главных, 10 RFID карт, 2 пульта климата.")

    if st.button("🚀 Сформировать Комплексный Акт (Ultra Version)"):
        if object_name and user_input:
            with st.spinner('ИИ-Аудитор формирует юридический Акт и верстает документы...'):
                
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
6. РЕКВИЗИТЫ И ПОДПИСИ СТОРОН (Графы для подписей Передающей, Принимающей сторон и Инспектора: {inspector_name}).

Стиль: строго официальный, юридически бескомпромиссный. Выдай готовый документ в формате Markdown без вступительных реплик.
"""
                try:
                    report_text, used_model = run_ai_audit(api_key, full_prompt, image_obj)
                    
                    st.success(f"✅ Документ успешно сформирован (Модель: {used_model})")
                    
                    # Предпросмотр
                    with st.expander("📄 Просмотр сформированного документа", expanded=True):
                        st.markdown(report_text)
                    
                    # Расчет хэша подлинности
                    doc_hash = hashlib.sha256(report_text.encode('utf-8')).hexdigest()
                    qr_path = generate_qr_code(f"VERIFIED AUDIT ACT\nHash: {doc_hash}\nAuditor: {inspector_name}")
                    
                    # Сборка PDF
                    font_file = get_validated_font()
                    use_dejavu = font_file is not None
                    
                    pdf = UltraPDF(company_name=company_name, doc_hash=doc_hash, use_dejavu=use_dejavu)
                    
                    if use_dejavu:
                        pdf.add_font("DejaVu", "", font_file)
                    
                    pdf.add_page()
                    
                    if use_dejavu:
                        pdf.set_font("DejaVu", size=10)
                    else:
                        pdf.set_font("Helvetica", size=10)
                        
                    pdf.set_text_color(30, 30, 30)
                    
                    # Запись очищенного текста
                    clean_text = report_text.replace('**', '').replace('*', '-').replace('#', '')
                    pdf.multi_cell(0, 6, text=clean_text)
                    
                    # Вшивание фото дефекта в PDF (Приложение №1)
                    if temp_img_path and os.path.exists(temp_img_path):
                        pdf.add_page()
                        if use_dejavu:
                            pdf.set_font("DejaVu", size=12)
                        else:
                            pdf.set_font("Helvetica", "B", 12)
                        pdf.set_text_color(184, 134, 11)
                        pdf.cell(0, 10, "ПРИЛОЖЕНИЕ № 1: ФОТОФИКСАЦИЯ ДЕФЕКТОВ ОБЪЕКТА", 0, 1, "L")
                        pdf.ln(5)
                        pdf.image(temp_img_path, x=15, y=30, w=180)
                        
                    # Вшивание QR-кода на последнюю страницу
                    if qr_path and os.path.exists(qr_path):
                        pdf.image(qr_path, x=165, y=240, w=30)
                    
                    pdf_data = pdf.output()
                    
                    # Генерация Word
                    docx_data = build_docx_report(company_name, inspector_name, object_name, report_text, temp_img_path)
                    
                    # Скачивание
                    st.markdown("### 📥 Скачать официальный пакет документов:")
                    col_dl1, col_dl2 = st.columns(2)
                    
                    with col_dl1:
                        st.download_button(
                            label="⬇️ Скачать Официальный PDF-Акт (с QR и фото)",
                            data=bytes(pdf_data),
                            file_name=f"Audit_Act_{object_name[:12].replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
                        
                    with col_dl2:
                        if docx_data:
                            st.download_button(
                                label="📝 Скачать Редактируемый Word (.docx)",
                                data=docx_data,
                                file_name=f"Audit_Act_{object_name[:12].replace(' ', '_')}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                        else:
                            st.info("💡 Для экспорта в Word установите `python-docx`")
                            
                except Exception as err:
                    if "429" in str(err) or "Quota" in str(err):
                        st.error("⏳ **Превышен лимит запросов API.** Подождите 30 секунд или используйте другой ключ.")
                    else:
                        st.error(f"❌ Ошибка системы: {err}")
        else:
            st.warning("⚠️ Пожалуйста, укажите объект и описание состояния.")
else:
    st.info("👈 Введите ваш Google Gemini API Key в меню слева для активации платформы.")
