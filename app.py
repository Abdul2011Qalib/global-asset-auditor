import os
import urllib.request
import streamlit as st
import pandas as pd
import sqlalchemy
from fpdf import FPDF

st.set_page_config(page_title="Global Asset Auditor", page_icon="📋", layout="wide")

# Премиальный стиль (черный с золотыми акцентами)
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

# Создание таблиц и миграция схемы
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
    
    conn.execute(sqlalchemy.text("ALTER TABLE audits ADD COLUMN IF NOT EXISTS pdf_filename TEXT;"))
    conn.execute(sqlalchemy.text("ALTER TABLE audits ADD COLUMN IF NOT EXISTS total_cost NUMERIC;"))
    conn.execute(sqlalchemy.text("ALTER TABLE audits ADD COLUMN IF NOT EXISTS object_name TEXT;"))
    conn.execute(sqlalchemy.text("ALTER TABLE audits ADD COLUMN IF NOT EXISTS audit_date TEXT;"))
    conn.execute(sqlalchemy.text("ALTER TABLE audits ADD COLUMN IF NOT EXISTS act_num TEXT;"))
    conn.execute(sqlalchemy.text("ALTER TABLE audits ADD COLUMN IF NOT EXISTS username TEXT;"))

    conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS payment_requests (
            id SERIAL PRIMARY KEY,
            username TEXT,
            plan TEXT,
            note TEXT,
            status TEXT DEFAULT 'Ожидает'
        )
    """))
    conn.execute(sqlalchemy.text("ALTER TABLE payment_requests ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Ожидает';"))
    conn.execute(sqlalchemy.text("ALTER TABLE payment_requests ADD COLUMN IF NOT EXISTS note TEXT;"))
    conn.execute(sqlalchemy.text("ALTER TABLE payment_requests ADD COLUMN IF NOT EXISTS plan TEXT;"))
    conn.execute(sqlalchemy.text("ALTER TABLE payment_requests ADD COLUMN IF NOT EXISTS username TEXT;"))

    conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS platform_wallet (
            id SERIAL PRIMARY KEY,
            withdrawn NUMERIC DEFAULT 0
        )
    """))

# Состояние сессии
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_plan = "Free"

# Блок авторизации / регистрации
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

# Панель пользователя
st.sidebar.markdown(f"**Пользователь:**\n{st.session_state.username}")
st.sidebar.markdown(f"**Тариф:** {st.session_state.user_plan}")
if st.sidebar.button("Выйти из аккаунта"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_plan = "Free"
    st.rerun()

st.title("Global Asset Auditor")
st.markdown("Technical Audit & Asset Management Platform")

tab_create, tab_archive, tab_billing, tab_admin = st.tabs(["Создать акт", "Архив отчетов", "Тарифы и Оплата", "💰 Кошелек и Админ"])

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
    
    total_cost = float(edited_df["Смета (AZN)"].sum() if not edited_df.empty else 0.0)
    st.metric("Итого смета", f"{total_cost:,.2f} AZN")

    st.subheader("Генерация и Сохранение")
    if st.button("📄 Сформировать и сохранить официальный акт", type="primary"):
        pdf_filename = f"Audit_{act_num}_{st.session_state.username}.pdf"

        font_files = {
            "DejaVuSans.ttf": "https://raw.githubusercontent.com/matplotlib/matplotlib/main/lib/matplotlib/mpl-data/fonts/ttf/DejaVuSans.ttf",
            "DejaVuSans-Bold.ttf": "https://raw.githubusercontent.com/matplotlib/matplotlib/main/lib/matplotlib/mpl-data/fonts/ttf/DejaVuSans-Bold.ttf"
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

        use_unicode = False
        try:
            pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
            pdf.add_font("DejaVuB", "", "DejaVuSans-Bold.ttf", uni=True)
            f_name_r = "DejaVu"
            f_name_b = "DejaVuB"
            use_unicode = True
        except Exception as e:
            f_name_r = "helvetica"
            f_name_b = "helvetica"

        def t(text):
            if use_unicode:
                return str(text)
            rus_to_lat = {
                'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh',
                'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
                'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts',
                'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu',
                'я': 'ya', 'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo', 'Ж': 'Zh',
                'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O',
                'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'H', 'Ц': 'Ts',
                'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch', 'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu',
                'Я': 'Ya', '№': 'No.'
            }
            return "".join([rus_to_lat.get(c, c) for c in str(text)])

        pdf.set_fill_color(24, 34, 48)
        pdf.rect(10, 10, 190, 24, style="F")
        pdf.set_font(f_name_b, size=15)
        pdf.set_text_color(212, 175, 55)
        pdf.set_xy(15, 14)
        pdf.cell(180, 8, t("GLOBAL ASSET AUDITOR"), 0, 1, "L")
        
        pdf.set_font(f_name_r, size=9)
        pdf.set_text_color(220, 220, 220)
        pdf.set_xy(15, 23)
        pdf.cell(180, 6, t(f"ОФИЦИАЛЬНЫЙ АКТ ТЕХНИЧЕСКОГО АУДИТА № {act_num}"), 0, 1, "L")

        pdf.ln(16)

        pdf.set_font(f_name_b, size=11)
        pdf.set_text_color(24, 34, 48)
        pdf.cell(0, 8, t("1. ОБЩИЕ СВЕДЕНИЯ И СТОРОНЫ"), 0, 1, "L")
        
        pdf.set_font(f_name_r, size=9)
        pdf.set_fill_color(245, 247, 250)
        pdf.set_text_color(50, 50, 50)
        
        start_y = pdf.get_y()
        pdf.rect(10, start_y, 190, 32, style="F")
        
        pdf.set_xy(15, start_y + 4)
        pdf.cell(90, 6, t(f"Дата аудита: {audit_date}"), 0, 0, "L")
        pdf.cell(90, 6, t(f"Передающая сторона: {party_trans}"), 0, 1, "L")
        
        pdf.set_x(15)
        pdf.cell(90, 6, t(f"Объект: {object_name}"), 0, 0, "L")
        pdf.cell(90, 6, t(f"Принимающая сторона: {party_recv}"), 0, 1, "L")
        
        pdf.set_x(15)
        pdf.cell(90, 6, t(f"Адрес: {object_address}"), 0, 0, "L")
        pdf.cell(90, 6, t(f"Ведущий аудитор: {lead_auditor if lead_auditor else 'Не указан'}"), 0, 1, "L")
        
        pdf.ln(12)

        pdf.set_font(f_name_b, size=11)
        pdf.set_text_color(24, 34, 48)
        pdf.cell(0, 8, t("2. ДЕФЕКТОВОЧНАЯ ВЕДОМОСТЬ И СМЕТА"), 0, 1, "L")
        
        pdf.set_fill_color(24, 34, 48)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(f_name_b, size=9)
        
        col_widths = [35, 90, 30, 35]
        pdf.cell(col_widths[0], 8, t("Категория"), 1, 0, "C", fill=True)
        pdf.cell(col_widths[1], 8, t("Описание дефекта"), 1, 0, "C", fill=True)
        pdf.cell(col_widths[2], 8, t("Критичность"), 1, 0, "C", fill=True)
        pdf.cell(col_widths[3], 8, t("Смета (AZN)"), 1, 1, "C", fill=True)

        pdf.set_font(f_name_r, size=9)
        pdf.set_text_color(50, 50, 50)
        
        for index, row in edited_df.iterrows():
            if index % 2 == 0:
                pdf.set_fill_color(255, 255, 255)
            else:
                pdf.set_fill_color(245, 247, 250)
                
            pdf.cell(col_widths[0], 8, t(str(row.get("Категория", ""))), 1, 0, "L", fill=True)
            pdf.cell(col_widths[1], 8, t(str(row.get("Описание", ""))), 1, 0, "L", fill=True)
            pdf.cell(col_widths[2], 8, t(str(row.get("Критичность", ""))), 1, 0, "C", fill=True)
            pdf.cell(col_widths[3], 8, f"{float(row.get('Смета (AZN)', 0)):,.2f}", 1, 1, "R", fill=True)

        pdf.set_fill_color(212, 175, 55)
        pdf.set_text_color(24, 34, 48)
        pdf.set_font(f_name_b, size=9)
        pdf.cell(sum(col_widths[:3]), 9, t("ИТОГО СМЕТА:"), 1, 0, "R", fill=True)
        pdf.cell(col_widths[3], 9, f"{total_cost:,.2f} AZN", 1, 1, "R", fill=True)
        
        pdf.ln(15)

        pdf.set_font(f_name_r, size=8)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 5, t("Документ сгенерирован автоматически платформой Global Asset Auditor."), 0, 1, "C")
        pdf.cell(0, 5, t(f"Дата формирования: {pd.Timestamp.now().strftime('%d.%m.%Y %H:%M')}"), 0, 1, "C")

        pdf.output(pdf_filename)

        with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text("INSERT INTO audits (username, act_num, audit_date, object_name, total_cost, pdf_filename) VALUES (:u, :an, :ad, :on, :tc, :pf)"),
                {
                    "u": str(st.session_state.username), 
                    "an": str(act_num), 
                    "ad": str(audit_date), 
                    "on": str(object_name), 
                    "tc": float(total_cost), 
                    "pf": str(pdf_filename)
                }
            )

        st.success("Акт успешно сформирован и сохранен в базе данных!")

        with open(pdf_filename, "rb") as f:
            st.download_button(
                label="📥 Скачать официальный PDF-Акт",
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
    st.subheader("💳 Тарифные планы и оплата через MilliÖN")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1b2838 0%, #0d131d 100%); padding: 22px; border-radius: 12px; border: 1px solid #d4af37; margin-bottom: 25px;">
        <h3 style="color: #d4af37; margin-top: 0; margin-bottom: 10px;">
            🇦🇿 Оплата подписки через терминалы или приложение MilliÖN
        </h3>
        <p style="color: #e0e0e0; font-size: 14px; margin-bottom: 0;">
            Выберите тариф, переведите средства через MilliÖN, после чего укажите номер чека для автоматического зачисления на ваш баланс.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🟢 Базовый (Free)")
        st.markdown("- До 5 аудитов в месяц\n- Стандартные PDF-отчеты\n- Облачное хранение")
        st.markdown("---")
        if st.session_state.user_plan == "Free":
            st.info("Ваш текущий тариф")

    with col2:
        st.markdown("### 🟡 PRO")
        st.markdown("- Безлимитные официальные PDF\n- Без водяных знаков\n- Приоритетная поддержка\n- **49 AZN / месяц**")
        st.markdown("---")
        if st.button("💳 Выбрать PRO (49 AZN)", type="primary", key="btn_pro", use_container_width=True):
            with engine.begin() as conn:
                conn.execute(
                    sqlalchemy.text("INSERT INTO payment_requests (username, plan, note, status) VALUES (:u, 'PRO', 'Запрос PRO', 'Ожидает')"),
                    {"u": st.session_state.username}
                )
            st.success("Запрос на PRO создан. Оплатите в MilliÖN и отправьте чек ниже.")

    with col3:
        st.markdown("### 💎 Enterprise")
        st.markdown("- Все функции PRO без ограничений\n- Командный доступ\n- Индивидуальный дизайн и логотип\n- **149 AZN / месяц**")
        st.markdown("---")
        if st.button("💳 Выбрать Enterprise (149 AZN)", type="primary", key="btn_ent", use_container_width=True):
            with engine.begin() as conn:
                conn.execute(
                    sqlalchemy.text("INSERT INTO payment_requests (username, plan, note, status) VALUES (:u, 'Enterprise', 'Запрос Enterprise', 'Ожидает')"),
                    {"u": st.session_state.username}
                )
            st.success("Запрос на Enterprise создан. Оплатите в MilliÖN и отправьте чек ниже.")

    st.markdown("---")
    st.subheader("🔍 Подтверждение оплаты по чеку MilliÖN")
    
    with st.form("million_form"):
        txn_id = st.text_input("Введите номер чека / ID транзакции MilliÖN:")
        submit_txn = st.form_submit_button("Отправить чек на проверку", type="primary")
        
        if submit_txn:
            if txn_id.strip():
                with engine.begin() as conn:
                    conn.execute(
                        sqlalchemy.text("INSERT INTO payment_requests (username, plan, note, status) VALUES (:u, 'Подтверждение', :n, 'Ожидает')"),
                        {"u": st.session_state.username, "n": f"Чек: {txn_id}"}
                    )
                st.success("Чек успешно отправлен! Администратор проверит поступление.")
            else:
                st.error("Введите номер чека.")

with tab_admin:
    st.subheader("💰 Внутренний кошелек и управление платежами платформы")
    
    with engine.begin() as conn:
        res_earned = conn.execute(sqlalchemy.text("SELECT SUM(CASE WHEN plan='PRO' THEN 49 WHEN plan='Enterprise' THEN 149 ELSE 0 END) FROM payment_requests WHERE status='Одобрен'")).fetchone()
        total_earned = res_earned[0] if res_earned and res_earned[0] else 0.0
        
        res_withdrawn = conn.execute(sqlalchemy.text("SELECT SUM(withdrawn) FROM platform_wallet")).fetchone()
        total_withdrawn = res_withdrawn[0] if res_withdrawn and res_withdrawn[0] else 0.0
        
    current_wallet_balance = total_earned - total_withdrawn

    col_w1, col_w2, col_w3 = st.columns(3)
    col_w1.metric("Всего заработано", f"{total_earned:,.2f} AZN")
    col_w2.metric("Выведено средств", f"{total_withdrawn:,.2f} AZN")
    col_w3.metric("💳 Баланс кошелька", f"{current_wallet_balance:,.2f} AZN")

    st.markdown("---")
    st.subheader("📋 Запросы на оплату от пользователей")
    
    with engine.begin() as conn:
        reqs_df = pd.read_sql(
            sqlalchemy.text("SELECT id, username, plan, note, status FROM payment_requests ORDER BY id DESC"),
            conn
        )
        
    if not reqs_df.empty:
        st.dataframe(reqs_df, use_container_width=True)
        
        st.markdown("### Одобрить платеж и активировать тариф")
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            req_id_to_approve = st.number_input("ID запроса для одобрения", min_value=1, step=1)
        with col_act2:
            target_plan_to_set = st.selectbox("Какой тариф активировать пользователю?", ["PRO", "Enterprise"])
            
        if st.button("✅ Одобрить и обновить тариф", type="primary"):
            with engine.begin() as conn:
                req_row = conn.execute(sqlalchemy.text("SELECT username FROM payment_requests WHERE id = :id"), {"id": req_id_to_approve}).fetchone()
                if req_row:
                    target_user = req_row[0]
                    conn.execute(sqlalchemy.text("UPDATE payment_requests SET status = 'Одобрен' WHERE id = :id"), {"id": req_id_to_approve})
                    conn.execute(sqlalchemy.text("UPDATE users SET plan = :p WHERE username = :u"), {"p": target_plan_to_set, "u": target_user})
                    st.success(f"Запрос #{req_id_to_approve} одобрен! Пользователю {target_user} назначен тариф {target_plan_to_set}.")
                    st.rerun()
                else:
                    st.error("Запрос с таким ID не найден.")
    else:
        st.info("Пока нет входящих заявок на оплату.")

    st.markdown("---")
    st.subheader("💸 Вывод средств с кошелька")
    withdraw_amount = st.number_input("Сумма для вывода (AZN)", min_value=0.0, max_value=float(current_wallet_balance), step=10.0)
    if st.button("📤 Подтвердить вывод средств на мою карту/счет"):
        if withdraw_amount > 0:
            with engine.begin() as conn:
                conn.execute(
                    sqlalchemy.text("INSERT INTO platform_wallet (withdrawn) VALUES (:w)"),
                    {"w": withdraw_amount}
                )
            st.success(f"Успешно выведено {withdraw_amount:,.2f} AZN!")
            st.rerun()
        else:
            st.error("Введите корректную сумму для вывода.")
