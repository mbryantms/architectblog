from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "architectblog.blog"
    verbose_name = "Architect blog"

    def ready(self):
        # import signal handlers
        from . import signals
