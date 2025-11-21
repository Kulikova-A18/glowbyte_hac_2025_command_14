# modules/ui_components.py

"""
Module for UI components and interaction logic.
"""

import streamlit as st
from modules.data_loader import load_csv
from modules.plotter import plot_series
from modules.schedule_manager import save_schedule
from constants import FIRE_FILE, SUPPLIES_FILE, TEMP_FILE, WEATHER_DIR
import logging
import os

def show_standard_config(category, file_path, default_date_col, default_y_cols, title_base):
    """
    Displays the configuration form for a standard data category.

    @param category: Key for the category (e.g., 'supplies', 'fires').
    @param file_path: Path to the CSV file for this category.
    @param default_date_col: Default date column name.
    @param default_y_cols: Default Y-axis columns.
    @param title_base: Base title for the expander.
    """
    if st.session_state.show_config[category]:
        with st.expander(f"Настройка: {title_base}", expanded=True):
            df_preview = load_csv(file_path)
            if df_preview.empty:
                st.error("Не удалось загрузить файл")
                st.session_state.show_config[category] = False
                st.rerun()
                return

            date_candidates = [col for col in df_preview.columns if "дата" in col.lower() or "date" in col.lower()]
            if not date_candidates:
                date_candidates = df_preview.select_dtypes(include=["object", "datetime"]).columns.tolist()
            date_col = st.selectbox("Колонка с датой", date_candidates, key=f"date_{category}")

            value_cols = [col for col in df_preview.columns if col != date_col]
            y_cols = st.multiselect("Параметры (ось Y)", value_cols, default=default_y_cols, key=f"ycols_{category}")

            params_str = "_".join(y_cols[:3]) if y_cols else "без_параметров"
            auto_name = f"{os.path.splitext(os.path.basename(file_path))[0]}_{params_str}"
            custom_name = st.text_input("Название графика", key=f"name_{category}")
            st.caption(f"Если оставить пустым, будет использовано: {auto_name}")
            display_name = custom_name.strip() if custom_name.strip() else auto_name

            days = st.slider("Данные за последние (дней)", 1, 365, 90, key=f"days_{category}")
            plot_type = st.selectbox("Тип графика", ["Линейный", "Гистограмма", "Точечный (scatter)"], key=f"type_{category}")

            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button("Создать график", key=f"create_{category}"):
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
                st.session_state.show_config[category] = False
                persist_changes()
                logging.info(f"Добавлен график в {category}: {display_name}")
                st.rerun()

            if col_btn2.button("Отмена", key=f"cancel_{category}"):
                st.session_state.show_config[category] = False
                st.rerun()

def show_weather_config():
    """
    Displays the configuration form for weather data with year selection.
    """
    if st.session_state.show_config["weather"]:
        if not os.path.exists(WEATHER_DIR):
            st.error("Папка weather_data не найдена")
            st.session_state.show_config["weather"] = False
            st.rerun()
            return

        weather_files = [f for f in os.listdir(WEATHER_DIR) if f.endswith(".csv")]
        if not weather_files:
            st.error("Папка weather_data пуста")
            st.session_state.show_config["weather"] = False
            st.rerun()
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
            st.session_state.show_config["weather"] = False
            st.rerun()
            return

        years = sorted(set(years))
        with st.expander("Настройка: Погода", expanded=True):
            selected_year = st.selectbox("Выберите год", years, key="year_weather_select")
            selected_file = f"weather_data_{selected_year}.csv"
            file_path = os.path.join(WEATHER_DIR, selected_file)

            df_preview = load_csv(file_path)
            if df_preview.empty:
                st.error("Не удалось загрузить файл")
                st.session_state.show_config["weather"] = False
                st.rerun()
                return

            date_candidates = [col for col in df_preview.columns if "дата" in col.lower() or "date" in col.lower()]
            if not date_candidates:
                date_candidates = df_preview.select_dtypes(include=["object", "datetime"]).columns.tolist()
            date_col = st.selectbox("Колонка с датой", date_candidates, key="date_weather")

            value_cols = [col for col in df_preview.columns if col != date_col]
            y_cols = st.multiselect("Параметры (ось Y)", value_cols, default=["t", "precipitation"], key="ycols_weather")

            params_str = "_".join(y_cols[:3]) if y_cols else "без_параметров"
            auto_name = f"{os.path.splitext(selected_file)[0]}_{params_str}"
            custom_name = st.text_input("Название графика", key="name_weather")
            st.caption(f"Если оставить пустым, будет использовано: {auto_name}")
            display_name = custom_name.strip() if custom_name.strip() else auto_name

            days = st.slider("Данные за последние (дней)", 1, 365, 90, key="days_weather")
            plot_type = st.selectbox("Тип графика", ["Линейный", "Гистограмма", "Точечный (scatter)"], key="type_weather")

            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button("Создать график", key="create_weather"):
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
                st.session_state.show_config["weather"] = False
                persist_changes()
                logging.info(f"Добавлен график в weather: {display_name}")
                st.rerun()

            if col_btn2.button("Отмена", key="cancel_weather"):
                st.session_state.show_config["weather"] = False
                st.rerun()

def persist_changes():
    """
    Saves the current state of graphs to the schedule file.
    """
    data_to_save = {
        "supplies": st.session_state.graphs["supplies"],
        "fires": st.session_state.graphs["fires"],
        "temperature": st.session_state.graphs["temperature"],
        "weather": st.session_state.graphs["weather"],
        "next_id": st.session_state.next_id
    }
    save_schedule(data_to_save)

def render_section(section_key, section_title):
    """
    Renders a section of graphs based on the category key.

    @param section_key: Key for the category (e.g., 'supplies', 'fires').
    @param section_title: Title to display for the section.
    """
    st.markdown(f"## {section_title}")
    if st.session_state.graphs[section_key]:
        plots = st.session_state.graphs[section_key]
        for i in range(0, len(plots), 2):
            cols = st.columns(2)
            for j, cfg in enumerate(plots[i:i+2]):
                with cols[j]:
                    st.markdown(f"### {cfg['title']}")
                    df = load_csv(cfg["file"])
                    if not df.empty:
                        plot_series(
                            df=df,
                            date_col=cfg["date_col"],
                            y_cols=cfg["y_cols"],
                            days_lookback=cfg["days"],
                            title=cfg["title"],
                            plot_type=cfg["plot_type"],
                            chart_key=f"chart_{section_key}_{cfg['id']}"
                        )
                    if st.button("Удалить", key=f"del_{section_key}_{cfg['id']}"):
                        st.session_state.graphs[section_key] = [
                            g for g in st.session_state.graphs[section_key] if g["id"] != cfg["id"]
                        ]
                        persist_changes()
                        logging.info(f"Удалён график ID {cfg['id']} из {section_key}")
                        st.rerun()
    else:
        st.info(f"Нет графиков. Нажмите кнопку выше.")

# -------------------------------
# Main UI Components

def render_header():
    """
    Renders the main header and metrics.
    """
    import datetime
    from constants import DATA_DIR

    st.set_page_config(page_title="Прогноз самовозгорания угля", layout="wide")
    st.title("Прогноз самовозгорания угля")

    now = datetime.datetime.now()
    all_files = []
    for root, _, files in os.walk(DATA_DIR):
        for f in files:
            if f.endswith(".csv"):
                all_files.append(f)

    st.metric("Текущая дата и время", now.strftime("%d.%m.%Y %H:%M"))
    st.metric("Всего CSV-файлов", len(all_files))
    total_graphs = sum(len(v) for v in st.session_state.graphs.values())
    st.metric("Создано графиков", total_graphs)

def render_buttons():
    """
    Renders the main category buttons.
    """
    st.subheader("Быстрое создание графиков")
    cols_btn = st.columns(4)

    if cols_btn[0].button("1. Выгрузка на склад и отгрузка", key="btn_supplies"):
        st.session_state.show_config["supplies"] = True
    if cols_btn[1].button("2. Информация о самовозгораниях", key="btn_fires"):
        st.session_state.show_config["fires"] = True
    if cols_btn[2].button("3. Показатели температуры в штабелях", key="btn_temp"):
        st.session_state.show_config["temperature"] = True
    if cols_btn[3].button("4. Погода", key="btn_weather"):
        st.session_state.show_config["weather"] = True

def render_instructions():
    """
    Renders the user instructions in the sidebar.
    """
    st.sidebar.markdown("### Инструкция пользователя")
    st.sidebar.write("""
    1. Нажмите одну из 4 кнопок.
    2. Настройте:
       - Тип графика
       - Параметры (ось Y)
       - Период (дней)
       - Название (или оставьте пустым)
    3. Нажмите «Создать график».
    4. Все настройки сохраняются в файл `schedule.json`.
    5. При следующем запуске графики загрузятся автоматически.
    """)

