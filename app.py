import streamlit as st
import pandas as pd
import io
import base64
from datetime import date
from weasyprint import HTML

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION & CUSTOM STYLES
# ---------------------------------------------------------
st.set_page_config(
    page_title="Global Asset Auditor | Corporate Platform",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Enterprise CSS
st.markdown("""
<style>
    /* Global Reset & Typography */
    .main { background-color: #0d1117; color: #c9d1d9; }
    
    /* Executive Card Styling */
    .metric-card {
        background: linear-gradient(135deg, #161b22 0%, #21262d 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.4);
        margin-bottom: 20px;
    }
    .metric-title { font-size: 0.85rem; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #f0f6fc; margin-top: 5px; }
    
    /* Custom Badges */
    .badge-low { background-color: #238636; color: white; padding: 3px 8px; border-radius: 6px; font-size: 0.8rem; }
    .badge-mid { background-color: #d29922; color: white; padding: 3px 8px; border-radius: 6px; font-size: 0.8rem; }
    .badge-high { background-color: #da3633; color: white; padding: 3px 8px; border-radius: 6px; font-size: 0.8rem; }
    
    /* Header Container */
    .hero-header {
        border-bottom: 1px solid #30363d;
        padding-bottom: 15px;
        margin-bottom: 25px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. SIDEBAR - CONTROL PANEL
# ---------------------------------------------------------
st.sidebar.image("https://img.icons8.com/isometric-line/100/4a90e2/city-buildings.png", width=70)
st.sidebar.title("Параметры Аудита")

st.sidebar.subheader("📌 Идентификация")
act_num = st.sidebar.text_input("Номер Акта", value="GS-BAK-1402")
audit_date = st.sidebar.date_input("Дата проведения", value=date.today())
object_name = st.sidebar.text_input("Объект недвижимости", value="Офис №1402, Port Baku Tower")
address = st.sidebar.text_input("Адрес объекта", value="г. Баку, пр. Нефтяников 153")

st.sidebar.divider()
st.sidebar.subheader("👥 Участники комиссии")
party_1 = st.sidebar.text_input("Заказчик / Передающий", value="ООО «Pasha Real Estate Asset Management»")
party_1_rep = st.sidebar.text_input("Представитель Заказчика", value="Гасанов Р. Э.")

party_2 = st.sidebar.text_input("Арендатор / Принимающий", value="ООО «AzCoin Digital Technologies»")
party_2_rep = st.sidebar.text_input("Представитель Арендатора", value="Мамедов Э. И.")

auditor_name = st.sidebar.text_input("Ведущий эксперт-аудитор", value="Сабит Фатизаде")

# ---------------------------------------------------------
# 3. HERO SECTION & METRIC DASHBOARD
# ---------------------------------------------------------
st.markdown(f"""
<div class="hero-header">
    <h1 style="color: #f0f6fc; margin-bottom: 0;">🏢 Global Asset Auditor</h1>
    <p style="color: #8b949e; font-size: 1.1rem;">Система технического аудита и мгновенной генерации коммерческих актов</p>
</div>
""", unsafe_allow_html=True)

# Default Defect Data State
if 'defects_data' not in st.session_state:
    st.session_state.defects_data = pd.DataFrame([
        {"Категория": "Отделка", "Описание": "Микротрещины на гипсокартоне (ресепшн)", "Критичность": "Низкая", "Смета (AZN)": 150.0},
        {"Категория": "Отделка", "Описание": "Следы протечек на потолке Armstrong", "Критичность": "Средняя", "Смета (AZN)": 350.0},
        {"Категория": "HVAC", "Описание": "Повышенный шум и вибрация фанкойла", "Критичность": "Средняя", "Смета (AZN)": 300.0},
        {"Категория": "Электрика", "Описание": "Отсутствие маркировки автоматов в ЩО №2", "Критичность": "Высокая", "Смета (AZN)": 120.0},
        {"Категория": "Сантехника", "Описание": "Люфт и ослабление фиксации смесителя", "Критичность": "Низкая", "Смета (AZN)": 90.0},
    ])

# Top KPI Dashboard
edited_df = st.session_state.defects_data
total_cost = edited_df["Смета (AZN)"].sum()
total_issues = len(edited_df)
high_risk = len(edited_df[edited_df["Критичность"] == "Высокая"])

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Объект</div><div class="metric-value" style="font-size:1.2rem;">{object_name[:18]}...</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Всего замечаний</div><div class="metric-value">{total_issues}</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Критичный риск</div><div class="metric-value" style="color:#da3633;">{high_risk}</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Итоговая смета</div><div class="metric-value" style="color:#2ea043;">{total_cost:,.2f} ₼</div></div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. TABBED INTERFACE
# ---------------------------------------------------------
tab_meters, tab_defects, tab_photos, tab_pdf = st.tabs([
    "⚡ Ресурсы и Доступ", 
    "🛠️ Ведомость Дефектов", 
    "📸 Фотофиксация", 
    "📄 Генерация и Запуск"
])

with tab_meters:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Приборы учета (Счетчики)")
        power_val = st.number_input("Электроэнергия (кВт·ч)", value=48512, step=1)
        cw_val = st.number_input("Холодная вода (м³)", value=412, step=1)
        hw_val = st.number_input("Горячая вода (м³)", value=189, step=1)
    with c2:
        st.subheader("🔑 Передача ключей и СКУД")
        keys_cnt = st.number_input("Физические ключи (шт.)", value=4, step=1)
        cards_cnt = st.number_input("Магнитные карты СКУД (шт.)", value=10, step=1)
        remotes_cnt = st.number_input("Пульты управления HVAC (шт.)", value=2, step=1)

with tab_defects:
    st.subheader("Редактор выявленных нарушений")
    st.caption("Вы можете добавлять новые строки прямо в таблицу или редактировать текущие значения.")
    
    st.session_state.defects_data = st.data_editor(
        edited_df, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "Критичность": st.column_config.SelectboxColumn(
                "Критичность",
                options=["Низкая", "Средняя", "Высокая"],
                required=True
            ),
            "Смета (AZN)": st.column_config.NumberColumn(
                "Смета (AZN)",
                format="%.2f ₼"
            )
        }
    )

with tab_photos:
    st.subheader("Приложение: Фотоматериалы нарушений")
    uploaded_files = st.file_uploader(
        "Загрузите фото дефектов (IMG_1402_01, IMG_1402_02 и т.д.)", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True
    )
    if uploaded_files:
        cols = st.columns(3)
        for idx, file in enumerate(uploaded_files):
            cols[idx % 3].image(file, caption=file.name, use_container_width=True)

with tab_pdf:
    st.subheader("Сформировать финальный PDF-документ")
    st.write("После нажатия кнопки система автоматически скомпилирует стилизованный PDF со всеми печатями и сметными расчетами.")

    def build_pdf():
        defects_rows_html = ""
        for _, r in st.session_state.defects_data.iterrows():
            badge_color = "#238636" if r['Критичность'] == "Низкая" else ("#d29922" if r['Критичность'] == "Средняя" else "#da3633")
            defects_rows_html += f"""
            <tr>
                <td><b>{r['Категория']}</b></td>
                <td>{r['Описание']}</td>
                <td style="text-align:center;"><span style="background:{badge_color}; color:white; padding:2px 6px; border-radius:4px; font-size:8pt;">{r['Критичность']}</span></td>
                <td style="text-align:right;"><b>{r['Смета (AZN)']:,.2f} ₼</b></td>
            </tr>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{ size: A4; margin: 15mm; }}
                body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 9.5pt; color: #1f2937; line-height: 1.4; }}
                .header-table {{ width: 100%; border-bottom: 2px solid #111827; padding-bottom: 10px; margin-bottom: 20px; }}
                .title {{ font-size: 16pt; font-weight: bold; color: #111827; text-transform: uppercase; }}
                .subtitle {{ font-size: 9pt; color: #6b7280; }}
                .section-title {{ font-size: 11pt; font-weight: bold; color: #111827; border-bottom: 1px solid #e5e7eb; padding-bottom: 4px; margin-top: 15px; margin-bottom: 8px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                th {{ background-color: #1f2937; color: white; padding: 6px 8px; text-align: left; font-size: 8.5pt; }}
                td {{ padding: 6px 8px; border-bottom: 1px solid #e5e7eb; font-size: 8.5pt; }}
                .total-box {{ background-color: #f9fafb; border: 1px solid #e5e7eb; padding: 10px; text-align: right; margin-top: 10px; border-radius: 4px; }}
                .signatures {{ margin-top: 30px; width: 100%; }}
                .sig-box {{ width: 30%; float: left; margin-right: 3%; font-size: 8.5pt; }}
            </style>
        </head>
        <body>
            <table class="header-table">
                <tr>
                    <td>
                        <div class="title">Акт Аудита № {act_num}</div>
                        <div class="subtitle">GLOBAL ASSET AUDITOR • СИСТЕМА ЦИФРОВОГО УЧЕТА</div>
                    </td>
                    <td style="text-align: right;">
                        <b>Дата:</b> {audit_date.strftime('%d.%m.%Y')}<br>
                        <b>Статус:</b> Сформирован
                    </td>
                </tr>
            </table>

            <p><b>Объект:</b> {object_name} ({address})</p>

            <div class="section-title">1. КОМИССИЯ И СТОРОНЫ</div>
            <p><b>Передающая сторона:</b> {party_1} — <i>{party_1_rep}</i></p>
            <p><b>Принимающая сторона:</b> {party_2} — <i>{party_2_rep}</i></p>
            <p><b>Независимый эксперт:</b> {auditor_name}</p>

            <div class="section-title">2. РЕСУРСНЫЕ ПОКАЗАТЕЛИ И СКУД</div>
            <p>Электроэнергия: <b>{power_val} кВт·ч</b> | ХВ: <b>{cw_val} м³</b> | ГВ: <b>{hw_val} м³</b></p>
            <p>Ключи: <b>{keys_cnt} шт.</b> | RFID-карты: <b>{cards_cnt} шт.</b> | Пульты HVAC: <b>{remotes_cnt} шт.</b></p>

            <div class="section-title">3. ДЕФЕКТОВОЧНАЯ ВЕДОМОСТЬ</div>
            <table>
                <thead>
                    <tr>
                        <th>Категория</th>
                        <th>Описание дефекта</th>
                        <th style="text-align:center;">Критичность</th>
                        <th style="text-align:right;">Смета (AZN)</th>
                    </tr>
                </thead>
                <tbody>
                    {defects_rows_html}
                </tbody>
            </table>

            <div class="total-box">
                <span style="font-size: 11pt;"><b>ИТОГО К ВОЗМЕЩЕНИЮ / УСТРАНЕНИЮ: {total_cost:,.2f} AZN</b></span>
            </div>

            <div class="section-title" style="margin-top: 40px;">4. ПОДПИСИ СТОРОН</div>
            <div class="signatures">
                <div class="sig-box">
                    <p><b>Аудитор:</b></p><br>____________ / {auditor_name}
                </div>
                <div class="sig-box">
                    <p><b>Передающая сторона:</b></p><br>____________ / {party_1_rep}
                </div>
                <div class="sig-box">
                    <p><b>Принимающая сторона:</b></p><br>____________ / {party_2_rep}
                </div>
            </div>
        </body>
        </html>
        """
        
        pdf_out = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_out)
        return pdf_out.getvalue()

    if st.button("🔥 Сформировать и запустить генерацию PDF", type="primary"):
        with st.spinner("Компиляция PDF-файла..."):
            pdf_bytes = build_pdf()
            st.download_button(
                label="📥 Скачать готовый Акт (PDF)",
                data=pdf_bytes,
                file_name=f"Audit_Act_{act_num}.pdf",
                mime="application/pdf"
            )
            st.success("Документ успешно сформирован!")
