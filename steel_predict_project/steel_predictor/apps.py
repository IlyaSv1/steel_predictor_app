from django.apps import AppConfig


class SteelPredictorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "steel_predictor"

    _models_loaded = False
