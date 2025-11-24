# modules/model_trainer.py
"""
Trains and saves a machine learning model for predicting coal stockpile fire risk.
Automatically aggregates all weather data files matching the pattern:
`data/weather_data/weather_data_*.csv`.

The pipeline performs the following steps:
1. Loads historical data on coal supplies, temperature, and fire incidents.
2. Constructs a daily calendar of coal stockpile states.
3. Engineers features including stack age, mass, temperature trends, and weather.
4. Defines a binary target: fire occurrence within the next 3 days.
5. Trains a class-weighted Random Forest classifier.
6. Saves the model and label encoder to `data/pkl/`.

All file paths are resolved relative to the project root (where `app.py` resides).
"""

import os
import glob
import pandas as pd
import joblib
from .logger import get_app_logger
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Initialize logger
logger = get_app_logger()


def train_and_save_model():
    """
    Trains a Random Forest classifier to predict the risk of coal stockpile self-ignition
    and saves the trained model along with the LabelEncoder for the 'Марка' feature.

    This function:
    - Loads and validates input datasets (fires, supplies, temperature, weather).
    - Builds a unified time-series dataset at daily granularity per stockpile.
    - Labels each day as high-risk if a fire occurred within the next 3 days.
    - Engineers key features (age, mass, temperature change, weather, etc.).
    - Encodes categorical features and handles missing values.
    - Splits data into train/test sets with stratification.
    - Trains a Random Forest with class weighting to address imbalance.
    - Persists model artifacts to disk.

    @raises FileNotFoundError
        If any of the required input CSV files are missing.
    @raises ValueError
        If no valid stockpiles or temporal boundaries can be derived from the data.
    @raises Exception
        If an unexpected error occurs during data processing or training.

    @return None
        Artifacts are saved to the file system; no value is returned.
    """
    logger.info("Starting coal fire risk model training pipeline")

    # Resolve project root and data directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data")

    # Define file paths
    fires_path = os.path.join(data_dir, "fires", "fires.csv")
    supplies_path = os.path.join(data_dir, "supplies", "supplies.csv")
    temperature_path = os.path.join(data_dir, "temperature", "temperature.csv")
    weather_pattern = os.path.join(data_dir, "weather_data", "weather_data_*.csv")

    pkl_dir = os.path.join(data_dir, "pkl")
    model_path = os.path.join(pkl_dir, "model.pkl")
    encoder_path = os.path.join(pkl_dir, "label_encoder.pkl")

    # Validate existence of core datasets
    required_files = [
        (fires_path, "fires.csv"),
        (supplies_path, "supplies.csv"),
        (temperature_path, "temperature.csv")
    ]
    for path, name in required_files:
        if not os.path.exists(path):
            error_msg = f"Required input file not found: {name} (expected at: {path})"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

    # Load core datasets
    db_fires = pd.read_csv(fires_path)
    db_supplies = pd.read_csv(supplies_path)
    db_temp = pd.read_csv(temperature_path)
    logger.info(f"Loaded datasets — fires: {db_fires.shape}, supplies: {db_supplies.shape}, temperature: {db_temp.shape}")

    # Load all weather files
    weather_files = glob.glob(weather_pattern)
    if not weather_files:
        error_msg = f"No weather files found matching pattern: {weather_pattern}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    weather_dfs = []
    for file in weather_files:
        df = pd.read_csv(file)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        weather_dfs.append(df[["date", "t", "p", "humidity"]])
        logger.debug(f"Loaded weather file: {os.path.basename(file)} ({len(df)} records)")

    weather = pd.concat(weather_dfs, ignore_index=True)
    logger.info(f"Aggregated total weather records: {len(weather)}")

    # Determine temporal boundaries from all data sources
    try:
        fire_end = pd.to_datetime(db_fires["Дата оконч."], errors='coerce')
        temp_date = pd.to_datetime(db_temp["Дата акта"], errors='coerce')
        unload_date = pd.to_datetime(db_supplies["ВыгрузкаНаСклад"], errors='coerce')
        load_date = pd.to_datetime(db_supplies["ПогрузкаНаСудно"], errors='coerce')

        dates = [
            fire_end.min(), temp_date.min(), unload_date.min(), load_date.min(),
            fire_end.max(), temp_date.max(), unload_date.max(), load_date.max()
        ]
        valid_dates = [d for d in dates if pd.notna(d)]
        if not valid_dates:
            raise ValueError("Unable to infer valid time range from input data")
        min_date = min(valid_dates)
        max_date = max(valid_dates)
        logger.debug(f"Inferred data time range: {min_date.date()} to {max_date.date()}")
    except Exception as e:
        logger.error(f"Failed to determine temporal boundaries: {e}", exc_info=True)
        raise

    # Build daily calendar per stockpile
    stack_start = db_supplies.groupby("Штабель")["ВыгрузкаНаСклад"].min()
    stack_calendars = {}
    for stack in stack_start.index:
        start = pd.to_datetime(stack_start[stack], errors='coerce')
        if pd.isna(start):
            continue
        dates_range = pd.date_range(start, max_date, freq="D")
        stack_calendars[stack] = pd.DataFrame({"Дата": dates_range, "Штабель": stack})

    if not stack_calendars:
        error_msg = "No valid stockpiles found for processing"
        logger.error(error_msg)
        raise ValueError(error_msg)

    df_calendar = pd.concat(list(stack_calendars.values()), ignore_index=True)
    df_calendar["Дата"] = pd.to_datetime(df_calendar["Дата"]).dt.normalize()
    logger.info(f"Constructed stockpile calendar with {len(df_calendar)} daily records")

    # Label high-risk days (fire within next 3 days)
    df_calendar["y_3d"] = 0
    fires_events = db_fires[["Штабель", "Дата начала"]].dropna()
    fires_events["Дата начала"] = pd.to_datetime(fires_events["Дата начала"]).dt.normalize()

    fire_count = 0
    for _, row in fires_events.iterrows():
        sht = row["Штабель"]
        fire_date = row["Дата начала"]
        if pd.isna(sht) or pd.isna(fire_date):
            continue
        window_start = fire_date - pd.Timedelta(days=3)
        window_end = fire_date - pd.Timedelta(days=1)
        mask = (
            (df_calendar["Штабель"] == sht) &
            (df_calendar["Дата"] >= window_start) &
            (df_calendar["Дата"] <= window_end)
        )
        df_calendar.loc[mask, "y_3d"] = 1
        fire_count += mask.sum()

    logger.info(f"Labeled {fire_count} high-risk days based on {len(fires_events)} fire events")

    # Enrich with stockpile metadata
    stack_info = (
        db_supplies
        .groupby("Штабель")
        .agg({"ВыгрузкаНаСклад": "min", "Наим. ЕТСНГ": "first"})
        .reset_index()
        .rename(columns={"ВыгрузкаНаСклад": "Дата_формирования", "Наим. ЕТСНГ": "Марка"})
    )
    stack_info["Дата_формирования"] = pd.to_datetime(stack_info["Дата_формирования"])
    df_calendar = df_calendar.merge(stack_info, on="Штабель", how="left")
    df_calendar["Возраст_дн"] = (df_calendar["Дата"] - df_calendar["Дата_формирования"]).dt.days

    # Compute cumulative mass
    arrivals = db_supplies[["Штабель", "ВыгрузкаНаСклад", "На склад, тн"]].dropna()
    arrivals = arrivals.rename(columns={"ВыгрузкаНаСклад": "Дата", "На склад, тн": "delta_mass"})
    arrivals["delta_mass"] = pd.to_numeric(arrivals["delta_mass"], errors="coerce")
    arrivals["Дата"] = pd.to_datetime(arrivals["Дата"])

    departures = db_supplies[["Штабель", "ПогрузкаНаСудно", "На судно, тн"]].dropna()
    departures = departures.rename(columns={"ПогрузкаНаСудно": "Дата", "На судно, тн": "delta_mass"})
    departures["delta_mass"] = -pd.to_numeric(departures["delta_mass"], errors="coerce")
    departures["Дата"] = pd.to_datetime(departures["Дата"])

    mass_events = pd.concat([arrivals, departures], ignore_index=True).dropna(subset=["delta_mass"])
    mass_daily = mass_events.groupby(["Штабель", "Дата"])["delta_mass"].sum().reset_index()
    df_calendar["Дата"] = pd.to_datetime(df_calendar["Дата"])
    df_calendar = df_calendar.merge(mass_daily, on=["Штабель", "Дата"], how="left")
    df_calendar["delta_mass"] = df_calendar["delta_mass"].fillna(0)
    df_calendar["mass"] = df_calendar.groupby("Штабель")["delta_mass"].cumsum()

    # Add temperature features
    db_temp["Дата акта"] = pd.to_datetime(db_temp["Дата акта"])
    db_temp_grouped = db_temp.groupby(["Штабель", "Дата акта"])["Максимальная температура"].max().reset_index()
    db_temp_grouped.rename(columns={"Дата акта": "Дата"}, inplace=True)
    df_calendar = df_calendar.merge(db_temp_grouped, on=["Штабель", "Дата"], how="left")
    df_calendar["Максимальная температура"] = df_calendar.groupby("Штабель")["Максимальная температура"].ffill().fillna(0)
    df_calendar["Темп_изменение"] = df_calendar.groupby("Штабель")["Максимальная температура"].diff().fillna(0)

    # Merge weather data
    df_calendar = df_calendar.merge(weather, left_on="Дата", right_on="date", how="left")
    for col in ["t", "p", "humidity"]:
        df_calendar[col] = df_calendar[col].ffill().fillna(df_calendar[col].mean())
    df_calendar.drop(columns=["date"], inplace=True)

    # Add temporal features
    df_calendar["weekday"] = df_calendar["Дата"].dt.weekday
    df_calendar["month"] = df_calendar["Дата"].dt.month

    # Prepare feature matrix and target vector
    feature_cols = [
        "Марка", "Возраст_дн", "mass", "Максимальная температура",
        "Темп_изменение", "weekday", "month", "t", "p", "humidity"
    ]
    X = df_calendar[feature_cols].copy()
    y = df_calendar["y_3d"].copy()
    logger.info(f"Prepared feature matrix of shape {X.shape} with positive class rate {y.mean():.4f}")

    # Encode categorical feature 'Марка'
    le = LabelEncoder()
    X["Марка"] = le.fit_transform(X["Марка"].astype(str))

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train model
    clf = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight={0: 1, 1: 5},
        max_depth=10,
        min_samples_leaf=5,
        max_features="sqrt"
    )
    clf.fit(X_train, y_train)
    logger.info("Model training completed successfully")

    # Save artifacts
    os.makedirs(pkl_dir, exist_ok=True)
    joblib.dump(clf, model_path)
    joblib.dump(le, encoder_path)

    logger.info(f"Model saved to: {model_path}")
    logger.info(f"LabelEncoder saved to: {encoder_path}")
    logger.info(f"Training set size: {X_train.shape}")
    logger.info(f"Positive class (fire risk) rate in full dataset: {y.mean():.2%}")
