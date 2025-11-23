# modules/config_forms.py

"""
Module containing configuration dialogs and form helpers for chart creation.
All UI text is in Russian.
"""

import streamlit as st
import os
import pandas as pd
from modules.data_loader import load_csv
from modules.schedule_manager import save_schedule
from constants import FIRE_FILE, SUPPLIES_FILE, TEMP_FILE, WEATHER_DIR


def _setup_standard_form(category: str, file_path: str, df_preview: pd.DataFrame, default_y_cols: list):
    """
    Renders a standard configuration form for chart creation.

    @param category: Key for the chart category (e.g., 'supplies', 'fires').
    @param file_path: Path to the CSV file.
    @param df_preview: DataFrame preview for column detection.
    @param default_y_cols: Suggested default columns for Y-axis.
    @return: None
    """
    date_candidates = [col for col in df_preview.columns if "дата" in col.lower() or "date" in col.lower()]
    if not date_candidates:
        date_candidates = df_preview.select_dtypes(include=["object", "datetime"]).columns.tolist()

    date_col = st.selectbox("Колонка с датой", date_candidates, key=f"date_{category}")
    value_cols = [col for col in df_preview.columns if col != date_col]

    safe_defaults = [col for col in default_y_cols if col in value_cols]
    if not safe_defaults and value_cols:
        safe_defaults = [value_cols[0]]

    y_cols = st.multiselect("Параметры (ось Y)", value_cols, default=safe_defaults, key=f"ycols_{category}")

    params_str = "_".join(y_cols[:3]) if y_cols else "без_параметров"
    auto_name = f"{os.path.splitext(os.path.basename(file_path))[0]}_{params_str}"
    custom_name = st.text_input("Название графика", key=f"name_{category}")
    st.caption(f"Если оставить пустым, будет использовано: `{auto_name}`")
    display_name = custom_name.strip() if custom_name.strip() else auto_name

    days = st.slider("Данные за последние (дней)", 1, 365, 90, key=f"days_{category}")
    plot_type = st.selectbox("Тип графика", ["Линейный", "Гистограмма", "Точечный (scatter)"], key=f"type_{category}")

    col_btn1, col_btn2 = st.columns(2)
    if col_btn1.button("Создать график"):
        st.session_state.graphs[category].append({
            "id": st.session_state.next_id,
            "file": file_path,
            "date_col": date_col,
            "y_cols": y_cols,
            "days": days,
            "plot_type": plot_type,
            "title": display_name
        })
        st.session_state.next_id += 1
        _persist_changes()
        st.rerun()
    if col_btn2.button("Отмена"):
        st.rerun()


def _persist_changes():
    """Saves current graph configuration to schedule.json."""
    data_to_save = {
        "supplies": st.session_state.graphs["supplies"],
        "fires": st.session_state.graphs["fires"],
        "temperature": st.session_state.graphs["temperature"],
        "weather": st.session_state.graphs["weather"],
        "next_id": st.session_state.next_id
    }
    save_schedule(data_to_save)


# Dialogs

@st.dialog("Настройка: Выгрузка и отгрузка")
def show_supplies_dialog():
    df_preview = load_csv(SUPPLIES_FILE)
    if df_preview.empty:
        st.error("Не удалось загрузить файл supplies.csv")
        return
    _setup_standard_form("supplies", SUPPLIES_FILE, df_preview, ["На склад, тн", "На судно, тн"])


@st.dialog("Настройка: Информация о самовозгораниях")
def show_fires_dialog():
    df_preview = load_csv(FIRE_FILE)
    if df_preview.empty:
        st.error("Не удалось загрузить файл fires.csv")
        return
    possible_defaults = [col for col in df_preview.columns if col != "Дата составления"]
    defaults = ["Штабель"] if "Штабель" in possible_defaults else possible_defaults[:2] if possible_defaults else []
    _setup_standard_form("fires", FIRE_FILE, df_preview, defaults)


@st.dialog("Настройка: Показатели температуры в штабелях")
def show_temperature_dialog():
    df_preview = load_csv(TEMP_FILE)
    if df_preview.empty:
        st.error("Не удалось загрузить файл temperature.csv")
        return
    _setup_standard_form("temperature", TEMP_FILE, df_preview, ["Максимальная температура"])


@st.dialog("Настройка: Погода")
def show_weather_dialog():
    if not os.path.exists(WEATHER_DIR):
        st.error("Папка weather_data не найдена")
        return

    weather_files = [f for f in os.listdir(WEATHER_DIR) if f.endswith(".csv")]
    if not weather_files:
        st.error("Папка weather_data пуста")
        return

    years = []
    for f in weather_files:
        try:
            year = int(f.replace("weather_data_", "").replace(".csv", ""))
            years.append(year)
        except ValueError:
            continue

    if not years:
        st.error("Не найдено файлов в формате weather_data_YYYY.csv")
        return

    years = sorted(set(years))
    selected_year = st.selectbox("Выберите год", years, key="year_weather_select")
    selected_file = f"weather_data_{selected_year}.csv"
    file_path = os.path.join(WEATHER_DIR, selected_file)

    df_preview = load_csv(file_path)
    if df_preview.empty:
        st.error(f"Не удалось загрузить {selected_file}")
        return

    date_candidates = [col for col in df_preview.columns if "дата" in col.lower() or "date" in col.lower()]
    if not date_candidates:
        date_candidates = df_preview.select_dtypes(include=["object", "datetime"]).columns.tolist()

    date_col = st.selectbox("Колонка с датой", date_candidates, key="date_weather")
    value_cols = [col for col in df_preview.columns if col != date_col]

    safe_defaults = ["t", "precipitation"]
    safe_defaults = [col for col in safe_defaults if col in value_cols]
    if not safe_defaults and value_cols:
        safe_defaults = [value_cols[0]]

    y_cols = st.multiselect("Параметры (ось Y)", value_cols, default=safe_defaults, key="ycols_weather")

    params_str = "_".join(y_cols[:3]) if y_cols else "без_параметров"
    auto_name = f"{os.path.splitext(selected_file)[0]}_{params_str}"
    custom_name = st.text_input("Название графика", key="name_weather")
    st.caption(f"Если оставить пустым, будет использовано: `{auto_name}`")
    display_name = custom_name.strip() if custom_name.strip() else auto_name

    days = st.slider("Данные за последние (дней)", 1, 365, 90, key="days_weather")
    plot_type = st.selectbox("Тип графика", ["Линейный", "Гистограмма", "Точечный (scatter)"], key="type_weather")

    col_btn1, col_btn2 = st.columns(2)
    if col_btn1.button("Создать график"):
        st.session_state.graphs["weather"].append({
            "id": st.session_state.next_id,
            "file": file_path,
            "date_col": date_col,
            "y_cols": y_cols,
            "days": days,
            "plot_type": plot_type,
            "title": display_name
        })
        st.session_state.next_id += 1
        _persist_changes()
        st.rerun()
    if col_btn2.button("Отмена"):
        st.rerun()
