from django.apps import AppConfig


class TdsNewConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tds_new'

    def ready(self):
        # Signals serão importados aqui quando implementados
        # import tds_new.signals
        pass
