from django.apps import AppConfig


class BaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'base'
    verbose_name = 'Restoran Yönetim Sistemi'

    def ready(self):
        import base.signals
