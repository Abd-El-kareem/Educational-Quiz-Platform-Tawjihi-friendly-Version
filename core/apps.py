from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        from django.conf import settings

        from config.logging import configure_logging

        _listener = configure_logging(
            level=getattr(settings, "LOG_LEVEL", "INFO"),
            log_file=getattr(settings, "LOG_FILE", ""),
        )
        self._logging_listener = _listener
