import os
import pandas as pd
from PIL import Image
import streamlit as st
from fpdf import FPDF

# Конфигурация страницы
st.set_page_config(
    page_title="Global Asset Auditor",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏢 Global Asset Auditor")
st.markdown(
    "**Профессиональная платформа технического аудита и контроля коммерческих"
    " активов**"
)

# --- БОКОВАЯ ПАНЕЛЬ (ПАРАМЕТРЫ) ---
st.sidebar.header("📁 Параметры акта")

# Загрузка логотипа по умолчанию
if os.path.exists("logo.png"):
  st.sidebar.image("logo.png", use_container_width=True)
else:
  st.sidebar.warning("Логотип `logo.png` не обнаружен в репозитории.")

st.sidebar.subheader("Инфо об объекте")
act_num = st.sidebar.text_input(
    "Номер акта", value="AUDIT-2026-01", placeholder="например: ACT-001"
)
audit_date = st.sidebar.date_input("Дата аудита")
object_name = st.sidebar.text_input(
    "Объект / Помещение",
    value="",
    placeholder="Например: Офис №101, Бизнес-центр",
)
object_address = st.sidebar.text_input(
    "Адрес объекта", value="", placeholder="Например: ул. Низами 25, Баку"
)

st.sidebar.subheader("Стороны комиссии")
party_trans = st.sidebar.text_input(
    "Передающая сторона",
    value="",
    placeholder="Например: ООО «Property Management»",
)
party_recv = st.sidebar.text_input(
    "Принимающая сторона", value="", placeholder="Например: ООО «Client Tech»"
)
lead_auditor = st.sidebar.text_input(
    "Главный эксперт-аудитор", value="", placeholder="ФИО эксперта"
)

st.sidebar.subheader("Ресурсные показатели и ключи")
meters_info = st.sidebar.text_input(
    "Показатели счетчиков",
    value="",
    placeholder="Электроэнергия: 0 кВт·ч | ХВ: 0 м³",
)
keys_info = st.sidebar.text_input(
    "Ключи и доступы", value="", placeholder="Ключи: 4 шт. | RFID-карты: 10 шт."
)

st.markdown("---")

# --- ОСНОВНАЯ ЧАСТЬ (ТАБЛИЦА ДЕФЕКТОВ) ---
st.subheader("📋 Дефектовочная ведомость и смета")
st.markdown(
    "Заполните или отредактируйте список выявленных дефектов и стоимость их"
    " устранения:"
)

# Шаблон таблицы с чистыми примерами
if "df" not in st.session_state:
  st.session_state.df = pd.DataFrame([
      {
          "Категория": "Отделка",
          "Описание": "Пример: Микротрещины на гипсокартоне",
          "Критичность": "Низкая",
          "Смета (AZN)": 100.0,
      },
      {
          "Категория": "HVAC",
          "Описание": "Пример: Проверка уровня шума фанкойла",
          "Критичность": "Средняя",
          "Смета (AZN)": 200.0,
      },
      {
          "Категория": "Электрика",
          "Описание": "Пример: Маркировка автоматических выключателей",
          "Критичность": "Высокая",
          "Смета (AZN)": 150.0,
      },
  ])

# Редактор таблицы
edited_df = st.data_editor(
    st.session_state.df, num_rows="dynamic", use_container_width=True
)

# Расчет итоговой суммы
total_cost = 0.0
try:
  total_cost = edited_df["Смета (AZN)"].sum()
except Exception:
  total_cost = 0.0

st.markdown(
    f"### Итоговая смета устранения дефектов: **{total_cost:,.2f} AZN**"
)

st.markdown("---")


# --- ГЕНЕРАЦИЯ PDF ---
class PDF(FPDF):

  def header(self):
    pass

  def footer(self):
    self.set_y(-15)
    self.set_font("helvetica", "I", 8)
    self.set_text_color(150, 150, 150)
    self.cell(
        0,
        10,
        f"Страница {self.page_no()} | Global Asset Auditor Platform",
        0,
        0,
        "C",
    )


st.subheader("🚀 Запуск и Скачивание")

if st.button("📄 Сформировать официальный PDF-Акт", type="primary"):
  pdf_filename = f"Audit_Act_{act_num}.pdf"

  # Создание PDF документа
  pdf = PDF(orientation="P", unit="mm", format="A4")
  pdf.add_page()

  # Попытка подключить шрифт с поддержкой кириллицы (DejaVu) если доступен, иначе стандартный
  font_loaded = False
  for f_path in ["DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
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

  if font_loaded:
    pdf.set_font("DejaVuB", size=14)
  else:
    pdf.set_font("helvetica", "B", size=14)

  # Шапка документа
  pdf.cell(
      0,
      10,
      f"АКТ ТЕХНИЧЕСКОГО АУДИТА № {act_num}"
      if font_loaded
      else f"AKT TEHNICHESKOGO AUDITA # {act_num}",
      0,
      1,
      "L",
  )

  if font_loaded:
    pdf.set_font("DejaVu", size=10)
  else:
    pdf.set_font("helvetica", size=10)

  pdf.cell(
      0,
      6,
      f"Дата: {audit_date} | Объект: {object_name or 'Не указан'} ({object_address or 'Адрес не указан'})",
      0,
      1,
      "L",
  )
  pdf.ln(5)

  # Стороны
  if font_loaded:
    pdf.set_font("DejaVuB", size=11)
  else:
    pdf.set_font("helvetica", "B", size=11)
  pdf.cell(0, 6, "1. СТОРОНЫ И КОМИССИЯ", 0, 1, "L")

  if font_loaded:
    pdf.set_font("DejaVu", size=10)
  else:
    pdf.set_font("helvetica", size=10)
  pdf.cell(
      0, 6, f"- Передающая сторона: {party_trans or 'Не указано'}", 0, 1, "L"
  )
  pdf.cell(
      0, 6, f"- Принимающая сторона: {party_recv or 'Не указано'}", 0, 1, "L"
  )
  pdf.cell(
      0, 6, f"- Эксперт-аудитор: {lead_auditor or 'Не указан'}", 0, 1, "L"
  )
  pdf.ln(5)

  # Ресурсы
  if font_loaded:
    pdf.set_font("DejaVuB", size=11)
  else:
    pdf.set_font("helvetica", "B", size=11)
  pdf.cell(0, 6, "2. РЕСУРСНЫЕ ПОКАЗАТЕЛИ И ДОСТУПЫ", 0, 1, "L")

  if font_loaded:
    pdf.set_font("DejaVu", size=10)
  else:
    pdf.set_font("helvetica", size=10)
  pdf.cell(
      0,
      6,
      f"- Показатели: {meters_info or 'Данные не внесены'}",
      0,
      1,
      "L",
  )
  pdf.cell(
      0,
      6,
      f"- Ключевые элементы: {keys_info or 'Данные не внесены'}",
      0,
      1,
      "L",
  )
  pdf.ln(5)

  # Таблица дефектов
  if font_loaded:
    pdf.set_font("DejaVuB", size=11)
  else:
    pdf.set_font("helvetica", "B", size=11)
  pdf.cell(0, 6, "3. ДЕФЕКТОВОЧНАЯ ВЕДОМОСТЬ", 0, 1, "L")

  if font_loaded:
    pdf.set_font("DejaVuB", size=9)
  else:
    pdf.set_font("helvetica", "B", size=9)

  # Табличный хэдер
  pdf.cell(40, 8, "Категория", 1, 0, "C")
  pdf.cell(85, 8, "Описание дефекта", 1, 0, "C")
  pdf.cell(30, 8, "Критичность", 1, 0, "C")
  pdf.cell(35, 8, "Смета (AZN)", 1, 1, "C")

  if font_loaded:
    pdf.set_font("DejaVu", size=9)
  else:
    pdf.set_font("helvetica", size=9)

  for index, row in edited_df.iterrows():
    pdf.cell(40, 8, str(row.get("Категория", "")), 1, 0, "L")
    pdf.cell(85, 8, str(row.get("Описание", "")), 1, 0, "L")
    pdf.cell(30, 8, str(row.get("Критичность", "")), 1, 0, "C")
    pdf.cell(35, 8, f"{float(row.get('Смета (AZN)', 0)):,.2f}", 1, 1, "R")

  # Итого
  if font_loaded:
    pdf.set_font("DejaVuB", size=10)
  else:
    pdf.set_font("helvetica", "B", size=10)
  pdf.cell(
      155, 9, "ИТОГО СМЕТА:", 1, 0, "R"
  )
  pdf.cell(35, 9, f"{total_cost:,.2f} AZN", 1, 1, "R")
  pdf.ln(10)

  # Подписи
  if font_loaded:
    pdf.set_font("DejaVuB", size=10)
  else:
    pdf.set_font("helvetica", "B", size=10)
  pdf.cell(0, 6, "ПОДПИСИ СТОРОН:", 0, 1, "L")
  pdf.ln(8)

  if font_loaded:
    pdf.set_font("DejaVu", size=9)
  else:
    pdf.set_font("helvetica", size=9)
  pdf.cell(
      63,
      6,
      "Аудитор: ______________________",
      0,
      0,
      "L",
  )
  pdf.cell(
      63,
      6,
      "Передающая: ___________________",
      0,
      0,
      "L",
  )
  pdf.cell(
      63,
      6,
      "Принимающая: __________________",
      0,
      1,
      "L",
  )

  # Сохранение PDF
  pdf.output(pdf_filename)

  with open(pdf_filename, "rb") as f:
    st.download_button(
        label="📥 Скачать готовый PDF-Акт",
        data=f,
        file_name=pdf_filename,
        mime="application/pdf",
    )
  st.success("Акт успешно сформирован и готов к скачиванию!")
