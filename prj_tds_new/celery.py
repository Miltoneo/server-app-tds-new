"""
Configuração Celery — TDS New

Lê configurações do bloco CELERY_* em settings.py.
Tarefas periódicas registradas em tds_new/tasks.py.

Uso em desenvolvimento:
  # Worker
  celery -A prj_tds_new worker -l info

  # Scheduler (beat) — requer celery[redis]
  celery -A prj_tds_new beat -l info

  # Ou ambos juntos (apenas dev):
  celery -A prj_tds_new worker --beat -l info
"""

import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')

app = Celery('tds_new')

# Lê configurações prefixadas com CELERY_ de settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descobre tasks em todos os INSTALLED_APPS (procura tasks.py em cada app)
app.autodiscover_tasks()
