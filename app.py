import hashlib
import os
import sqlite3
import pandas as pd
from PIL import Image
import streamlit as st
from fpdf import FPDF

# Конфигурация страницы
st.set_page_config(
    page_title="Global Asset Auditor | SaaS Platform",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ---
def init_db():
  conn = sqlite3.connect("auditor_saas.db", check_same_thread=False)
  cursor = conn.cursor()
  # Таблица пользователей
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            plan TEXT DEFAULT 'Free'
        )
    """)
  # Таблица сохраненных актов аудита
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            act_num TEXT,
            audit_date TEXT,
            object_name TEXT,
            total_cost REAL,
            pdf_filename TEXT
        )
    """)
  conn.commit()
  return conn


conn = init_db()
cursor = conn.cursor()

# Хеширование паролей
def make_hash(password):
  return hashlib.sha256(str.encode(password)).hexdigest()


def check_hash(password, hashed_password):
  return make_hash(password) == hashed_password


# --- УПРАВЛЕНИЕ СЕССИЕЙ АВТОРИЗАЦИИ ---
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
if "username" not in st.session_state:
  st.session_state.username = ""
if "user_plan" not in st.session_state:
  st.session_state.user_plan = "Free"

# --- БОКОВАЯ ПАНЕЛЬ: АВТОРИЗАЦИЯ И НАВИГАЦИЯ ---
st.sidebar.title("🏢 Global Asset Auditor")

if not st.session_state.logged_in:
  st.sidebar.markdown("### Вход в систему")
  auth_mode = st.sidebar.radio("Выберите действие", ["Вход", "Регистрация"])

  u_input = st.sidebar.text_input("Логин (Email)")
  p_input = st.sidebar.text_input("Пароль", type="password")

  if auth_mode == "Регистрация":
    if st.sidebar.button("Зарегистрироваться", type="primary"):
      if u_input and p_input:
        cursor.execute(
            "SELECT * FROM users WHERE username = ?", (u_input,)
        )
        if cursor.fetchone():
          st.sidebar.error("Такой пользователь уже существует!")
        else:
          cursor.execute(
              "INSERT INTO users (username, password, plan) VALUES (?, ?, ?)",
              (u_input, make_hash(p_input), "Free"),
          )
          conn.commit()
          st.sidebar.success("Регистрация успешна! Войдите в систему.")
      else:
        st.sidebar.warning("Заполните все поля.")
  else:
    if st.sidebar.button("Войти", type="primary"):
      if u_input and p_input:
        cursor.execute(
            "SELECT password, plan FROM users WHERE username = ?", (u_input,)
        )
        user_data = cursor.fetchone()
        if user_data and check_hash(p_input, user_data[0]):
          st.session_state.logged_in = True
          st.session_state.username = u_input
          st.session_state.user_plan = user_data[1]
          st.rerun()
        else:
          st.sidebar.error("Неверный логин или пароль.")
      else:
        st.sidebar.warning("Введите логин и пароль.")

  st.stop()  # Останавливаем выполнение, пока пользователь не вошел

# --- ЕСЛИ ПОЛЬЗОВАТЕЛЬ АВТОРИЗОВАН ---
st.sidebar.success(
    f"👤 Пользователь: {st.session_state.username}\n\nТариф:"
    f" **{st.session_state.user_plan}**"
)

if st.sidebar.button("🚪 Выйти из аккаунта"):
  st.session_state.logged_in = False
  st.session_state.username = ""
  st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("📁 Параметры текущего акта")

# Загрузка логотипа
if os.path.exists("logo.png"):
  st.sidebar.image("logo.png", use_container_width=True)

act_num = st.sidebar.text_input("Номер акта", value="AUDIT-2026-01")
audit_date = st.sidebar.date_input("Дата аудита")
object_name = st.sidebar.text_input(
    "Объект / Помещение", value="Офис №101, Бизнес-центр"
)
object_address = st.sidebar.text_input("Адрес объекта", value="ул. Низами 25, Баку")

st.sidebar.subheader("Стороны комиссии")
party_trans = st.sidebar.text_input(
    "Передающая сторона", value="ООО «Property Management»"
)
party_recv = st.sidebar.text_input(
    "Принимающая сторона", value="ООО «Client Tech»"
)
lead_auditor = st.sidebar.text_input("Главный эксперт-аудитор", value="Сабит Ф.")

# --- ОСНОВНОЙ ИНТЕРФЕЙС (ВКЛАДКИ) ---
tab_create, tab_history, tab_billing = st.tabs([
    "📝 Создать акт",
    "🗂️ Архив отчетов",
    "💳 Тарифы и Оплата",
])

with tab_billing:
  st.subheader("💳 Тарифные планы и корпоративные решения")
  
  col1, col2, col3 = st.columns(3)

  with col1:
    st.markdown("### 🟢 Базовый (Free)")
    st.markdown("""
    - До 5 аудитов в месяц
    - Стандартные PDF-отчеты
    - Облачное хранение
    """)
    st.markdown("**Текущий статус:** Ваш тариф")

  with col2:
    st.markdown("### 🟡 Профессиональный (PRO)")
    st.markdown("""
    - Безлимитные официальные PDF
    - Без водяных знаков
    - Приоритетная поддержка
    - **49 AZN / месяц**
    """)
    if st.button("🚀 Выбрать PRO", type="primary", key="pro_btn"):
      with engine.begin() as conn:
        conn.execute(
            sqlalchemy.text("UPDATE users SET plan = 'PRO' WHERE username = :u"),
            {"u": st.session_state.username},
        )
      st.session_state.user_plan = "PRO"
      st.success("Тариф обновлен до PRO!")
      st.rerun()

  with col3:
    st.markdown("### 💎 Корпоративный (Enterprise)")
    st.markdown("""
    - Все функции PRO без ограничений
    - Несколько сотрудников в команде
    - Индивидуальный дизайн и логотип
    - **149 AZN / месяц**
    """)
    if st.button("🌟 Подключить Enterprise", type="primary", key="ent_btn"):
      with engine.begin() as conn:
        conn.execute(
            sqlalchemy.text("UPDATE users SET plan = 'Enterprise' WHERE username = :u"),
            {"u": st.session_state.username},
        )
      st.session_state.user_plan = "Enterprise"
      st.success("Тариф обновлен до Корпоративного!")
      st.rerun()

    # Подключение кириллического шрифта
    font_loaded = False
    for f_path in [
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
      if os.path.exists(f_path):
        try:
          pdf.add_font("DejaVu", "", f_path, uni=True)
          pdf.add_font(
              "DejaVuB", "", f_path.replace("Sans.ttf", "Sans-Bold.ttf"), uni=True
          )
          font_loaded = True
          break
        except Exception:
          pass

    # Заполнение контента PDF
    f_name_b = "DejaVuB" if font_loaded else "helvetica"
    f_name_r = "DejaVu" if font_loaded else "helvetica"

    pdf.set_font(f_name_b, size=14)
    pdf.cell(0, 10, f"АКТ ТЕХНИЧЕСКОГО АУДИТА № {act_num}", 0, 1, "L")

    pdf.set_font(f_name_r, size=10)
    pdf.cell(
        0,
        6,
        f"Дата: {audit_date} | Объект: {object_name} ({object_address})",
        0,
        1,
        "L",
    )
    pdf.ln(5)

    pdf.set_font(f_name_b, size=11)
    pdf.cell(0, 6, "1. СТОРОНЫ И КОМИССИЯ", 0, 1, "L")
    pdf.set_font(f_name_r, size=10)
    pdf.cell(0, 6, f"- Передающая сторона: {party_trans}", 0, 1, "L")
    pdf.cell(0, 6, f"- Принимающая сторона: {party_recv}", 0, 1, "L")
    pdf.cell(0, 6, f"- Эксперт-аудитор: {lead_auditor}", 0, 1, "L")
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

    # Сохранение в базу данных пользователя
    cursor.execute(
        """INSERT INTO audits (username, act_num, audit_date, object_name,"
        " total_cost, pdf_filename) VALUES (?, ?, ?, ?, ?, ?)""",
        (
            st.session_state.username,
            act_num,
            str(audit_date),
            object_name,
            total_cost,
            pdf_filename,
        ),
    )
    conn.commit()

    st.success("Акт успешно сформирован и сохранен в вашем личном кабинете!")

    with open(pdf_filename, "rb") as f:
      st.download_button(
          label="📥 Скачать готовый PDF-Акт",
          data=f,
          file_name=pdf_filename,
          mime="application/pdf",
      )

with tab_history:
  st.subheader("🗂️ История ваших аудитов")
  cursor.execute(
      "SELECT act_num, audit_date, object_name, total_cost, pdf_filename FROM"
      " audits WHERE username = ?",
      (st.session_state.username,),
  )
  user_audits = cursor.fetchall()

  if user_audits:
    for audit in user_audits:
      with st.expander(
          f"Акт № {audit[0]} от {audit[1]} — {audit[2]} ({audit[3]:,.2f} AZN)"
      ):
        st.write(f"**Объект:** {audit[2]}")
        st.write(f"**Сумма сметы:** {audit[3]:,.2f} AZN")
        if os.path.exists(audit[4]):
          with open(audit[4], "rb") as f:
            st.download_button(
                label="📥 Скачать этот PDF повторно",
                data=f,
                file_name=audit[4],
                mime="application/pdf",
                key=f"dl_{audit[0]}",
            )
        else:
          st.warning("Файл PDF был очищен сервером. Сформируйте его заново.")
  else:
    st.info(
        "У вас пока нет сохраненных актов. Создайте первый акт на вкладке"
        " «Создать акт»."
    )

with tab_billing:
  st.subheader("💳 Тарифные планы и монетизация")
  col1, col2 = st.columns(2)

  with col1:
    st.markdown("### 🟢 Базовый (Free)")
    st.markdown("- Неограниченные черновики\n- Стандартные отчеты\n- Ручной ввод")
    st.markdown("**Текущий статус:** Ваш тариф")

  with col2:
    st.markdown("### 🟡 Профессиональный (PRO)")
    st.markdown(
        "- Безлимитные официальные PDF\n- Без водяных знаков\n- Приоритетная"
        " поддержка\n- **19 AZN / месяц**"
    )
    if st.button("🚀 Подключить PRO тариф (Тестовая оплата)", type="primary"):
      cursor.execute(
          "UPDATE users SET plan = 'PRO' WHERE username = ?",
          (st.session_state.username,),
      )
      conn.commit()
      st.session_state.user_plan = "PRO"
      st.success(
          "Тариф успешно обновлен до PRO! Перезагрузите страницу для"
          " применения."
      )
      st.rerun()
