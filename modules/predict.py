# modules/predict.py
import joblib
import pandas as pd
import streamlit as st
from .logger import get_app_logger  # ← добавлен импорт логгера

# Инициализация логгера
logger = get_app_logger()

MODEL_PATH = "data/pkl/model.pkl"
LE_PATH = "data/pkl/label_encoder.pkl"


class CoalFirePredictor:
    def __init__(self, model_path: str = MODEL_PATH, encoder_path: str = LE_PATH):
        self.model = None
        self.encoder = None
        self.model_path = model_path
        self.encoder_path = encoder_path
        self.load_model()
        self.load_encoder()

    def load_model(self):
        try:
            self.model = joblib.load(self.model_path)
            msg = f"Модель загружена: {type(self.model)}"
            logger.info(msg)
            st.write(msg)
        except FileNotFoundError:
            error_msg = f"Файл модели не найден: {self.model_path}"
            logger.error(error_msg)
            st.error(f"Ошибка загрузки модели: файл не найден")
            self.model = None
        except Exception as e:
            error_msg = f"Ошибка загрузки модели из {self.model_path}: {e}"
            logger.error(error_msg, exc_info=True)
            st.error(f"Ошибка загрузки модели: {e}")
            self.model = None

    def load_encoder(self):
        try:
            self.encoder = joblib.load(self.encoder_path)
            msg = "LabelEncoder загружен."
            logger.info(msg)
            st.write(msg)
        except FileNotFoundError:
            warning_msg = f"Файл LabelEncoder не найден: {self.encoder_path}"
            logger.warning(warning_msg)
            st.warning("LabelEncoder НЕ загружен. Категория 'Марка' будет факторизована.")
            self.encoder = None
        except Exception as e:
            warning_msg = f"Ошибка загрузки LabelEncoder из {self.encoder_path}: {e}"
            logger.warning(warning_msg, exc_info=True)
            st.warning(f"LabelEncoder НЕ загружен ({e}). Категория 'Марка' будет факторизована.")
            self.encoder = None

    def _ensure_model(self):
        if self.model is None:
            error_msg = "Попытка использовать предсказание при отсутствии загруженной модели"
            logger.error(error_msg)
            raise ValueError("Модель не загружена")

    def prepare_features_from_df(self, df, feature_cols):
        df = df.copy()
        missing = [c for c in feature_cols if c not in df.columns]
        if missing:
            error_msg = f"В DataFrame не хватает колонок: {missing}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        if "Марка" in df.columns:
            if self.encoder is not None:
                try:
                    df["Марка"] = self.encoder.transform(df["Марка"])
                    logger.debug("Марка закодирована с помощью LabelEncoder")
                except Exception as e:
                    logger.warning(f"Ошибка при трансформации 'Марка' через LabelEncoder: {e}. Используется fallback.")
                    df["Марка"] = df["Марка"].apply(
                        lambda x: self.encoder.transform([x])[0]
                        if x in self.encoder.classes_
                        else -1
                    )
            else:
                df["Марка"], _ = pd.factorize(df["Марка"])
                logger.debug("Марка закодирована через pd.factorize (LabelEncoder недоступен)")

        X = df[feature_cols].copy()
        for col in X.columns:
            if X[col].isna().any():
                X[col] = X[col].fillna(X[col].mean())
                logger.debug(f"В колонке '{col}' заполнены пропущенные значения средним")
        return X

    def predict_from_features(self, X):
        self._ensure_model()
        logger.debug(f"Выполнен вызов predict() для {X.shape[0]} записей")
        return self.model.predict(X)

    def predict_proba_from_features(self, X):
        self._ensure_model()
        if not hasattr(self.model, "predict_proba"):
            error_msg = "Модель не поддерживает метод predict_proba"
            logger.error(error_msg)
            raise ValueError(error_msg)
        proba = self.model.predict_proba(X)[:, 1]
        logger.debug(f"Получены вероятности для {X.shape[0]} записей")
        return proba

    def add_predictions_to_df(self, df, feature_cols, threshold=0.1):
        logger.info(f"Запущено добавление предсказаний (порог={threshold}) для {len(df)} записей")
        X = self.prepare_features_from_df(df, feature_cols)
        proba = self.predict_proba_from_features(X)
        df = df.copy()
        df["fire_proba"] = proba
        df["fire_pred"] = (proba >= threshold).astype(int)
        logger.info(f"Предсказания добавлены: {df['fire_pred'].sum()} записей с высоким риском")
        return df


# Ленивая инициализация
_predictor_instance = None

def get_predictor():
    global _predictor_instance
    if _predictor_instance is None:
        logger.info("Инициализация ленивого экземпляра CoalFirePredictor")
        _predictor_instance = CoalFirePredictor()
    return _predictor_instance
