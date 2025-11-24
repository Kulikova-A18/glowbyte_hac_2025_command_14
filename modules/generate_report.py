# modules/generate_report.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from pathlib import Path
from .logger import get_app_logger
from .predict import get_predictor

logger = get_app_logger()

def generate_comprehensive_report():
    st.subheader("Генерация аналитического отчёта")
    logger.info("Запущена генерация общего аналитического отчёта")
    st.info("Общий отчёт по погодным и операционным данным будет реализован позже.")


def generate_prediction_report(result_df: pd.DataFrame) -> str:
    total = len(result_df)
    high_risk = result_df["fire_pred"].sum()
    max_proba = result_df["fire_proba"].max()
    mean_proba = result_df["fire_proba"].mean()

    if "Штабель" in result_df.columns:
        high_risk_stacks = (
            result_df[result_df["fire_pred"] == 1]
            .groupby("Штабель")
            .size()
            .sort_values(ascending=False)
            .head(5)
        )
        top_stacks_str = ", ".join([f"Штабель {int(s)}" for s in high_risk_stacks.index])
    else:
        top_stacks_str = "информация о штабелях недоступна"

    monthly_risk = ""
    if "month" in result_df.columns:
        monthly_counts = (
            result_df[result_df["fire_pred"] == 1]
            .groupby("month")
            .size()
            .sort_values(ascending=False)
        )
        if not monthly_counts.empty:
            peak_month = monthly_counts.index[0]
            monthly_risk = f"\n- Наибольшее количество рисковых событий прогнозируется в месяце: {peak_month}."

    report = f"""Аналитический отчет по прогнозу риска самовозгорания угля

Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}

Общая статистика:
- Всего проанализировано записей: {total}
- Записей с высоким риском самовозгорания: {high_risk}
- Максимальная вероятность риска: {max_proba:.3f}
- Средняя вероятность риска: {mean_proba:.3f}

Ключевые выводы:
- Доля рисковых записей: {high_risk / total:.1%} от общего объема.
- Топ-5 штабелей с наибольшим числом рисковых событий: {top_stacks_str}.{monthly_risk}

Рекомендации:
- Рекомендуется провести дополнительный температурный мониторинг и/или профилактические мероприятия
  на указанных штабелях в указанные периоды.
- Для снижения ложных срабатываний возможно уточнение порога классификации или дообучение модели
  на новых данных.

Отчет сформирован автоматически на основе модели машинного обучения.
"""
    return report


def run_prediction_and_generate_report():
    st.subheader("Результаты прогноза риска самовозгорания")
    logger.info("Запущен процесс прогнозирования риска самовозгорания")

    schedule_path = os.path.join("data", "schedule_for_prediction.csv")
    output_dir = "output"
    feature_cols = [
        "Марка", "Возраст_дн", "mass", "Максимальная температура",
        "Темп_изменение", "weekday", "month", "t", "p", "humidity"
    ]
    threshold = 0.1

    if not os.path.exists(schedule_path):
        error_msg = f"Файл для прогноза не найден: {schedule_path}"
        logger.error(error_msg)
        st.error(error_msg)
        st.info("Убедитесь, что файл schedule_for_prediction.csv существует в папке data/ и содержит все необходимые колонки.")
        return

    try:
        df = pd.read_csv(schedule_path)
        logger.info(f"Загружен файл прогноза: {df.shape[0]} записей")

        predictor = get_predictor()
        result_df = predictor.add_predictions_to_df(df, feature_cols, threshold=threshold)
        logger.info("Прогноз успешно выполнен")

        os.makedirs(output_dir, exist_ok=True)
        results_path = os.path.join(output_dir, "prediction_results.csv")
        result_df.to_csv(results_path, index=False, encoding="utf-8")
        logger.info(f"Результаты сохранены: {results_path}")

        report_text = generate_prediction_report(result_df)
        report_path = os.path.join(output_dir, "prediction_report.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_text)
        logger.info(f"Аналитический отчёт сохранён: {report_path}")

        total = len(result_df)
        high_risk = int(result_df["fire_pred"].sum())
        max_proba = float(result_df["fire_proba"].max())
        mean_proba = float(result_df["fire_proba"].mean())

        st.success(f"Прогноз завершен: {high_risk} из {total} записей — высокий риск")
        logger.info(f"Прогноз: {high_risk}/{total} записей с высоким риском")

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Макс. вероятность", f"{max_proba:.3f}")
        col_b.metric("Ср. вероятность", f"{mean_proba:.3f}")
        col_c.metric("Порог классификации", f"{threshold:.2f}")

        csv_data = result_df.to_csv(index=False).encode("utf-8")
        st.download_button("Скачать результаты (CSV)", csv_data, "prediction_results.csv", "text/csv")
        st.download_button("Скачать аналитический отчет (TXT)", report_text.encode("utf-8"), "prediction_report.txt", "text/plain")

        st.write("Первые 10 записей:")
        st.dataframe(result_df.head(10))

    except Exception as e:
        error_msg = f"Ошибка при выполнении прогноза: {str(e)}"
        logger.error(error_msg, exc_info=True)
        st.error(error_msg)
        st.exception(e)
