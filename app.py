import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Global Asset Auditor", page_icon="🏢")
st.title("🏢 Глобальный Аудитор Активов (Expert)")

api_key = st.sidebar.text_input("Введите OpenAI API Key", type="password")

if api_key:
    client = OpenAI(api_key=api_key)
    user_input = st.text_area("Введите данные об объекте (описание, состояние, оборудование):")
    
    if st.button("Сформировать Акт аудита"):
        if user_input:
            with st.spinner('Аудит в процессе...'):
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": """Ты — элитный аудитор активов. Твой стиль: строго деловой, юридически точный. 
                        Твоя задача при создании Акта приема-передачи:
                        1. Выделить все технические дефекты.
                        2. Сверить описание с международными стандартами приемки (ISO/ГОСТ).
                        3. Оформить документ в виде таблицы: [Параметр] | [Состояние] | [Рекомендация].
                        4. В конце добавить раздел 'Юридические риски' и сгенерировать уникальный Hash-код для документа."""},
                        {"role": "user", "content": user_input}
                    ]
                )
                report = response.choices[0].message.content
                st.markdown(report)
                st.download_button("Скачать Акт", report, file_name="professional_audit.txt")
