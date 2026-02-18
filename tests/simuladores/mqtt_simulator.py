#!/usr/bin/env python
"""
Simulador MQTT - Envia telemetria de teste
====================================================================================
Uso: python tests/simuladores/mqtt_simulator.py
====================================================================================
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime, timezone

# Configurações
BROKER_HOST = "localhost"
BROKER_PORT = 1883
BROKER_USER = "admin"  # Usar admin para testes
BROKER_PASSWORD = "admin"
MAC_ADDRESS = "aa:bb:cc:dd:ee:ff"  # Gateway fictício para teste
TOPIC = f"tds_new/devices/{MAC_ADDRESS}/telemetry"

# Payload de teste
payload = {
    "gateway_mac": MAC_ADDRESS,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "leituras": [
        {
            "dispositivo_codigo": "D01",
            "valor": 123.45,
            "unidade": "kWh"
        },
        {
            "dispositivo_codigo": "D02",
            "valor": 67.89,
            "unidade": "m³"
        },
        {
            "dispositivo_codigo": "D03",
            "valor": 22.5,
            "unidade": "°C"
        }
    ]
}

def on_publish(client, userdata, mid):
    """Callback quando mensagem é publicada"""
    print(f"✅ Mensagem publicada (mid={mid})")

def main():
    """Envia mensagem de telemetria de teste"""
    print("🚀 Simulador MQTT - Telemetria de Teste")
    print("=" * 50)
    print(f"Broker: {BROKER_HOST}:{BROKER_PORT}")
    print(f"Topic: {TOPIC}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("=" * 50)
    
    # Criar cliente
    client = mqtt.Client(client_id="test_simulator")
    client.on_publish = on_publish
    
    # Configurar autenticação
    client.username_pw_set(BROKER_USER, BROKER_PASSWORD)
    
    try:
        # Conectar
        print(f"\n🔗 Conectando ao broker...")
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        print("✅ Conectado!")
        
        # Publicar mensagem
        print(f"\n📤 Publicando mensagem...")
        result = client.publish(TOPIC, json.dumps(payload), qos=1)
        
        # Aguardar confirmação
        result.wait_for_publish()
        
        print(f"✅ Mensagem enviada com sucesso!")
        print(f"\n💡 Verifique o consumer Django para confirmar recebimento")
        
        # Dar tempo para callbacks
        time.sleep(1)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    finally:
        client.disconnect()
        print("\n👋 Desconectado")

if __name__ == "__main__":
    main()
