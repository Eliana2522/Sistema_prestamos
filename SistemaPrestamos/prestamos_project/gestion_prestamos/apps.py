from django.apps import AppConfig

class PrestamosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion_prestamos'

    def ready(self):
        import gestion_prestamos.signals