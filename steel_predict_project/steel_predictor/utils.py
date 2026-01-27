import pandas as pd
import joblib
from pathlib import Path
from typing import Dict

# Папка приложения steel_predictor
APP_DIR = Path(__file__).resolve().parent

MODELS = {
    "carbon": {},
    "stainless": {}
}

# Допустимые диапазоны химического состава (%)
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
    }
}


def validate_composition(
    steel_type: str,
    raw_data: dict
) -> list[str]:
    """
    Проверяет химический состав на соответствие допустимым диапазонам

    :return: список ошибок (пустой список = всё ок)
    """

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


def load_models():
    """
    Загружает модели, scaler и список признаков
    для каждого типа стали
    """
    for steel_type in ["carbon", "stainless"]:
        model_dir = APP_DIR / "models" / steel_type

        # Загружаем модели
        MODELS[steel_type]["models"] = {
            "uts": joblib.load(model_dir / "uts_model.pkl"),
            "ys": joblib.load(model_dir / "ys_model.pkl"),
            "elong": joblib.load(model_dir / "elong_model.pkl"),
            "hardness": joblib.load(model_dir / "hardness_model.pkl"),
        }

        # Загружаем scaler
        MODELS[steel_type]["scaler"] = joblib.load(model_dir / "scaler.pkl")

        # Загружаем features
        features_path = model_dir / "features.pkl"
        if features_path.exists():
            MODELS[steel_type]["features"] = joblib.load(features_path)
        else:
            # Если features.pkl нет — используем стандартный список элементов
            default_features = ["C", "Mn", "Si",
                                "P", "S", "Ni", "Cr", "Mo", "Ti"]
            MODELS[steel_type]["features"] = default_features
            print(
                f"⚠️ features.pkl не найден для {steel_type}, используется default: {default_features}")

    print("✅ ML models loaded successfully")


def prepare_input_data(raw_data: dict, features: list) -> pd.DataFrame:
    """
    Преобразует данные из формы Django
    в DataFrame с правильным порядком признаков
    """
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


def predict_properties(
    steel_type: str,
    raw_data: dict
) -> Dict[str, float]:
    """
    Делает предсказание механических свойств стали
    """

    if steel_type not in MODELS:
        raise ValueError(f"Неизвестный тип стали: {steel_type}")

    model_block = MODELS[steel_type]

    features = model_block["features"]
    scaler = model_block["scaler"]
    models = model_block["models"]

    # 1. Подготовка входных данных
    X = prepare_input_data(raw_data, features)

    # 2. Масштабирование (без warning)
    X_scaled = pd.DataFrame(
        scaler.transform(X),
        columns=features
    )

    # 3. Предсказания (СТАБИЛЬНЫЕ КЛЮЧИ)
    return {
        "uts": round(float(models["uts"].predict(X_scaled)[0]), 2),
        "ys": round(float(models["ys"].predict(X_scaled)[0]), 2),
        "elong": round(float(models["elong"].predict(X_scaled)[0]), 2),
        "hardness": round(float(models["hardness"].predict(X_scaled)[0]), 2),
    }
