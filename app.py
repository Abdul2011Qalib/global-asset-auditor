# Замените строку: model = genai.GenerativeModel('gemini-1.5-pro')
# На этот блок:

try:
    # Ищем модель, поддерживающую генерацию контента
    models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
    
    # Приоритет: сначала пробуем 1.5-pro, если нет - берем любую доступную gemini
    target_model = 'gemini-1.5-pro' if 'models/gemini-1.5-pro' in models else 'models/gemini-1.5-flash'
    
    # Если и flash нет, берем первую попавшуюся доступную
    if target_model not in models:
        target_model = models[0]
        
    model = genai.GenerativeModel(target_model)
    st.sidebar.success(f"Используется модель: {target_model}")
except Exception as e:
    st.error(f"Ошибка при выборе модели: {e}")
