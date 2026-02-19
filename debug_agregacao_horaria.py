import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.db.models.functions import TruncHour
from django.db.models import Avg, Count
from tds_new.models import LeituraDispositivo
from datetime import datetime, timedelta
import pytz

# Configurar timezone
tz_brasilia = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(tz_brasilia)
inicio = agora - timedelta(hours=24)

print(f"=== DEBUG AGREGAÇÃO HORÁRIA ===\n")
print(f"Período: {inicio.strftime('%d/%m/%Y %H:%M')} até {agora.strftime('%d/%m/%Y %H:%M')}\n")

# Verificar total de leituras
total = LeituraDispositivo.objects.filter(
    conta_id=2,
    time__gte=inicio,
    time__lte=agora
).count()
print(f"Total de leituras no período: {total}\n")

# Listar todas as leituras com timestamp
print("=== LEITURAS INDIVIDUAIS ===")
leituras = LeituraDispositivo.objects.filter(
    conta_id=2,
    time__gte=inicio,
    time__lte=agora
).order_by('time').values('time', 'dispositivo__codigo', 'unidade', 'valor')

for leitura in leituras:
    ts = leitura['time'].astimezone(tz_brasilia)
    print(f"{ts.strftime('%d/%m %H:%M:%S')} | {leitura['dispositivo__codigo']} | {leitura['unidade']}: {leitura['valor']}")

# Verificar agregação por hora
print("\n=== AGREGAÇÃO POR HORA (TruncHour) ===")
agregacao = LeituraDispositivo.objects.filter(
    conta_id=2,
    time__gte=inicio,
    time__lte=agora
).annotate(
    hora=TruncHour('time')
).values(
    'hora', 'dispositivo__codigo', 'unidade'
).annotate(
    valor_medio=Avg('valor'),
    quantidade=Count('id')
).order_by('hora', 'dispositivo__codigo', 'unidade')

horas_distintas = set()
for item in agregacao:
    hora_local = item['hora'].astimezone(tz_brasilia)
    horas_distintas.add(hora_local.strftime('%d/%m %H:00'))
    print(f"{hora_local.strftime('%d/%m %H:00')} | {item['dispositivo__codigo']} | {item['unidade']}: {item['valor_medio']:.2f} (qty: {item['quantidade']})")

print(f"\n=== RESUMO ===")
print(f"Total de horas distintas: {len(horas_distintas)}")
print(f"Horas: {sorted(horas_distintas)}")
print(f"\nPara ter grid vertical a cada hora, precisamos de múltiplas horas com dados.")
print(f"Atualmente temos apenas {len(horas_distintas)} hora(s) com dados.")
