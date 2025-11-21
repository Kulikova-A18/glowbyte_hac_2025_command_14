# Инструкция для разработчиков

## Общее описание

Это веб-приложение для прогнозирования самовозгорания угля при открытом хранении, разработанное в рамках хакатона glowbye. 

Приложение позволяет:

- Загружать данные из нескольких источников:  
  - `fires.csv` — факты самовозгораний  
  - `supplies.csv` — выгрузки и отгрузки  
  - `temperature.csv` — температурные показатели штабелей  
  - `weather_data_*.csv` — метеоданные  

- Визуализировать эти данные в виде графиков по категориям.  
- Настраивать графики: выбирать параметры, тип визуализации, временной диапазон и название.  
- Сохранять и восстанавливать настройки между запусками через файл `schedule.json`.  
- Оценивать точность прогноза (в будущем — при интеграции ML-модели).

---

## Архитектура приложения

Приложение построено по модульной архитектуре, что обеспечивает:

- Чистоту кода  
- Легкость расширения  
- Наличие модульной архитектуры

### Структура проекта

```
glowbyte/
├── app.py                     # Главный файл — точка входа
├── constants.py               # Все константы (пути к файлам)
├── schedule.json              # Сохранение настроек графиков (автоматически)
├── app.log                    # Логи работы приложения (автоматически)
├── requirements.txt           # Зависимости
├── doc/                       # Папка для разработчиков с документациями и с отчетами
├── modules/
│   ├── __init__.py
│   ├── data_loader.py         # Загрузка CSV-файлов с парсингом дат
│   ├── plotter.py             # Построение графиков (plotly)
│   ├── schedule_manager.py    # Сохранение/загрузка настроек в JSON
│   └── ui_components.py       # Вся логика интерфейса (кнопки, формы, отображение)
└── utils/
    ├── __init__.py
    └── logger.py              # Настройка логгирования (совместимо с Python < 3.9)
```

---

## Как работает код

### 1. Загрузка данных (`data_loader.py`)
Функция `load_csv(file_path)` автоматически распознаёт столбцы с датой по ключевым словам `"дата"` или `"date"`.  
Использует `pd.to_datetime(..., errors='coerce')` — некорректные даты превращаются в `NaT`, не ломая приложение.  
Не требует жёсткого формата даты — поддерживает `2020-08-05`, `2020-08-05 09:00:00` и т.д.

### 2. Построение графиков (`plotter.py`)
Функция `plot_series()`:
- Группирует данные по дням (`df.groupby("День")`).
- Безопасно агрегирует:
  - Числовые столбцы → `mean()` (среднее значение)
  - Строковые столбцы → `count()` (количество записей)
- Позволяет выбирать тип графика:
  - Линейный  
  - Гистограмма  
  - Точечный (scatter)
- Каждый график имеет уникальный `key` — предотвращает ошибку `StreamlitDuplicateElementId`.

### 3. Сохранение настроек (`schedule_manager.py`)
Все созданные графики (параметры, тип, название, период) сохраняются в `schedule.json`.  
При запуске приложения — файл автоматически загружается, и все графики восстанавливаются.  
Это позволяет сохранять результаты анализа между сессиями.

### 4. Интерфейс (`ui_components.py`)
Все пользовательские элементы (кнопки, формы, графики) разделены по логике:
- `render_header()` — статистика и заголовок
- `render_buttons()` — 4 кнопки быстрого создания
- `show_standard_config()` — настройка для `fires`, `supplies`, `temperature`
- `show_weather_config()` — специальная настройка для погоды с выбором года
- `render_section()` — отображение графиков в сетке 2×N

Текст на интерфейсе — на русском, комментарии и документация — на английском (по требованиям хакатона).

### 5. Логирование (`utils/logger.py`)
Все ключевые действия (загрузка, сохранение, добавление графика) логируются в `app.log`.  
Поддерживает кодировку UTF-8 и совместимость с Python < 3.9.

---

## Как добавить новый компонент (например, новый тип данных)

### Шаг 1: Подготовьте данные
Поместите новый CSV-файл в соответствующую папку, например:
```
data/new_data/new_metrics.csv
```

### Шаг 2: Добавьте константу
В файле `constants.py` добавьте путь:

```python
NEW_DATA_FILE = os.path.join(DATA_DIR, "new_data", "new_metrics.csv")
```

### Шаг 3: Создайте настройку в `ui_components.py`
Создайте функцию `show_new_config()` — копируйте структуру `show_standard_config()`:

```python
def show_new_config():
    if st.session_state.show_config["new"]:
        with st.expander("Настройка: Новые метрики", expanded=True):
            # Загрузка файла
            df_preview = load_csv(NEW_DATA_FILE)
            if df_preview.empty:
                st.error("Файл не загружен")
                return

            # Выбор даты
            date_candidates = [col for col in df_preview.columns if "дата" in col.lower() or "date" in col.lower()]
            date_col = st.selectbox("Колонка с датой", date_candidates, key="date_new")

            # Выбор параметров
            value_cols = [col for col in df_preview.columns if col != date_col]
            y_cols = st.multiselect("Параметры (ось Y)", value_cols, default=value_cols[:1], key="ycols_new")

            # Автоимя
            params_str = "_".join(y_cols[:3]) if y_cols else "без_параметров"
            auto_name = f"{os.path.splitext(os.path.basename(NEW_DATA_FILE))[0]}_{params_str}"
            custom_name = st.text_input("Название графика", key="name_new")
            st.caption(f"Если оставить пустым, будет использовано: {auto_name}")
            display_name = custom_name.strip() if custom_name.strip() else auto_name

            days = st.slider("Данные за последние (дней)", 1, 365, 90, key="days_new")
            plot_type = st.selectbox("Тип графика", ["Линейный", "Гистограмма", "Точечный (scatter)"], key="type_new")

            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button("Создать график", key="create_new"):
                st.session_state.graphs["new"].append({
                    "id": st.session_state.next_id,
                    "file": NEW_DATA_FILE,
                    "date_col": date_col,
                    "y_cols": y_cols,
                    "days": days,
                    "plot_type": plot_type,
                    "title": display_name
                })
                st.session_state.next_id += 1
                st.session_state.show_config["new"] = False
                persist_changes()
                logging.info(f"Добавлен график в new: {display_name}")
                st.rerun()

            if col_btn2.button("Отмена", key="cancel_new"):
                st.session_state.show_config["new"] = False
                st.rerun()
```

### Шаг 4: Добавьте в состояние
В `app.py` в секции инициализации добавьте новую категорию:

```python
if "initialized" not in st.session_state:
    saved = load_schedule()
    st.session_state.graphs = {
        "supplies": saved["supplies"],
        "fires": saved["fires"],
        "temperature": saved["temperature"],
        "weather": saved["weather"],
        "new": saved.get("new", [])  # <-- НОВАЯ КАТЕГОРИЯ
    }
    st.session_state.next_id = saved.get("next_id", 0)
    st.session_state.show_config = {
        "supplies": False,
        "fires": False,
        "temperature": False,
        "weather": False,
        "new": False  # <-- НОВАЯ КАТЕГОРИЯ
    }
    st.session_state.initialized = True
```

### Шаг 5: Добавьте кнопку и отображение
В `app.py` в `render_buttons()` добавьте кнопку:

```python
if cols_btn[4].button("5. Новые метрики", key="btn_new"):
    st.session_state.show_config["new"] = True
```

В `render_section()` добавьте отображение:

```python
render_section("new", "Новые метрики")
```

### Шаг 6: Обновите `schedule_manager.py`
Добавьте новую категорию в `load_schedule()` и `save_schedule()`:

```python
# В load_schedule()
return {
    "supplies": [],
    "fires": [],
    "temperature": [],
    "weather": [],
    "new": [],  # <-- ДОБАВЛЕНО
    "next_id": 0
}

# В save_schedule()
data_to_save = {
    "supplies": st.session_state.graphs["supplies"],
    "fires": st.session_state.graphs["fires"],
    "temperature": st.session_state.graphs["temperature"],
    "weather": st.session_state.graphs["weather"],
    "new": st.session_state.graphs["new"],  # <-- ДОБАВЛЕНО
    "next_id": st.session_state.next_id
}
```

---

## Как запустить

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

2. Убедитесь, что структура папок такая:
   ```
   data/
   ├── fires/fires.csv
   ├── supplies/supplies.csv
   ├── temperature/temperature.csv
   └── weather_data/weather_data_2015.csv
   ```

3. Запустите приложение:
   ```bash
   streamlit run app.py
   ```

4. Откройте в браузере: `http://localhost:8501`

---

## Рекомендации для расширения

| Задача | Решение |
|-------|---------|
| Добавить ML-модель прогноза | Создайте `model/predict.py`, сгенерируйте `predictions.csv` с колонкой `predicted_date`, добавьте как новую категорию `predictions` |
| Добавить метрики точности | В `plotter.py` добавьте сравнение `fires.csv` и `predictions.csv` с выводом % попаданий в ±2 дня |
| Добавить календарь возгораний | Используйте `plotly` с `calendar heatmap` — можно добавить цветовую индикацию по риску |
| Добавить экспорт PDF/CSV | Используйте `streamlit.download_button()` для экспорта данных или графиков |
