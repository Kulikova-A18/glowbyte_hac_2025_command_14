# app.py

"""
Main entry point for the coal self-ignition prediction Streamlit app.
"""

import streamlit as st
from modules.ui_components import render_header, render_buttons, render_section, show_standard_config, show_weather_config, render_instructions
from modules.schedule_manager import load_schedule
from constants import FIRE_FILE, SUPPLIES_FILE, TEMP_FILE, WEATHER_DIR

# Initialize session state
if "initialized" not in st.session_state:
    saved = load_schedule()
    st.session_state.graphs = {
        "supplies": saved["supplies"],
        "fires": saved["fires"],
        "temperature": saved["temperature"],
        "weather": saved["weather"]
    }
    st.session_state.next_id = saved.get("next_id", 0)
    st.session_state.show_config = {"supplies": False, "fires": False, "temperature": False, "weather": False}
    st.session_state.initialized = True

# Render UI
render_header()
render_buttons()

# Show active config forms
show_standard_config("supplies", SUPPLIES_FILE, "ВыгрузкаНаСклад", ["На склад, тн", "На судно, тн"], "Выгрузка и отгрузка")
show_standard_config("fires", FIRE_FILE, "Дата составления", ["Штабель"], "Самовозгорания")
show_standard_config("temperature", TEMP_FILE, "Дата акта", ["Максимальная температура"], "Температура")
show_weather_config()

# Render graph sections
render_section("supplies", "Выгрузка на склад и отгрузка")
render_section("fires", "Информация о самовозгораниях")
render_section("temperature", "Показатели температуры в штабелях")
render_section("weather", "Погода")

# Render instructions
render_instructions()
