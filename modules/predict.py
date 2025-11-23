import joblib
import pandas as pd
import streamlit as st

# путь к модели
MODEL_PATH = "model.pkl"
LE_PATH = "label_encoder.pkl"

# класс содержит функции: 
# - инициализации 
# - загрузки модели И загрузка энкодера для параметра Марка
# - защиты о том что модель точно загружена
# - подготовки фич 
# - вероятность пожара [0 ... 1], отсюда смотрим по порогу true или false
# - вероятность пожара (true/false 1/0)
# - добавление колонок в наш df итоговый
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
            print(f"Модель загружена: {type(self.model)}")
        except Exception as e:
            st.error(f"Ошибка загрузки модели: {e}")
            self.model = None
 
    def load_encoder(self):
        try:
            self.encoder = joblib.load(self.encoder_path)
            print("LabelEncoder загружен.")
        except Exception as e:
            print(f"LabelEncoder НЕ загружен ({e}). Категория 'Марка' будет факторизована.")
            self.encoder = None
 
    def _ensure_model(self):
        if self.model is None:
            raise ValueError("Модель не загружена")
        
    def prepare_features_from_df(self, df, feature_cols):
        df = df.copy()

        missing = [c for c in feature_cols if c not in df.columns]
        if missing:
            raise ValueError(f"В DataFrame не хватает колонок: {missing}")

        # обработка Марка
        if "Марка" in df.columns:
            if self.encoder is not None:
                # LabelEncoder
                try:
                    df["Марка"] = self.encoder.transform(df["Марка"])
                except Exception:
                    df["Марка"] = df["Марка"].apply(
                        lambda x: self.encoder.transform([x])[0]
                        if x in self.encoder.classes_
                        else -1
                    )
            else:
                # если encoder не найден
                df["Марка"], _ = pd.factorize(df["Марка"])

        X = df[feature_cols].copy()
        
        for col in X.columns:
            if X[col].isna().any():
                X[col] = X[col].fillna(X[col].mean())

        return X

    
    def predict_from_features(self, X):

        self._ensure_model()
        preds = self.model.predict(X)
        return preds

    def predict_proba_from_features(self, X):
        self._ensure_model()

        if not hasattr(self.model, "predict_proba"):
            raise ValueError("Модель не поддерживает predict_proba")

        probs = self.model.predict_proba(X)[:, 1]
        return probs

    def add_predictions_to_df(self, df, feature_cols, threshold=0.1):
        X = self.prepare_features_from_df(df, feature_cols)

        proba = self.predict_proba_from_features(X)

        df = df.copy()
        df["fire_proba"] = proba
        df["fire_pred"] = (proba >= threshold).astype(int)

        return df

# читаем csv 
def predict_from_csv(csv_path, feature_cols, threshold=0.15):
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise ValueError(f"Ошибка чтения CSV: {e}")

    result_df = predictor.add_predictions_to_df(df, feature_cols, threshold)

    return result_df

# глобальный экземпляр
predictor = CoalFirePredictor()