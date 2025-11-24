# modules/data_loader.py
"""
Module for loading and preprocessing CSV data.
"""

import streamlit as st
import pandas as pd
from .logger import get_app_logger

logger = get_app_logger()

def load_csv(file_path):
    """
    Loads a CSV file and attempts to parse date columns.

    @param file_path: Path to the CSV file to load.
    @return: Loaded DataFrame or empty DataFrame on failure.
    """
    try:
        df = pd.read_csv(file_path)
        logger.debug(f"Файл загружен: {file_path} ({df.shape[0]} строк, {df.shape[1]} колонок)")

        for col in df.columns:
            if "дата" in col.lower() or "date" in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce')
                logger.debug(f"Колонка '{col}' распознана как дата")

        return df

    except FileNotFoundError:
        error_msg = f"Файл не найден: {file_path}"
        logger.error(error_msg)
        st.error(f"Файл не найден: {file_path}")
        return pd.DataFrame()

    except pd.errors.EmptyDataError:
        error_msg = f"Файл пуст: {file_path}"
        logger.warning(error_msg)
        st.error(f"Файл пуст: {file_path}")
        return pd.DataFrame()

    except pd.errors.ParserError as e:
        error_msg = f"Ошибка парсинга CSV: {file_path} — {e}"
        logger.error(error_msg, exc_info=True)
        st.error(f"Ошибка формата CSV в файле: {file_path}")
        return pd.DataFrame()

    except Exception as e:
        error_msg = f"Неизвестная ошибка при загрузке файла: {file_path} — {e}"
        logger.error(error_msg, exc_info=True)
        st.error(f"Ошибка при загрузке {file_path}")
        return pd.DataFrame()
