# Garante que o app Celery é carregado quando Django inicializa,
# permitindo que @shared_task use a configuração correta.
from .celery import app as celery_app

__all__ = ('celery_app',)
