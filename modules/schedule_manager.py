# modules/schedule_manager.py
"""
Module for saving and loading graph configurations.
"""

import json
import os
import streamlit as st
from .logger import get_app_logger  # ← используем ваш кастомный логгер
from constants import SCHEDULE_FILE

# Инициализация логгера
logger = get_app_logger()


def load_schedule():
    """
    Loads graph configurations from the schedule file.

    @return: Dictionary containing graph data or default structure.
    """
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info("Настройки графиков успешно загружены из schedule.json")
            return data
        except json.JSONDecodeError as e:
            error_msg = f"Некорректный формат JSON в schedule.json: {e}"
            logger.error(error_msg, exc_info=True)
            st.warning("Не удалось загрузить сохранённые графики: повреждён файл конфигурации")
        except Exception as e:
            error_msg = f"Ошибка при загрузке schedule.json: {e}"
            logger.error(error_msg, exc_info=True)
            st.warning("Не удалось загрузить сохранённые графики")
    else:
        logger.info("Файл schedule.json не найден, используется конфигурация по умолчанию")

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

    @param data: Dictionary containing graph data to save.
    """
    try:
        with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("Настройки графиков успешно сохранены в schedule.json")
    except PermissionError:
        error_msg = "Нет прав на запись в файл schedule.json"
        logger.error(error_msg)
        st.error("Не удалось сохранить настройки: отказано в доступе к файлу")
    except Exception as e:
        error_msg = f"Ошибка при сохранении schedule.json: {e}"
        logger.error(error_msg, exc_info=True)
        st.error("Не удалось сохранить настройки")
