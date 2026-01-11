from django.apps import AppConfig
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)


class SteelPredictorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'steel_predictor'

    def ready(self):
        """
        Загружаем ML-модели один раз при старте Django
        """
        # ❗ предотвращаем двойную загрузку
        if os.environ.get('RUN_MAIN') != 'true':
            return

        try:
            from .utils import load_models
            load_models()
            logger.info("ML models loaded")
        except Exception as e:
            logger.exception("❌ Failed to load ML models")
