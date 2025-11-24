# modules/ui_components.py
"""
Main UI composition module. Orchestrates all components.
All displayed text is in Russian.
"""

import streamlit as st
import os
import datetime
from .logger import get_app_logger  # ← добавлен импорт логгера
from .global_weather import render_global_weather
from .config_forms import (
    show_supplies_dialog,
    show_fires_dialog,
    show_temperature_dialog,
    show_weather_dialog
)
from .sections import render_section
from .schedule_manager import load_schedule
from constants import DATA_DIR
from .add_weather_file import handle_add_weather_file
from .add_predict_file import show_prediction_requirements, handle_predict_file_upload
from .generate_report import (
    generate_comprehensive_report,
    run_prediction_and_generate_report
)
from .model_trainer import train_and_save_model

# Инициализация логгера
logger = get_app_logger()


def render_header():
    """Renders the main header with date, metrics, and action buttons (with gradient styling)."""
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
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, = st.columns(1)
    with col1:
        back_to_main_btn = st.button("Главная", key="back_to_main")

    st.markdown("## Добавить погоду")
    col1, = st.columns(1)
    with col1:
        add_weather_btn = st.button("Добавить погоду", key="add_weather_file")

    st.markdown("## Прогноз")

    col2, col4, col6 = st.columns(3)
    with col2:
        upload_predict_btn = st.button("Добавить predict-файл", key="upload_predict")
    with col4:
        predict_btn = st.button("Запустить прогноз", key="run_prediction")
    with col6:
        model_btn = st.button("Пересоздать модель", key="model_prediction")

    # Handle button states
    if back_to_main_btn:
        st.session_state.show_upload_weather = False
        st.session_state.show_upload_predict = False
        st.session_state.trigger_report = False
        st.session_state.trigger_prediction = False
        logger.info("Пользователь вернулся на главную страницу")

    elif add_weather_btn:
        st.session_state.show_upload_weather = True
        st.session_state.show_upload_predict = False
        st.session_state.trigger_report = False
        st.session_state.trigger_prediction = False
        logger.info("Активирован режим загрузки погодного файла")

    elif upload_predict_btn:
        st.session_state.show_upload_predict = True
        st.session_state.show_upload_weather = False
        st.session_state.trigger_report = False
        st.session_state.trigger_prediction = False
        logger.info("Активирован режим загрузки predict-файла")

    elif predict_btn:
        st.session_state.trigger_prediction = True
        st.session_state.show_upload_weather = False
        st.session_state.show_upload_predict = False
        st.session_state.trigger_report = False
        logger.info("Запущен процесс прогнозирования")

    elif model_btn:
        try:
            logger.info("Запущено переобучение модели")
            train_and_save_model()
            st.sidebar.success("Модель успешно пересоздана!")
            logger.info("Модель успешно пересоздана")
        except Exception as e:
            error_msg = f"Ошибка при переобучении модели: {e}"
            logger.error(error_msg, exc_info=True)
            st.sidebar.error(f"Ошибка при обучении: {e}")


def render_buttons():
    """Renders quick-create buttons for each category."""
    st.markdown("## Быстрое создание графиков")
    cols_btn = st.columns(4)
    if cols_btn[0].button("Выгрузка/Отгрузка", use_container_width=True):
        logger.info("Открыт диалог настройки графика: Выгрузка/Отгрузка")
        show_supplies_dialog()
    if cols_btn[1].button("Самовозгорания", use_container_width=True):
        logger.info("Открыт диалог настройки графика: Самовозгорания")
        show_fires_dialog()
    if cols_btn[2].button("Температура", use_container_width=True):
        logger.info("Открыт диалог настройки графика: Температура")
        show_temperature_dialog()
    if cols_btn[3].button("Погода", use_container_width=True):
        logger.info("Открыт диалог настройки графика: Погода")
        show_weather_dialog()


def render_instructions():
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


def render_app():
    logger.info("Запуск основного UI приложения")
    if "initialized" not in st.session_state:
        saved = load_schedule()
        st.session_state.graphs = {
            "supplies": saved.get("supplies", []),
            "fires": saved.get("fires", []),
            "temperature": saved.get("temperature", []),
            "weather": saved.get("weather", [])
        }
        st.session_state.next_id = saved.get("next_id", 0)
        st.session_state.initialized = True
        logger.debug("Состояние приложения инициализировано из schedule.json")

    # Initialize all flags
    for flag in [
        "show_upload_weather",
        "show_upload_predict",
        "trigger_report",
        "trigger_prediction"
    ]:
        if flag not in st.session_state:
            st.session_state[flag] = False

    render_header()

    if st.session_state.show_upload_weather:
        handle_add_weather_file()
    elif st.session_state.show_upload_predict:
        show_prediction_requirements()
        handle_predict_file_upload()
    elif st.session_state.trigger_report:
        generate_comprehensive_report()
    elif st.session_state.trigger_prediction:
        run_prediction_and_generate_report()
    else:
        render_instructions()
        render_global_weather()
        render_buttons()
        st.divider()
        render_main_tabs()
