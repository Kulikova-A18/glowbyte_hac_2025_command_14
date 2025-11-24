# modules/plotter.py
"""
Module for plotting time-series data.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from .logger import get_app_logger  # ← добавлен импорт логгера

# Инициализация логгера
logger = get_app_logger()


def plot_series(
    df,
    date_col,
    y_cols,
    days_lookback,
    title,
    plot_type,
    chart_key,
    group_by_day=True,
    show_back_button=True
):
    """
    Plots a time-series graph.

    @param df: pd.DataFrame
        DataFrame with data.
    @param date_col: str
        Name of the date column.
    @param y_cols: List[str]
        List of Y-axis column names.
    @param days_lookback: int
        Number of days to show.
    @param title: str
        Plot title.
    @param plot_type: str
        One of: 'Линейный', 'Гистограмма', 'Точечный (scatter)'.
    @param chart_key: str
        Unique key for Streamlit components.
    @param group_by_day: bool
        If True — aggregate by day (default). If False — show raw data.
    @param show_back_button: bool
        If True — show "Back to main" button above the chart.
    """
    logger.debug(f"Запуск построения графика: {title}, тип={plot_type}, дней={days_lookback}")

    if date_col not in df.columns:
        warning_msg = f"Колонка даты '{date_col}' не найдена в данных"
        logger.warning(warning_msg)
        st.warning(warning_msg)
        return

    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col]).copy()
    if df.empty:
        logger.info("Нет корректных дат для отображения")
        st.info("Нет корректных дат")
        return

    max_date = df[date_col].max()
    min_date = max_date - pd.Timedelta(days=days_lookback)
    df = df[(df[date_col] >= min_date) & (df[date_col] <= max_date)].copy()
    if df.empty:
        msg = f"Нет данных за последние {days_lookback} дней (до {max_date.date()})"
        logger.info(msg)
        st.info(msg)
        return

    if group_by_day:
        df["День"] = df[date_col].dt.date
        agg_dict = {}
        for col in y_cols:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                agg_dict[col] = "mean"
        if not agg_dict:
            warning_msg = "Нет числовых колонок для отображения"
            logger.warning(warning_msg)
            st.warning(warning_msg)
            return
        df_agg = df.groupby("День").agg(agg_dict).reset_index()
        df_agg["День"] = pd.to_datetime(df_agg["День"])
        x_col = "День"
    else:
        df_agg = df.copy()
        x_col = date_col

    # Ensure all y_cols exist in df_agg
    y_cols = [col for col in y_cols if col in df_agg.columns]
    if not y_cols:
        warning_msg = "Ни одна из указанных Y-колонок не найдена в данных"
        logger.warning(warning_msg)
        st.warning(warning_msg)
        return

    try:
        if plot_type == "Линейный":
            fig = go.Figure()
            for col in y_cols:
                fig.add_trace(go.Scatter(x=df_agg[x_col], y=df_agg[col], mode='lines+markers', name=col))
            fig.update_layout(title=title, xaxis_title="Дата", yaxis_title="Значение")

        elif plot_type == "Гистограмма":
            df_melted = df_agg.melt(id_vars=[x_col], value_vars=y_cols, var_name="Метрика", value_name="Значение")
            fig = px.bar(
                df_melted,
                x=x_col,
                y="Значение",
                color="Метрика",
                title=title,
                barmode="group"
            )
            fig.update_layout(xaxis_title="Дата", yaxis_title="Значение")

        elif plot_type == "Точечный (scatter)":
            fig = go.Figure()
            for col in y_cols:
                fig.add_trace(go.Scatter(x=df_agg[x_col], y=df_agg[col], mode='markers', name=col))
            fig.update_layout(title=title, xaxis_title="Дата", yaxis_title="Значение")

        else:
            warning_msg = f"Неизвестный тип графика: {plot_type}"
            logger.warning(warning_msg)
            st.warning(warning_msg)
            return

        st.plotly_chart(fig, use_container_width=True, key=chart_key)
        logger.info(f"График успешно отображён: {title}")

    except Exception as e:
        error_msg = f"Ошибка при построении графика '{title}': {e}"
        logger.error(error_msg, exc_info=True)
        st.error("Ошибка при отображении графика. Подробности в логах.")
