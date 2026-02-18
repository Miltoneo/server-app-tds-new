#!/usr/bin/env python
"""
Teste rápido MQTT - Com autenticação
"""
import paho.mqtt.publish as publish
import json
from datetime import datetime, timezone

# Config
BROKER = "localhost"
PORT = 1883  
AUTH = {'username': 'admin', 'password': 'admin'}
TOPIC = "tds_new/devices/aa:bb:cc:dd:ee:ff/telemetry"

# Payload
payload = {
    "gateway_mac": "aa:bb:cc:dd:ee:ff",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "leituras": [
        {"dispositivo_codigo": "D01", "valor": 123.45, "unidade": "kWh"},
        {"dispositivo_codigo": "D02", "valor": 67.89, "unidade": "m³"},
        {"dispositivo_codigo": "D03", "valor": 22.5, "unidade": "°C"}
    ]
}

print(f"[MQTT] Enviando para {TOPIC}...")
publish.single(
    TOPIC,
    payload=json.dumps(payload),
    hostname=BROKER,
    port=PORT,
    auth=AUTH,
    qos=1
)
print("[OK] Mensagem enviada com autenticacao!")
print(f"[INFO] Payload: {json.dumps(payload, indent=2)}")
