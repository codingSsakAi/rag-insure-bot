# insurance_app/apps.py
from django.apps import AppConfig

class InsuranceAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "insurance_app"

    def ready(self):
        try:
            from .services.embedding_provider import warmup_embedding_model
            import threading
            threading.Thread(target=warmup_embedding_model, daemon=True).start()
        except Exception:
            pass
