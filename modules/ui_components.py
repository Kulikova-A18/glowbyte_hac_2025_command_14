"""
Main UI composition module. Orchestrates all components.
All displayed text is in Russian.
"""

import streamlit as st
import os
import datetime
from modules.global_weather import render_global_weather
from modules.config_forms import (
    show_supplies_dialog,
    show_fires_dialog,
    show_temperature_dialog,
    show_weather_dialog
)
from modules.sections import render_section
from modules.schedule_manager import load_schedule
from constants import DATA_DIR
from modules.add_weather_file import handle_add_weather_file
from modules.generate_report import generate_comprehensive_report


def render_header():
    """Renders the main header with date, metrics, and action buttons."""
    st.set_page_config(
        page_title="Прогноз самовозгорания угля",
        layout="wide",
        initial_sidebar_state="expanded",
        page_icon=""
    )

    st.markdown("""
    <style>
    body {
        background-color: #f5f5f5;
        color: #333333;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .stButton > button {
        background: linear-gradient(to bottom right, #4a90e2, #7fbaf5) !important;
        color: white !important;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        padding: 8px 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.15);
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(to bottom right, #3a7bc8, #6aa5d9) !important;
        box-shadow: 0 3px 6px rgba(0,0,0,0.2) !important;
    }
    .header-container {
        background: linear-gradient(to bottom right, #4a90e2, #7fbaf5);
        color: white;
        border-radius: 12px;
        padding: 28px;
        margin-bottom: 24px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)

    now = datetime.datetime.now()
    all_files = []
    for root, _, files in os.walk(DATA_DIR):
        for f in files:
            if f.endswith(".csv"):
                all_files.append(f)
    total_graphs = sum(len(v) for v in st.session_state.graphs.values())

    st.markdown(
        f"""
        <div class="header-container">
            <div style="font-size: 2.6em; font-weight: 600; margin-bottom: 6px;">
                Прогноз самовозгорания угля
            </div>
            <div style="font-size: 7em; font-weight: 600; margin-bottom: 24px;">
                {now.strftime("%d.%m.%Y %H:%M")}
            </div>
            <div style="font-size: 1em; opacity: 0.95;">
                CSV-файлов: {len(all_files)} &nbsp; • &nbsp; Создано графиков: {total_graphs}
            </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        add_weather_btn = st.button("Добавить новый файл погоды", key="add_weather_file")
    with col2:
        generate_report_btn = st.button("Сгенерировать отчет", key="generate_report")

    st.markdown("</div>", unsafe_allow_html=True)

    if add_weather_btn:
        st.session_state.show_upload_weather = True
        st.session_state.trigger_report = False  # mutually exclusive if needed
    if generate_report_btn:
        st.session_state.trigger_report = True
        st.session_state.show_upload_weather = False


def render_buttons():
    """Renders quick-create buttons for each category."""
    st.markdown("## Быстрое создание графиков")
    cols_btn = st.columns(4)
    if cols_btn[0].button("Выгрузка/Отгрузка", use_container_width=True):
        show_supplies_dialog()
    if cols_btn[1].button("Самовозгорания", use_container_width=True):
        show_fires_dialog()
    if cols_btn[2].button("Температура", use_container_width=True):
        show_temperature_dialog()
    if cols_btn[3].button("Погода", use_container_width=True):
        show_weather_dialog()


def render_instructions():
    """Renders user instructions in the sidebar."""
    st.sidebar.button("Инструкция пользователя", key="sidebar_instructions", use_container_width=True)
    st.sidebar.markdown("### Как пользоваться")
    st.sidebar.write("""
    1. Нажмите одну из 4 кнопок.
    2. Настройте:
       - Колонку с датой
       - Параметры (ось Y)
       - Период (дней)
       - Название (или оставьте пустым)
    3. Нажмите «Создать график».
    4. Все настройки сохраняются в файл `schedule.json`.
    5. При следующем запуске графики загрузятся автоматически.
    """)


def render_main_tabs():
    """Renders tabbed sections for each chart category."""
    tab_titles = ["Выгрузка/Отгрузка", "Самовозгорания", "Температура", "Погода"]
    tabs = st.tabs(tab_titles)

    with tabs[0]:
        render_section("supplies", "Выгрузка и отгрузка на склад")
    with tabs[1]:
        render_section("fires", "Информация о самовозгораниях")
    with tabs[2]:
        render_section("temperature", "Показатели температуры в штабелях")
    with tabs[3]:
        render_section("weather", "Погодные условия")


# Entry point
def render_app():
    """
    Main entry point for the entire UI.
    Initializes session state and renders all components.
    """
    if "initialized" not in st.session_state:
        saved = load_schedule()
        st.session_state.graphs = {
            "supplies": saved["supplies"],
            "fires": saved["fires"],
            "temperature": saved["temperature"],
            "weather": saved["weather"]
        }
        st.session_state.next_id = saved.get("next_id", 0)
        st.session_state.initialized = True

    # Initialize optional flags
    if "show_upload_weather" not in st.session_state:
        st.session_state.show_upload_weather = False
    if "trigger_report" not in st.session_state:
        st.session_state.trigger_report = False

    render_header()

    # Conditionally render dynamic sections
    if st.session_state.show_upload_weather:
        handle_add_weather_file()

    if st.session_state.trigger_report:
        generate_comprehensive_report()

    render_instructions()
    render_global_weather()
    render_buttons()
    st.divider()
    render_main_tabs()
