import os
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd
import joblib


# Путь
def resource_path(relative_path: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).resolve().parent
    return base_path / relative_path


# Глобальное хранилище моделей
MODELS: Dict[str, dict] = {
    "carbon": {},
    "stainless": {},
}


# Допустимые диапазоны
COMPOSITION_LIMITS = {
    "carbon": {
        "C": (0.02, 1.20),
        "Mn": (0.0, 2.00),
        "Si": (0.0, 0.80),
        "P": (0.0, 0.045),
        "S": (0.0, 0.050),
        "Ni": (0.0, 0.30),
        "Cr": (0.0, 0.30),
        "Mo": (0.0, 0.10),
        "Ti": (0.0, 0.10),
    },
    "stainless": {
        "C": (0.0, 0.15),
        "Mn": (0.0, 2.00),
        "Si": (0.0, 1.00),
        "P": (0.0, 0.045),
        "S": (0.0, 0.030),
        "Ni": (8.0, 20.0),
        "Cr": (10.5, 26.0),
        "Mo": (0.0, 6.0),
        "Ti": (0.0, 1.0),
    },
}


# Валидация
def validate_composition(steel_type: str, raw_data: dict) -> List[str]:
    errors = []
    limits = COMPOSITION_LIMITS.get(steel_type)

    if not limits:
        return ["Неизвестный тип стали"]

    for element, (min_val, max_val) in limits.items():
        value = raw_data.get(element)

        if value in (None, "", "null"):
            continue

        try:
            value = float(value)
        except ValueError:
            errors.append(f"{element}: некорректное числовое значение")
            continue

        if not (min_val <= value <= max_val):
            errors.append(
                f"{element}: {value}% (допустимо {min_val}–{max_val}%)"
            )

    return errors


# Загрузка моделей
def load_models() -> None:
    for steel_type in MODELS.keys():

        model_dir = resource_path(
            f"models/{steel_type}"
        )

        if not model_dir.exists():
            raise FileNotFoundError(
                f"Папка моделей не найдена: {model_dir}"
            )

        try:
            MODELS[steel_type]["models"] = {
                "uts": joblib.load(model_dir / "uts_model.pkl"),
                "ys": joblib.load(model_dir / "ys_model.pkl"),
                "elong": joblib.load(model_dir / "elong_model.pkl"),
                "hardness": joblib.load(model_dir / "hardness_model.pkl"),
            }

            MODELS[steel_type]["scaler"] = joblib.load(
                model_dir / "scaler.pkl"
            )

            features_path = model_dir / "features.pkl"

            if features_path.exists():
                MODELS[steel_type]["features"] = joblib.load(features_path)
            else:
                MODELS[steel_type]["features"] = [
                    "C", "Mn", "Si",
                    "P", "S", "Ni", "Cr", "Mo", "Ti"
                ]
                print(
                    f"⚠ features.pkl не найден для {steel_type}, используется default"
                )

        except Exception as e:
            raise RuntimeError(
                f"Ошибка загрузки моделей для {steel_type}: {e}"
            )

    print("ML models loaded successfully")


# Подготовка входных данных
def prepare_input_data(raw_data: dict, features: list) -> pd.DataFrame:
    values = []

    for feature in features:
        value = raw_data.get(feature)

        if value in (None, "", "null"):
            values.append(0.0)
        else:
            try:
                values.append(float(value))
            except ValueError:
                raise ValueError(
                    f"Некорректное значение для {feature}: {value}"
                )

    return pd.DataFrame([values], columns=features)


# Предсказание
def predict_properties(
    steel_type: str,
    raw_data: dict
) -> Dict[str, float]:

    if steel_type not in MODELS:
        raise ValueError(f"Неизвестный тип стали: {steel_type}")

    # ЛЕНИВАЯ ЗАГРУЗКА
    if not MODELS[steel_type]:
        load_models()

    model_block = MODELS[steel_type]

    features = model_block["features"]
    scaler = model_block["scaler"]
    models = model_block["models"]

    X = prepare_input_data(raw_data, features)
    X_scaled = scaler.transform(X)

    return {
        "uts": round(float(models["uts"].predict(X_scaled)[0]), 2),
        "ys": round(float(models["ys"].predict(X_scaled)[0]), 2),
        "elong": round(float(models["elong"].predict(X_scaled)[0]), 2),
        "hardness": round(float(models["hardness"].predict(X_scaled)[0]), 2),
    }
