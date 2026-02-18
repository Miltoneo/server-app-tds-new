#!/usr/bin/env python
"""
Script para verificar leituras salvas no TimescaleDB
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from tds_new.models import LeituraDispositivo, Gateway, Dispositivo
from django.utils import timezone

print("=" * 80)
print("VERIFICAÇÃO DE LEITURAS - FASE 2")
print("=" * 80)
print()

# 1. Verificar Gateway
print("[1/4] Verificando Gateway...")
try:
    gateway = Gateway.objects.get(mac='aa:bb:cc:dd:ee:ff')
    print(f"  [OK] Gateway encontrado: {gateway.nome}")
    print(f"  - ID: {gateway.id}")
    print(f"  - MAC: {gateway.mac}")
    print(f"  - Online: {gateway.is_online}")
    print(f"  - Last seen: {gateway.last_seen}")
except Gateway.DoesNotExist:
    print("  [ERRO] Gateway não encontrado!")
    exit(1)
print()

# 2. Verificar Dispositivos
print("[2/4] Verificando Dispositivos...")
dispositivos = Dispositivo.objects.filter(gateway=gateway)
print(f"  Total de dispositivos: {dispositivos.count()}")
for disp in dispositivos:
    print(f"  - {disp.codigo}: {disp.nome} (ID: {disp.id})")
print()

# 3. Verificar Leituras
print("[3/4] Verificando Leituras...")
leituras = LeituraDispositivo.objects.all().order_by('-time')[:10]
total_leituras = LeituraDispositivo.objects.count()

print(f"  Total de leituras no banco: {total_leituras}")
print()

if total_leituras > 0:
    print("  Últimas 10 leituras:")
    print("  " + "-" * 76)
    print(f"  {'Timestamp':<25} {'Device':<8} {'Valor':<12} {'Unidade':<8}")
    print("  " + "-" * 76)
    for leitura in leituras:
        print(f"  {str(leitura.time):<25} {leitura.dispositivo.codigo:<8} {leitura.valor:<12} {leitura.unidade:<8}")
    print("  " + "-" * 76)
else:
    print("  [AVISO] Nenhuma leitura encontrada no banco de dados!")
    print("  Possíveis causas:")
    print("    - Consumer MQTT não está rodando")
    print("    - Simulador não enviou mensagens")
    print("    - Erro no processamento da telemetria")
print()

# 4. Últimas leituras por dispositivo
if total_leituras > 0:
    print("[4/4] Última leitura por dispositivo:")
    print("  " + "-" * 76)
    for disp in dispositivos:
        ultima = LeituraDispositivo.objects.filter(dispositivo=disp).order_by('-time').first()
        if ultima:
            print(f"  {disp.codigo}: {ultima.valor} {ultima.unidade} (em {ultima.time})")
        else:
            print(f"  {disp.codigo}: [SEM LEITURAS]")
    print("  " + "-" * 76)
else:
    print("[4/4] Sem leituras para exibir")

print()
print("=" * 80)
print("[OK] Verificação concluída")
print("=" * 80)
