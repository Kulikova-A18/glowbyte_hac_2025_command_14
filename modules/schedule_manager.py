# modules/schedule_manager.py

"""
Module for saving and loading graph configurations.
"""

import json
import os
import streamlit as st
import logging
from constants import SCHEDULE_FILE

def load_schedule():
    """
    Loads graph configurations from the schedule file.

    @return: Dictionary containing graph data or default structure.
    """
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                logging.info("Настройки загружены из schedule.json")
                return data
        except Exception as e:
            st.warning("Не удалось загрузить сохранённые графики")
            logging.error(f"Ошибка загрузки schedule.json: {e}")
    return {
        "supplies": [],
        "fires": [],
        "temperature": [],
        "weather": [],
        "next_id": 0
    }

def save_schedule(data):
    """
    Saves graph configurations to the schedule file.

    @param  Dictionary containing graph data to save.
    """
    try:
        with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info("Настройки сохранены в schedule.json")
    except Exception as e:
        st.error("Не удалось сохранить настройки")
        logging.error(f"Ошибка сохранения schedule.json: {e}")

