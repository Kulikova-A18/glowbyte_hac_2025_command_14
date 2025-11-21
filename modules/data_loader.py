# modules/data_loader.py

"""
Module for loading and preprocessing CSV data.
"""

import streamlit as st
import pandas as pd
import logging

def load_csv(file_path):
    """
    Loads a CSV file and attempts to parse date columns.

    @param file_path: Path to the CSV file to load.
    @return: Loaded DataFrame or empty DataFrame on failure.
    """
    try:
        df = pd.read_csv(file_path)
        for col in df.columns:
            if "дата" in col.lower() or "date" in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Ошибка при загрузке {file_path}: {e}")
        logging.error(f"Ошибка загрузки файла {file_path}: {e}")
        return pd.DataFrame()

