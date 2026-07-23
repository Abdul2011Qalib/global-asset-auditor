import os
import urllib.request
import streamlit as st
import pandas as pd
import sqlalchemy
from fpdf import FPDF

st.set_page_config(page_title="Global Asset Auditor", page_icon="📋", layout="wide")

# Фирменный премиальный стиль (черный с золотыми акцентами)
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    h1, h2, h3 {
        color: #d4af37 !important;
        font-family: 'Helvetica Neue', sans-serif;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #d4af37 0%, #aa8c2c 100%);
        color: #ffffff;
        border: none;
        font-weight: bold;
        border-radius: 6px;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #e6c547, #bc9b35);
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# Инициализация подключения к базе данных Supabase PostgreSQL
@st.cache_resource
def init_connection():
    db_url = st.secrets["postgres"]["url"]
    return sqlalchemy.create_engine(db_url)

engine = init_connection()

# Создание таблиц при первом запуске, если они еще не существуют
with engine.begin() as conn:
    conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            plan TEXT DEFAULT 'Free'
        )
    """))
    conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS audits (
            id SERIAL PRIMARY KEY,
            username TEXT,
            act_num TEXT,
            audit_date TEXT,
            object_name TEXT,
            total_cost NUMERIC,
            pdf_filename TEXT
        )
    """))
    conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS payment_requests (
            id SERIAL PRIMARY KEY,
            username TEXT,
            plan TEXT,
            note TEXT,
            status TEXT DEFAULT 'Ожидает'
        )
    """))

# Инициализация состояния сессии
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_plan = "Free"

# Блок авторизации и регистрации
if not st.session_state.logged_in:
    st.sidebar.title("🔐 Авторизация")
    auth_mode = st.sidebar.radio("Выберите режим", ["Вход", "Регистрация"])
    
    username = st.sidebar.text_input("Логин (Email)")
    password = st.sidebar.text_input("Пароль", type="password")
    
    if auth_mode == "Вход":
        if st.sidebar.button("Войти", type="primary"):
            with engine.begin() as conn:
                result = conn.execute(
                    sqlalchemy.text("SELECT password, plan FROM users WHERE username = :u"),
                    {"u": username}
                ).fetchone()
            if result and result[0] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_plan = result[1] or "Free"
                st.success("Успешный вход!")
                st.rerun()
            else:
                st.sidebar.error("Неверный логин или пароль")
    else:
        if st.sidebar.button("Зарегистрироваться", type="primary"):
            try:
                with engine.begin() as conn:
                    conn.execute(
                        sqlalchemy.text("INSERT INTO users (username, password, plan) VALUES (:u, :p, 'Free')"),
                        {"u": username, "p": password}
                    )
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_plan = "Free"
                st.success("Регистрация успешна!")
                st.rerun()
            except Exception:
                st.sidebar.error("Пользователь с таким именем уже существует или ошибка базы данных")
    
    st.stop()

# Боковая панель для авторизованного пользователя
st.sidebar.markdown(f"**Пользователь:**\n{st.session_state.username}")
st.sidebar.markdown(f"**Тариф:** {st.session_state.user_plan}")
if st.sidebar.button("Выйти из аккаунта"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_plan = "Free"
    st.rerun()

st.title("Global Asset Auditor")
st.markdown("Technical Audit & Asset Management Platform")

tab_create, tab_archive, tab_billing = st.tabs(["Создать акт", "Архив отчетов", "Тарифы и Оплата"])

with tab_create:
    st.subheader("Параметры текущего акта")
    col_a, col_b = st.columns(2)
    with col_a:
        act_num = st.text_input("Номер акта", value="AUDIT-2026-01")
        audit_date = st.date_input("Дата аудита")
        object_name = st.text_input("Название объекта", value="Главный складской комплекс")
    with col_b:
        object_address = st.text_input("Адрес объекта", value="г. Баку, ул. Низами 1")
        party_trans = st.text_input("Передающая сторона", value="ООО 'ТехноСтрой'")
        party_recv = st.text_input("Принимающая сторона", value="ОАО 'Global Assets'")
        lead_auditor = st.text_input("Ведущий аудитор", value="")

    st.subheader("Дефектовочная ведомость")
    initial_data = pd.DataFrame([
        {"Категория": "Электрика", "Описание": "Повреждение изоляции кабеля питания", "Критичность": "Высокая", "Смета (AZN)": 1200.0},
        {"Категория": "Оборудование", "Описание": "Износ подшипников вентиляции", "Критичность": "Средняя", "Смета (AZN)": 450.0}
    ])
    edited_df = st.data_editor(initial_data, num_rows="dynamic", use_container_width=True)
    
    total_cost = edited_df["Смета (AZN)"].sum() if not edited_df.empty else 0.0
    st.metric("Итого смета", f"{total_cost:,.2f} AZN")

    st.subheader("Генерация и Сохранение")
    if st.button("📄 Сформировать и сохранить официальный акт", type="primary"):
        pdf_filename = f"Audit_{act_num}_{st.session_state.username}.pdf"

        # Автоматическая загрузка шрифтов DejaVu для полноценной поддержки кириллицы в облаке
        font_files = {
            "DejaVuSans.ttf": "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf",
            "DejaVuSans-Bold.ttf": "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans-Bold.ttf"
        }
        for fname, furl in font_files.items():
            if not os.path.exists(fname):
                try:
                    urllib.request.urlretrieve(furl, fname)
                except Exception:
                    pass

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Регистрация шрифтов в FPDF
        f_name_r = "helvetica"
        f_name_b = "helvetica"

        if os.path.exists("DejaVuSans.ttf"):
            try:
                pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
                f_name_r = "DejaVu"
            except Exception:
                pass

        if os.path.exists("DejaVuSans-Bold.ttf"):
            try:
                pdf.add_font("DejaVuB", "", "DejaVuSans-Bold.ttf", uni=True)
                f_name_b = "DejaVuB"
            except Exception:
                pass
        
        # Если жирный шрифт не подключился, используем обычный DejaVu как универсальный
        if f_name_b == "helvetica" and f_name_r == "DejaVu":
            f_name_b = "DejaVu"

        # --- СОВРЕМЕННЫЙ ДИЗАЙН PDF ---
        
        # 1. Шапка (Хедер документа)
        pdf.set_fill_color(24, 34, 48)  # Глубокий темно-синий/графитовый цвет
        pdf.rect(10, 10, 190, 24, style="F")
        
        pdf.set_font(f_name_b, size=15)
        pdf.set_text_color(212, 175, 55)  # Золотой акцент
        pdf.set_xy(15, 14)
        pdf.cell(180, 8, "GLOBAL ASSET AUDITOR", 0, 1, "L")
        
        pdf.set_font(f_name_r, size=9)
        pdf.set_text_color(220, 220, 220)
        pdf.set_xy(15, 23)
        pdf.cell(180, 6, f"ОФИЦИАЛЬНЫЙ АКТ ТЕХНИЧЕСКОГО АУДИТА № {act_num}", 0, 1, "L")

        pdf.ln(16)

        # 2. Блок общих сведений (метаданные с фоном)
        pdf.set_font(f_name_b, size=11)
        pdf.set_text_color(24, 34, 48)
        pdf.cell(0, 8, "1. ОБЩИЕ СВЕДЕНИЯ И СТОРОНЫ", 0, 1, "L")
        
        pdf.set_font(f_name_r, size=9)
        pdf.set_fill_color(245, 247, 250) # Светло-серый современный фон
        pdf.set_text_color(50, 50, 50)
        
        start_y = pdf.get_y()
        pdf.rect(10, start_y, 190, 32, style="F")
        
        pdf.set_xy(15, start_y + 4)
        pdf.cell(90, 6, f"Дата аудита: {audit_date}", 0, 0, "L")
        pdf.cell(90, 6, f"Передающая сторона: {party_trans}", 0, 1, "L")
        
        pdf.set_x(15)
        pdf.cell(90, 6, f"Объект: {object_name}", 0, 0, "L")
        pdf.cell(90, 6, f"Принимающая сторона: {party_recv}", 0, 1, "L")
        
        pdf.set_x(15)
        pdf.cell(90, 6, f"Адрес: {object_address}", 0, 0, "L")
        pdf.cell(90, 6, f"Ведущий аудитор: {lead_auditor if lead_auditor else 'Не указан'}", 0, 1, "L")
        
        pdf.ln(12)

        # 3. Дефектовочная ведомость (Таблица)
        pdf.set_font(f_name_b, size=11)
        pdf.set_text_color(24, 34, 48)
        pdf.cell(0, 8, "2. ДЕФЕКТОВОЧНАЯ ВЕДОМОСТЬ И СМЕТА", 0, 1, "L")
        
        # Шапка таблицы
        pdf.set_fill_color(24, 34, 48)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(f_name_b, size=9)
        
        col_widths = [35, 90, 30, 35] # Сумма = 190
        pdf.cell(col_widths[0], 8, "Категория", 1, 0, "C", fill=True)
        pdf.cell(col_widths[1], 8, "Описание дефекта", 1, 0, "C", fill=True)
        pdf.cell(col_widths[2], 8, "Критичность", 1, 0, "C", fill=True)
        pdf.cell(col_widths[3], 8, "Смета (AZN)", 1, 1, "C", fill=True)

        # Строки таблицы с чередованием цвета (зебра)
        pdf.set_font(f_name_r, size=9)
        pdf.set_text_color(50, 50, 50)
        
        for index, row in edited_df.iterrows():
            if index % 2 == 0:
                pdf.set_fill_color(255, 255, 255)
            else:
                pdf.set_fill_color(245, 247, 250)
                
            pdf.cell(col_widths[0], 8, str(row.get("Категория", "")), 1, 0, "L", fill=True)
            pdf.cell(col_widths[1], 8, str(row.get("Описание", "")), 1, 0, "L", fill=True)
            pdf.cell(col_widths[2], 8, str(row.get("Критичность", "")), 1, 0, "C", fill=True)
            pdf.cell(col_widths[3], 8, f"{float(row.get('Смета (AZN)', 0)):,.2f}", 1, 1, "R", fill=True)

        # Выделенная итоговая строка
        pdf.set_fill_color(212, 175, 55) # Золотистый акцент для итогов
        pdf.set_text_color(24, 34, 48)
        pdf.set_font(f_name_b, size=9)
        pdf.cell(sum(col_widths[:3]), 9, "ИТОГО СМЕТА:", 1, 0, "R", fill=True)
        pdf.cell(col_widths[3], 9, f"{total_cost:,.2f} AZN", 1, 1, "R", fill=True)
        
        pdf.ln(15)

        # 4. Подвал документа
        pdf.set_font(f_name_r, size=8)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 5, "Документ сгенерирован автоматически платформой Global Asset Auditor.", 0, 1, "C")
        pdf.cell(0, 5, f"Дата формирования: {pd.Timestamp.now().strftime('%d.%m.%Y %H:%M')}", 0, 1, "C")

        # Сохранение PDF файла
        pdf.output(pdf_filename)

        with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text("INSERT INTO audits (username, act_num, audit_date, object_name, total_cost, pdf_filename) VALUES (:u, :an, :ad, :on, :tc, :pf)"),
                {"u": st.session_state.username, "an": act_num, "ad": str(audit_date), "on": object_name, "tc": total_cost, "pf": pdf_filename}
            )

        st.success("Акт успешно сформирован в современном стиле и сохранен в облачной базе данных!")

        with open(pdf_filename, "rb") as f:
            st.download_button(
                label="📥 Скачать красивый PDF-Акт",
                data=f,
                file_name=pdf_filename,
                mime="application/pdf"
            )

with tab_archive:
    st.subheader("📂 Архив сохраненных отчетов")
    with engine.begin() as conn:
        archive_df = pd.read_sql(
            sqlalchemy.text("SELECT act_num, audit_date, object_name, total_cost, pdf_filename FROM audits WHERE username = :u"),
            conn,
            params={"u": st.session_state.username}
        )
    if not archive_df.empty:
        st.dataframe(archive_df, use_container_width=True)
    else:
        st.info("У вас пока нет сохраненных отчетов в облаке.")

with tab_billing:
    st.subheader("💳 Тарифные планы и оплата")
    
    st.markdown("""
    <div style="background-color: #1a1f2c; padding: 20px; border-radius: 10px; border: 1px solid #d4af37; margin-bottom: 20px;">
        <h3 style="color: #d4af37; margin-top: 0;">🦁 Реквизиты для оплаты</h3>
        <p style="font-size: 16px; color: #ffffff; margin-bottom: 5px;">Номер карты Leobank:</p>
        <p style="font-size: 20px; font-weight: bold; color: #d4af37;">4098 5844 9895 1357</p>
        <p style="font-size: 13px; color: #e0e0e0; margin-top: 10px;"><i>После перевода заполните заявку ниже для активации тарифа.</i></p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🟢 Базовый (Free)")
        st.markdown("- До 5 аудитов в месяц\n- Стандартные PDF-отчеты\n- Облачное хранение")
        if st.session_state.user_plan == "Free":
            st.markdown("**Текущий статус:** Ваш тариф")

    with col2:
        st.markdown("### 🟡 Профессиональный (PRO)")
        st.markdown("- Безлимитные официальные PDF\n- Без водяных знаков\n- Приоритетная поддержка\n- **49 AZN / месяц**")

    with col3:
        st.markdown("### 💎 Корпоративный (Enterprise)")
        st.markdown("- Все функции PRO без ограничений\n- Несколько сотрудников в команде\n- Индивидуальный дизайн и логотип\n- **149 AZN / месяц**")

    st.markdown("---")
    st.subheader("📝 Подтверждение оплаты")
    
    with st.form("payment_form"):
        selected_plan = st.selectbox("Выберите тариф, который вы оплатили:", ["PRO (49 AZN)", "Enterprise (149 AZN)"])
        payment_note = st.text_input("Комментарий или номер перевода / последние 4 цифры карты отправителя")
        submit_payment = st.form_submit_button("📤 Отправить запрос на активацию тарифа", type="primary")
        
        if submit_payment:
            plan_name = "PRO" if "PRO" in selected_plan else "Enterprise"
            with engine.begin() as conn:
                conn.execute(
                    sqlalchemy.text("INSERT INTO payment_requests (username, plan, note, status) VALUES (:u, :p, :n, 'Ожидает')"),
                    {"u": st.session_state.username, "p": plan_name, "n": payment_note}
                )
            st.success("Запрос успешно отправлен! Как только перевод поступит, ваш тариф будет активирован.")
