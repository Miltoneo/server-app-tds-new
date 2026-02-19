"""
Debug: O que a view telemetria_dashboard está retornando
"""
import os
import sys
import django
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.utils import timezone
from tds_new.models import LeituraDispositivo, Dispositivo, Gateway

# Simular sessão com conta_id = 2
conta_id = 2
periodo = '24h'

print("=" * 80)
print("DEBUG: Telemetria Dashboard - Conta ID 2")
print("=" * 80)

# Calcular período
if periodo == '24h':
    inicio = timezone.now() - timedelta(hours=24)
elif periodo == '7d':
    inicio = timezone.now() - timedelta(days=7)
else:  # 30d
    inicio = timezone.now() - timedelta(days=30)

print(f"\n[INFO] Período: {periodo}")
print(f"       Início: {inicio}")
print(f"       Agora: {timezone.now()}")

# Query 1: Total de leituras
total_leituras = LeituraDispositivo.objects.filter(
    conta_id=conta_id,
    time__gte=inicio
).count()
print(f"\n[QUERY 1] Total de leituras (período {periodo}): {total_leituras}")

# Query 2: Dispositivos com leituras no período
dispositivos_ativos = LeituraDispositivo.objects.filter(
    conta_id=conta_id,
    time__gte=inicio
).values('dispositivo_id').distinct().count()
print(f"[QUERY 2] Dispositivos ativos (com leituras no período): {dispositivos_ativos}")

# Query 3: Última atualização
ultima_atualizacao = LeituraDispositivo.objects.filter(
    conta_id=conta_id
).order_by('-time').values_list('time', flat=True).first()
print(f"[QUERY 3] Última atualização: {ultima_atualizacao}")

# Query 4: Gateways online
gateways_online = Gateway.objects.filter(
    conta_id=conta_id,
    is_online=True
).count()
print(f"[QUERY 4] Gateways online: {gateways_online}")

# Query 5: Últimas leituras
ultimas_leituras = LeituraDispositivo.objects.filter(
    conta_id=conta_id,
    time__gte=inicio
).select_related('dispositivo').order_by('-time')[:10]

print(f"\n[QUERY 5] Últimas 10 leituras:")
for i, leitura in enumerate(ultimas_leituras, 1):
    print(f"  {i}. {leitura.time} - {leitura.dispositivo.codigo}: {leitura.valor} {leitura.unidade}")

# Query 6: Todos os dispositivos (para filtro)
todos_dispositivos = Dispositivo.objects.filter(
    conta_id=conta_id
)
print(f"\n[QUERY 6] Todos os dispositivos da conta:")
for disp in todos_dispositivos:
    print(f"  - {disp.codigo}: {disp.nome} ({disp.tipo})")
    leituras_disp = LeituraDispositivo.objects.filter(dispositivo=disp).count()
    print(f"    └─ Total de leituras: {leituras_disp}")

# Verificar se há leituras FORA do período
leituras_total = LeituraDispositivo.objects.filter(
    conta_id=conta_id
).count()
print(f"\n[INFO] Total de leituras (sem filtro de período): {leituras_total}")

if leituras_total > total_leituras:
    print(f"[AVISO] Existem {leituras_total - total_leituras} leituras FORA do período de {periodo}")
    leitura_mais_antiga = LeituraDispositivo.objects.filter(
        conta_id=conta_id
    ).order_by('time').first()
    print(f"        Leitura mais antiga: {leitura_mais_antiga.time}")

print("\n" + "=" * 80)
