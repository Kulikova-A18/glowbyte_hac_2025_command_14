# app.py
import streamlit as st

st.set_page_config(
    page_title="Прогноз самовозгорания угля",
    layout="wide",
    initial_sidebar_state="expanded"
)

from modules.ui_components import render_app
render_app()
