# modules/add_weather_file.py

import streamlit as st
import pandas as pd
from pathlib import Path
from .logger import get_app_logger
from constants import DATA_WEATHER_DIR

logger = get_app_logger()

REQUIRED_COLUMNS = {
    "date", "t", "p", "humidity", "precipitation",
    "wind_dir", "v_avg", "v_max", "cloudcover", "visibility", "weather_code"
}


def handle_add_weather_file():
    """
    Renders a file uploader in the Streamlit UI to allow the user to upload a new weather CSV file.
    The uploaded file is validated for:
      - File extension (.csv)
      - Presence of all required columns
    If valid, it is saved to the designated weather data directory (DATA_WEATHER_DIR).

    This function is typically triggered when the user clicks the
    "Добавить новый файл погоды" (Add new weather file) button.

    @param None
    @return None

    Side effects:
    - Creates the weather data directory if it does not exist.
    - Displays a file uploader widget in the Streamlit app.
    - Validates file structure and required columns.
    - On successful upload and validation, saves the file and shows a success message.
    - On failure (wrong type, missing columns, I/O error), shows an appropriate warning/error.
    """
    weather_data_dir = Path(DATA_WEATHER_DIR)
    weather_data_dir.mkdir(parents=True, exist_ok=True)

    st.subheader("Загрузка нового файла погоды")

    uploaded_file = st.file_uploader(
        "Выберите CSV-файл с погодными данными",
        type=["csv"],
        key="weather_uploader"
    )

    if uploaded_file is not None:
        filename = uploaded_file.name.strip()
        if not filename.lower().startswith('weather_data_'):
            warning_msg = "Загружен файл без названия weather_data_"
            logger.warning(warning_msg)
            st.warning("Пожалуйста, загрузите файл с расширением weather_data_**.csv**")
            return

        if not filename.lower().endswith('.csv'):
            warning_msg = "Загружен файл без расширения .csv"
            logger.warning(warning_msg)
            st.warning("Пожалуйста, загрузите файл с расширением weather_data_**.csv**")
            return

        try:
            logger.info(f"Начата валидация файла погоды: {filename}")

            # Читаем только заголовки
            df = pd.read_csv(uploaded_file, nrows=0)
            actual_columns = set(df.columns)
            missing_columns = REQUIRED_COLUMNS - actual_columns

            if missing_columns:
                error_msg = f"Файл '{filename}' не содержит обязательные столбцы: {sorted(missing_columns)}"
                logger.warning(error_msg)
                st.error(
                    "Файл не содержит все обязательные столбцы.\n\n"
                    "**Отсутствующие параметры:**\n"
                    + "\n".join(f"- `{col}`" for col in sorted(missing_columns))
                )
                st.info(
                    "Обязательные столбцы: " + ", ".join(f"`{c}`" for c in sorted(REQUIRED_COLUMNS))
                )
                return

            # Сохраняем файл
            file_path = weather_data_dir / filename
            uploaded_file.seek(0)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            success_msg = f"Файл погоды '{filename}' успешно сохранён в {weather_data_dir}"
            logger.info(success_msg)
            st.success(f"Файл **{filename}** успешно загружен и сохранён в `{weather_data_dir}`")

            if "show_upload_weather" in st.session_state:
                st.session_state.show_upload_weather = False

        except pd.errors.EmptyDataError:
            error_msg = "Загружен пустой CSV-файл"
            logger.error(error_msg)
            st.error("Файл пуст. Загрузите корректный CSV-файл с данными.")
        except pd.errors.ParserError as e:
            error_msg = f"Ошибка парсинга CSV ({filename}): {e}"
            logger.error(error_msg, exc_info=True)
            st.error(f"Ошибка при разборе CSV: {str(e)}")
        except Exception as e:
            error_msg = f"Неизвестная ошибка при обработке файла погоды ({filename}): {e}"
            logger.error(error_msg, exc_info=True)
            st.error(f"Ошибка при обработке файла: {e}")
    else:
        st.info("Ожидается загрузка CSV-файла с погодными данными.")
