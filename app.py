import streamlit as st
import pandas as pd
import os
import urllib.request
from datetime import date
from fpdf import FPDF
from PIL import Image

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Global Asset Auditor",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Global Asset Auditor")
st.caption("Платформа автоматизированного технического аудита и формирования актов")

st.divider()

# ---------------------------------------------------------
# 2. SIDEBAR CONFIGURATION
# ---------------------------------------------------------
st.sidebar.header("📋 Параметры акта")

st.sidebar.subheader("🖼️ Логотип компании")
logo_file = st.sidebar.file_uploader("Загрузить логотип (PNG / JPG)", type=["png", "jpg", "jpeg"])

st.sidebar.subheader("📌 Основная информация")
act_num = st.sidebar.text_input("Номер акта", value="GS-BAK-1402")
audit_date = st.sidebar.date_input("Дата аудита", value=date.today())
object_name = st.sidebar.text_input("Объект", value="Офис №1402, Port Baku Tower")
address = st.sidebar.text_input("Адрес", value="г. Баку, пр. Нефтяников 153")

st.sidebar.subheader("👥 Стороны")
party_1 = st.sidebar.text_input("Передающая сторона", value="ООО «Pasha Real Estate»")
party_1_rep = st.sidebar.text_input("Представитель 1", value="Гасанов Р. Э.")

party_2 = st.sidebar.text_input("Принимающая сторона", value="ООО «AzCoin Digital Tech»")
party_2_rep = st.sidebar.text_input("Представитель 2", value="Мамедов Э. И.")

auditor_name = st.sidebar.text_input("Аудитор", value="Сабит Фатизаде")

# ---------------------------------------------------------
# 3. METRICS & INPUTS
# ---------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("⚡ Показания счетчиков")
    power_val = st.number_input("Электричество (кВт·ч)", value=48512)
    cw_val = st.number_input("Холодная вода (м³)", value=412)
    hw_val = st.number_input("Горячая вода (м³)", value=189)

with col2:
    st.subheader("🔑 Средства доступа")
    keys_cnt = st.number_input("Ключи (шт.)", value=4)
    cards_cnt = st.number_input("RFID Карты (шт.)", value=10)
    remotes_cnt = st.number_input("Пульты HVAC (шт.)", value=2)

st.divider()

# ---------------------------------------------------------
# 4. DEFECT TABLE
# ---------------------------------------------------------
st.subheader("🛠️ Дефектовочная ведомость")

default_defects = [
    {"Категория": "Отделка", "Описание": "Микротрещины на гипсокартоне (ресепшн)", "Критичность": "Низкая", "Смета (AZN)": 150.0},
    {"Категория": "Отделка", "Описание": "Следы протечек на потолке Armstrong", "Критичность": "Средняя", "Смета (AZN)": 350.0},
    {"Категория": "HVAC", "Описание": "Повышенный шум и вибрация фанкойла", "Критичность": "Средняя", "Смета (AZN)": 300.0},
    {"Категория": "Электрика", "Описание": "Отсутствие маркировки автоматов в ЩО №2", "Критичность": "Высокая", "Смета (AZN)": 120.0},
    {"Категория": "Сантехника", "Описание": "Люфт и ослабление фиксации смесителя", "Критичность": "Низкая", "Смета (AZN)": 90.0},
]

df_defects = pd.DataFrame(default_defects)
edited_df = st.data_editor(df_defects, num_rows="dynamic", use_container_width=True)

total_cost = edited_df["Смета (AZN)"].sum()
st.metric(label="Итоговая смета устранения дефектов", value=f"{total_cost:,.2f} AZN")

st.divider()

# ---------------------------------------------------------
# 5. PDF GENERATION WITH LOGO SUPPORT
# ---------------------------------------------------------
def download_font():
    font_path = "DejaVuSans.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf"
        try:
            urllib.request.urlretrieve(url, font_path)
        except Exception:
            pass
    return font_path

def create_pdf(logo):
    font_path = download_font()
    pdf = FPDF()
    pdf.add_page()
    
    # Font setup for UTF-8 Support
    if os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", "", 10)
    else:
        pdf.set_font("Arial", "", 10)

    # Insert Header Logo if uploaded
    if logo is not None:
        try:
            img = Image.open(logo)
            temp_path = "temp_logo.png"
            img.convert("RGB").save(temp_path)
            pdf.image(temp_path, x=155, y=10, w=40)
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass

    # Title Section
    pdf.set_font_size(14)
    pdf.cell(0, 10, f"АКТ ТЕХНИЧЕСКОГО АУДИТА № {act_num}", ln=True, align="L")
    pdf.set_font_size(9)
    pdf.cell(0, 5, f"Дата: {audit_date.strftime('%d.%m.%Y')} | Объект: {object_name}", ln=True, align="L")
    pdf.ln(10)

    # Parties
    pdf.set_font_size(10)
    pdf.cell(0, 6, "1. СТОРОНЫ И КОМИССИЯ", ln=True)
    pdf.cell(0, 5, f"• Передающая сторона: {party_1} ({party_1_rep})", ln=True)
    pdf.cell(0, 5, f"• Принимающая сторона: {party_2} ({party_2_rep})", ln=True)
    pdf.cell(0, 5, f"• Эксперт-аудитор: {auditor_name}", ln=True)
    pdf.ln(5)

    # Resources
    pdf.cell(0, 6, "2. РЕСУРСНЫЕ ПОКАЗАТЕЛИ И СКУД", ln=True)
    pdf.cell(0, 5, f"• Электроэнергия: {power_val} кВт·ч | ХВ: {cw_val} м³ | ГВ: {hw_val} м³", ln=True)
    pdf.cell(0, 5, f"• Ключи: {keys_cnt} шт. | RFID-карты: {cards_cnt} шт. | Пульты HVAC: {remotes_cnt} шт.", ln=True)
    pdf.ln(5)

    # Table
    pdf.cell(0, 6, "3. ДЕФЕКТОВОЧНАЯ ВЕДОМОСТЬ", ln=True)
    pdf.ln(2)

    # Table Header
    pdf.cell(35, 7, "Категория", border=1)
    pdf.cell(95, 7, "Описание", border=1)
    pdf.cell(30, 7, "Критичность", border=1)
    pdf.cell(30, 7, "Смета (AZN)", border=1, ln=True)

    # Table Body
    for _, row in edited_df.iterrows():
        pdf.cell(35, 6, str(row['Категория']), border=1)
        pdf.cell(95, 6, str(row['Описание'])[:50], border=1)
        pdf.cell(30, 6, str(row['Критичность']), border=1)
        pdf.cell(30, 6, f"{row['Смета (AZN)']:,.2f}", border=1, ln=True)

    pdf.cell(160, 7, "ИТОГО СМЕТА:", border=1, align="R")
    pdf.cell(30, 7, f"{total_cost:,.2f} AZN", border=1, ln=True)

    pdf.ln(12)
    pdf.cell(0, 5, "ПОДПИСИ СТОРОН:", ln=True)
    pdf.ln(8)
    pdf.cell(60, 5, "Аудитор: _____________", ln=False)
    pdf.cell(60, 5, "Передающая: _____________", ln=False)
    pdf.cell(60, 5, "Принимающая: _____________", ln=True)

    return bytes(pdf.output())

# ---------------------------------------------------------
# 6. DOWNLOAD BUTTON
# ---------------------------------------------------------
st.subheader("🚀 Запуск и Скачивание")
if st.button("📄 Сформировать PDF-Акт", type="primary"):
    with st.spinner("Генерация документа..."):
        pdf_bytes = create_pdf(logo_file)
        st.download_button(
            label="📥 Скачать готовый Акт (PDF)",
            data=pdf_bytes,
            file_name=f"Audit_Act_{act_num}.pdf",
            mime="application/pdf"
        )
        st.success("Документ успешно сформирован!")
