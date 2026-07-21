import os
import streamlit as st
import pandas as pd
import sqlalchemy
from fpdf import FPDF

st.set_page_config(page_title="Global Asset Auditor", page_icon="📋", layout="wide")

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
        lead_auditor = st.text_input("Ведущий аудитор", value="Сабит Фетизде")

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

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()

        font_loaded = False
        for f_path in ["DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
            if os.path.exists(f_path):
                try:
                    pdf.add_font("DejaVu", "", f_path, uni=True)
                    pdf.add_font("DejaVuB", "", f_path.replace("Sans.ttf", "Sans-Bold.ttf"), uni=True)
                    font_loaded = True
                    break
                except Exception:
                    pass

        f_name_b = "DejaVuB" if font_loaded else "helvetica"
        f_name_r = "DejaVu" if font_loaded else "helvetica"

        pdf.set_font(f_name_b, size=14)
        pdf.cell(0, 10, f"АКТ ТЕХНИЧЕСКОГО АУДИТА № {act_num}", 0, 1, "L")

        pdf.set_font(f_name_r, size=10)
        pdf.cell(0, 6, f"Дата: {audit_date} | Объект: {object_name} ({object_address})", 0, 1, "L")
        pdf.ln(5)

        pdf.set_font(f_name_b, size=11)
        pdf.cell(0, 6, "1. СТОРОНЫ И КОМИССИЯ", 0, 1, "L")
        pdf.set_font(f_name_r, size=10)
        pdf.cell(0, 6, f"- Передающая сторона: {party_trans}", 0, 1, "L")
        pdf.cell(0, 6, f"- Принимающая сторона: {party_recv}", 0, 1, "L")
        pdf.cell(0, 6, f"- Ведущий аудитор: {lead_auditor}", 0, 1, "L")
        pdf.ln(5)

        pdf.set_font(f_name_b, size=11)
        pdf.cell(0, 6, "2. ДЕФЕКТОВОЧНАЯ ВЕДОМОСТЬ", 0, 1, "L")
        pdf.set_font(f_name_b, size=9)
        pdf.cell(40, 8, "Категория", 1, 0, "C")
        pdf.cell(85, 8, "Описание дефекта", 1, 0, "C")
        pdf.cell(30, 8, "Критичность", 1, 0, "C")
        pdf.cell(35, 8, "Смета (AZN)", 1, 1, "C")

        pdf.set_font(f_name_r, size=9)
        for index, row in edited_df.iterrows():
            pdf.cell(40, 8, str(row.get("Категория", "")), 1, 0, "L")
            pdf.cell(85, 8, str(row.get("Описание", "")), 1, 0, "L")
            pdf.cell(30, 8, str(row.get("Критичность", "")), 1, 0, "C")
            pdf.cell(35, 8, f"{float(row.get('Смета (AZN)', 0)):,.2f}", 1, 1, "R")

        pdf.set_font(f_name_b, size=10)
        pdf.cell(155, 9, "ИТОГО СМЕТА:", 1, 0, "R")
        pdf.cell(35, 9, f"{total_cost:,.2f} AZN", 1, 1, "R")
        pdf.ln(10)

        pdf.output(pdf_filename)

        with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text("INSERT INTO audits (username, act_num, audit_date, object_name, total_cost, pdf_filename) VALUES (:u, :an, :ad, :on, :tc, :pf)"),
                {"u": st.session_state.username, "an": act_num, "ad": str(audit_date), "on": object_name, "tc": total_cost, "pf": pdf_filename}
            )

        st.success("Акт успешно сформирован и надежно сохранен в облачной базе данных!")

        with open(pdf_filename, "rb") as f:
            st.download_button(
                label="📥 Скачать готовый PDF-Акт",
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
    st.subheader("💳 Тарифные планы и монетизация")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🟢 Базовый (Free)")
        st.markdown("- До 5 аудитов в месяц\n- Стандартные PDF-отчеты\n- Облачное хранение")
        if st.session_state.user_plan == "Free":
            st.markdown("**Текущий статус:** Ваш тариф")

    with col2:
        st.markdown("### 🟡 Профессиональный (PRO)")
        st.markdown("- Безлимитные официальные PDF\n- Без водяных знаков\n- Приоритетная поддержка\n- **49 AZN / месяц**")
        if st.button("🚀 Выбрать PRO", type="primary", key="pro_btn"):
            with engine.begin() as conn:
                conn.execute(sqlalchemy.text("UPDATE users SET plan = 'PRO' WHERE username = :u"), {"u": st.session_state.username})
            st.session_state.user_plan = "PRO"
            st.success("Тариф обновлен до PRO!")
            st.rerun()

    with col3:
        st.markdown("### 💎 Корпоративный (Enterprise)")
        st.markdown("- Все функции PRO без ограничений\n- Несколько сотрудников в команде\n- Индивидуальный дизайн и логотип\n- **149 AZN / месяц**")
        if st.button("🌟 Подключить Enterprise", type="primary", key="ent_btn"):
            with engine.begin() as conn:
                conn.execute(sqlalchemy.text("UPDATE users SET plan = 'Enterprise' WHERE username = :u"), {"u": st.session_state.username})
            st.session_state.user_plan = "Enterprise"
            st.success("Тариф обновлен до Корпоративного!")
            st.rerun()
