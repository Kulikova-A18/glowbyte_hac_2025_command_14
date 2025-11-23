# modules/global_weather.py

"""
Module for rendering the global weather visualization panel.
Displays aggregated meteorological data across multiple years with daily averaging.
All UI text is in Russian.
"""

import streamlit as st
import os
import glob
import pandas as pd
import plotly.express as px
from datetime import timedelta
from modules.data_loader import load_csv
from constants import WEATHER_DIR


def render_global_weather():
    """
    Renders the global weather section with year selection, parameter choice,
    and a Plotly line chart showing averaged values across selected years.

    @note: All displayed text is in Russian.
    @return: None
    """
    st.markdown("## Метеоданные")

    if not os.path.exists(WEATHER_DIR):
        st.error("Папка с метеоданными не найдена")
        return

    # Scan for weather files
    weather_files = glob.glob(os.path.join(WEATHER_DIR, "weather_data_*.csv"))
    if not weather_files:
        st.info("Нет файлов метеоданных")
        return

    # Extract years from filenames
    years = []
    for f in weather_files:
        basename = os.path.basename(f)
        try:
            year = int(basename.replace("weather_data_", "").replace(".csv", ""))
            years.append(year)
        except ValueError:
            continue

    if not years:
        st.info("Не найдено файлов в формате weather_data_YYYY.csv")
        return

    years = sorted(set(years), reverse=False)

    # UI Controls
    with st.container():
        mode = st.radio(
            "Режим отображения",
            ["Выбрать годы", "Все годы"],
            horizontal=True,
            key="weather_mode"
        )

        selected_years = years if mode == "Все годы" else st.multiselect(
            "Годы",
            years,
            default=years[-1:],
            key="global_weather_years"
        )

        col1, col2 = st.columns([2, 1])
        with col1:
            st.caption(f"Выбрано: {len(selected_years)} лет")
        with col2:
            days = st.slider("Дней для отображения", 1, 365, 90, key="global_weather_days")

        if not selected_years:
            st.info("Выберите хотя бы один год")
            return

        # Load and preprocess data
        all_dfs = []
        for year in selected_years:
            file_path = os.path.join(WEATHER_DIR, f"weather_data_{year}.csv")
            df = load_csv(file_path)
            if not df.empty and "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df = df.dropna(subset=["date"])
                df["Год"] = str(year)
                df["ДеньМесяц"] = df["date"].dt.strftime("%m-%d")
                all_dfs.append(df)
            else:
                st.warning(f"Данные за {year} г. недоступны")

        if not all_dfs:
            st.info("Нет данных для отображения")
            return

        combined_df = pd.concat(all_dfs, ignore_index=True)
        exclude = ["date", "Год", "ДеньМесяц"]
        available_params = [col for col in combined_df.columns if col not in exclude]
        default_params = ["t", "precipitation", "humidity", "v_max"]
        safe_defaults = [p for p in default_params if p in available_params] or (available_params[:1] if available_params else [])

        y_cols = st.multiselect(
            "Параметры для отображения",
            available_params,
            default=safe_defaults,
            key="global_weather_params"
        )

    # Build and display chart
    if y_cols:
        plot_data = []
        for col in y_cols:
            for year in selected_years:
                year_str = str(year)
                mask = combined_df["Год"] == year_str
                if mask.sum() == 0:
                    continue
                yearly_avg = combined_df[mask].groupby("ДеньМесяц")[col].mean().reset_index()
                yearly_avg["Год"] = year_str
                yearly_avg.rename(columns={col: "Значение"}, inplace=True)
                yearly_avg["Параметр"] = col
                plot_data.append(yearly_avg)

        if not plot_data:
            st.info("Нет данных для отображения")
            return

        final_df = pd.concat(plot_data, ignore_index=True)
        final_df["Дата"] = pd.to_datetime("2020-" + final_df["ДеньМесяц"], errors="coerce")
        final_df = final_df.dropna(subset=["Дата"]).sort_values("Дата")

        # Apply day limit: keep only last N days
        max_date = final_df["Дата"].max()
        min_date = max_date - timedelta(days=days)
        final_df = final_df[(final_df["Дата"] >= min_date) & (final_df["Дата"] <= max_date)]

        if final_df.empty:
            st.info(f"Нет данных за последние {days} дней")
            return

        final_df["Линия"] = final_df["Параметр"] + " (" + final_df["Год"] + ")"

        fig = px.line(
            final_df,
            x="Дата",
            y="Значение",
            color="Линия",
            title=f"Метеоданные ({len(selected_years)} лет) — среднее по дням",
            labels={"Дата": "Дата", "Значение": "Среднее значение"}
        )
        fig.update_layout(
            xaxis_title="Дата",
            yaxis_title="Значение",
            legend_title="Параметр / Год",
            height=500,
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True, key=f"global_weather_{'_'.join(map(str, selected_years))}")
    else:
        st.info("Выберите хотя бы один параметр")
