import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Global Asset Auditor", page_icon="🏢")
st.title("🏢 Глобальный Аудитор Активов (Beta)")

api_key = st.sidebar.text_input("Введите OpenAI API Key", type="password")

if api_key:
    client = OpenAI(api_key=api_key)
    user_input = st.text_area("Введите данные об объекте (описание, состояние, оборудование):")
    
    if st.button("Провести ИИ-аудит и создать Акт"):
        if user_input:
            with st.spinner('ИИ проводит аудит...'):
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Ты — мировой эксперт по аудиту недвижимости. Создай строго юридический Акт приема-передачи. Найди риски в описании и дай рекомендации по стандартам."},
                        {"role": "user", "content": user_input}
                    ]
                )
                report = response.choices[0].message.content
                st.markdown("---")
                st.markdown(report)
                st.download_button("Скачать отчет", report, file_name="audit_report.txt")
        else:
            st.error("Пожалуйста, введите данные объекта.")
else:
    st.warning("Пожалуйста, введите OpenAI API Key в боковой панели, чтобы начать.")
