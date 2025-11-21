# modules/plotter.py

"""
Module for plotting time-series data.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import logging

def plot_series(df, date_col, y_cols, days_lookback, title, plot_type, chart_key):
    """
    Plots a time-series graph based on aggregated data.

    @param df: DataFrame containing the data.
    @param date_col: Name of the date column.
    @param y_cols: List of columns to plot on the Y-axis.
    @param days_lookback: Number of days back to filter the data.
    @param title: Title of the plot.
    @param plot_type: Type of plot ('Линейный', 'Гистограмма', 'Точечный (scatter)').
    @param chart_key: Unique key for the Streamlit plot element.
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

    df["День"] = df[date_col].dt.date

    # Safe aggregation
    agg_dict = {}
    for col in y_cols:
        if col not in df.columns:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            agg_dict[col] = "mean"
        else:
            agg_dict[col] = "count"  # or "nunique"

    if not agg_dict:
        st.warning("Нет колонок для отображения")
        return

    df_agg = df.groupby("День").agg(agg_dict).reset_index()
    df_agg["День"] = pd.to_datetime(df_agg["День"])

    # Plotting
    if plot_type == "Линейный":
        fig = go.Figure()
        for col in y_cols:
            if col in df_agg.columns:
                fig.add_trace(go.Scatter(x=df_agg["День"], y=df_agg[col], mode='lines+markers', name=col))
        fig.update_layout(title=title, xaxis_title="Дата", yaxis_title="Значение")
    elif plot_type == "Гистограмма":
        fig = px.bar(df_agg, x="День", y=y_cols, title=title)
        fig.update_layout(xaxis_title="Дата", yaxis_title="Значение")
    elif plot_type == "Точечный (scatter)":
        fig = go.Figure()
        for col in y_cols:
            if col in df_agg.columns:
                fig.add_trace(go.Scatter(x=df_agg["День"], y=df_agg[col], mode='markers', name=col))
        fig.update_layout(title=title, xaxis_title="Дата", yaxis_title="Значение")
    else:
        st.warning("Неизвестный тип графика")
        return

    st.plotly_chart(fig, use_container_width=True, key=chart_key)

