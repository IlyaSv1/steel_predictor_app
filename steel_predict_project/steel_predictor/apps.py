from django.apps import AppConfig
import logging
import os


logger = logging.getLogger(__name__)


class SteelPredictorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "steel_predictor"

    _models_loaded = False  # защита от повторной загрузки

    def ready(self):
        """
        Загружаем ML-модели один раз при старте Django
        """

        # Защита от двойного запуска
        if os.environ.get("RUN_MAIN") != "true":
            return

        if SteelPredictorConfig._models_loaded:
            return

        from .utils import load_models

        try:
            load_models()
            SteelPredictorConfig._models_loaded = True
            logger.info("ML models successfully loaded")
        except Exception as e:
            logger.exception(f"Failed to load ML models: {e}")
            raise
