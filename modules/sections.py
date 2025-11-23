# modules/sections.py

"""
Module for rendering chart sections (tabs) with delete functionality.
All UI text is in Russian.
"""

import streamlit as st
from modules.data_loader import load_csv
from modules.plotter import plot_series
from modules.config_forms import _persist_changes
import logging


def render_section(section_key: str, section_title: str):
    """
    Renders a section of user-created charts.

    @param section_key: Internal key (e.g., 'supplies', 'weather').
    @param section_title: Display title for the section.
    @return: None
    """
    st.markdown(f"## {section_title}")
    if st.session_state.graphs[section_key]:
        plots = st.session_state.graphs[section_key]
        for i in range(0, len(plots), 2):
            cols = st.columns(2)
            for j, cfg in enumerate(plots[i:i+2]):
                with cols[j]:
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
                            _persist_changes()
                            logging.info(f"Удалён график ID {cfg['id']} из {section_key}")
                            st.rerun()
                    else:
                        st.warning("Данные не загружены.")
    else:
        st.info("Нет графиков. Нажмите кнопку выше для создания.")
