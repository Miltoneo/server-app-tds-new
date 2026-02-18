#!/usr/bin/env python
"""
Diagnóstico: Re-executar on_message manual com payload de teste
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

import json
from datetime import datetime, timezone
from tds_new.consumers.mqtt_telemetry import on_message
from tds_new.models import Gateway

class MockMsg:
    """Mock da mensagem MQTT"""
    def __init__(self, topic, payload):
        self.topic = topic
        self.payload = payload.encode('utf-8')

class MockClient:
    """Mock do cliente MQTT"""
    pass

# Criar payload de teste
payload = {
    "gateway_mac": "aa:bb:cc:dd:ee:ff",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "leituras": [
        {"dispositivo_codigo": "D01", "valor": 123.45, "unidade": "kWh"},
        {"dispositivo_codigo": "D02", "valor": 67.89, "unidade": "m³"},
        {"dispositivo_codigo": "D03", "valor": 22.5, "unidade": "°C"}
    ]
}

# Criar mensagem mockada
msg = MockMsg(
    topic="tds_new/devices/aa:bb:cc:dd:ee:ff/telemetry",
    payload=json.dumps(payload)
)

print("="*80)
print("TESTE DIRETO DO CALLBACK ON_MESSAGE")
print("="*80)
print()
print(f"[INFO] Topic: {msg.topic}")
print(f"[INFO] Payload: {json.dumps(payload, indent=2)}")
print()
print("[EXEC] Executando on_message()...")
print("-"*80)

# Executar callback diretamente
try:
    client = MockClient()
    on_message(client, None, msg)
    print("-"*80)
    print("[OK] Callback executado sem exceções")
except Exception as e:
    print("-"*80)
    print(f"[ERROR] Exceção capturada: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("[RESULT] Verificando leituras salvas...")
print("="*80)

from tds_new.models import LeituraDispositivo
leituras = LeituraDispositivo.objects.all().order_by('-time')[:5]
total = LeituraDispositivo.objects.count()

print(f"Total de leituras: {total}")
if total > 0:
    print()
    print("Últimas 5 leituras:")
    for l in leituras:
        print(f"  - {l.time} | Device {l.dispositivo.codigo} | {l.valor} {l.unidade}")
else:
    print("[WARN] Nenhuma leitura foi salva!")
