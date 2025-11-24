# modules/add_predict_file.py
"""
Handles UI and logic for uploading a CSV file for ML prediction.
"""

import streamlit as st
import pandas as pd
import os
from .logger import get_app_logger

logger = get_app_logger()

PREDICT_REQUIRED_COLUMNS = [
    "Марка", "Возраст_дн", "mass", "Максимальная температура",
    "Темп_изменение", "weekday", "month", "t", "p", "humidity"
]

DEFAULT_PREDICT_FILENAME = "schedule_for_prediction.csv"
PREDICT_FILE_PATH = os.path.join("data", DEFAULT_PREDICT_FILENAME)

def show_prediction_requirements():
    """Shows user-friendly instructions for the required CSV structure."""
    st.markdown("### Требования к файлу прогноза")
    st.write("""
    Для корректного выполнения прогноза риска самовозгорания файл **должен быть в формате CSV** и содержать **все следующие колонки**:
    """)
    for col in PREDICT_REQUIRED_COLUMNS:
        st.code(f"- {col}", language="text")
    st.write(f"""
    - Файл будет сохранён в папке `data/` под именем **`{DEFAULT_PREDICT_FILENAME}`**.
    - Колонка `Марка` может содержать текст (например, "A1", "E5").
    - Остальные колонки должны быть числовыми.
    - Пропущенные значения будут автоматически заменены на средние.
    """)


def handle_predict_file_upload():
    """Handles file upload and validation, then saves to data/."""
    st.subheader("Загрузка файла для прогноза")

    uploaded_file = st.file_uploader(
        "Выберите CSV-файл с данными для прогноза",
        type=["csv"],
        key="predict_file_uploader"
    )

    if uploaded_file is not None:
        try:
            logger.info(f"Начата обработка загруженного файла: {uploaded_file.name}")
            df = pd.read_csv(uploaded_file)
            logger.info(f"Файл загружен: {df.shape[0]} строк, {df.shape[1]} колонок")

            missing_cols = [col for col in PREDICT_REQUIRED_COLUMNS if col not in df.columns]
            if missing_cols:
                error_msg = f"Отсутствуют обязательные колонки: {missing_cols}"
                logger.warning(error_msg)
                st.error(error_msg)
                return

            os.makedirs("data", exist_ok=True)
            with open(PREDICT_FILE_PATH, "wb") as f:
                f.write(uploaded_file.getbuffer())
            logger.info(f"Файл успешно сохранён: {PREDICT_FILE_PATH}")

            st.success(f"Файл успешно сохранён: `{PREDICT_FILE_PATH}`")
            st.info("Теперь вы можете нажать «Запустить прогноз» в верхнем меню.")

        except Exception as e:
            error_msg = f"Ошибка при обработке файла: {e}"
            logger.error(error_msg, exc_info=True)
            st.error(error_msg)
            st.exception(e)
