# modules/plotter.py
"""
Module for plotting time-series data.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def plot_series(df, date_col, y_cols, days_lookback, title, plot_type, chart_key, group_by_day=True):
    """
    Plots a time-series graph.

    @param df: DataFrame with data.
    @param date_col: Name of the date column.
    @param y_cols: List of Y-axis columns.
    @param days_lookback: Number of days to show.
    @param title: Plot title.
    @param plot_type: 'Линейный', 'Гистограмма', 'Точечный (scatter)'.
    @param chart_key: Unique key for Streamlit.
    @param group_by_day: If True — aggregate by day (default). If False — show raw data (for multi-year plots).
    """
    if date_col not in df.columns:
        st.warning(f"Колонка даты '{date_col}' не найдена")
        return

    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col]).copy()
    if df.empty:
        st.info("Нет корректных дат")
        return

    max_date = df[date_col].max()
    min_date = max_date - pd.Timedelta(days=days_lookback)
    df = df[(df[date_col] >= min_date) & (df[date_col] <= max_date)].copy()
    if df.empty:
        st.info(f"Нет данных за последние {days_lookback} дней (до {max_date.date()})")
        return

    if group_by_day:
        df["День"] = df[date_col].dt.date
        agg_dict = {}
        for col in y_cols:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                agg_dict[col] = "mean"
        if not agg_dict:
            st.warning("Нет числовых колонок для отображения")
            return
        df_agg = df.groupby("День").agg(agg_dict).reset_index()
        df_agg["День"] = pd.to_datetime(df_agg["День"])
        x_col = "День"
    else:
        df_agg = df.copy()
        x_col = date_col

    if plot_type == "Линейный":
        fig = go.Figure()
        for col in y_cols:
            if col in df_agg.columns:
                fig.add_trace(go.Scatter(x=df_agg[x_col], y=df_agg[col], mode='lines+markers', name=col))
        fig.update_layout(title=title, xaxis_title="Дата", yaxis_title="Значение")
    elif plot_type == "Гистограмма":
        fig = px.bar(df_agg, x=x_col, y=y_cols, title=title)
        fig.update_layout(xaxis_title="Дата", yaxis_title="Значение")
    elif plot_type == "Точечный (scatter)":
        fig = go.Figure()
        for col in y_cols:
            if col in df_agg.columns:
                fig.add_trace(go.Scatter(x=df_agg[x_col], y=df_agg[col], mode='markers', name=col))
        fig.update_layout(title=title, xaxis_title="Дата", yaxis_title="Значение")
    else:
        st.warning("Неизвестный тип графика")
        return

    st.plotly_chart(fig, use_container_width=True, key=chart_key)
