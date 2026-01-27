from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class SteelPredictorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'steel_predictor'

    def ready(self):
        """
        Загружаем ML-модели один раз при старте Django
        """
        from .utils import load_models
        try:
            load_models()
            logger.info("✅ ML models loaded")
        except Exception:
            logger.exception("❌ Failed to load ML models")
