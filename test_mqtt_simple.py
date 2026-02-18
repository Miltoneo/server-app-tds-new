#!/usr/bin/env python
"""
Teste simples de subscribe MQTT (sem Django)
"""
import paho.mqtt.client as mqtt
import time
import json

# Callback quando conecta
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[OK] Conectado ao broker MQTT")
        print(f"[INFO] Flags: {flags}")
        client.subscribe("tds_new/devices/+/telemetry", qos=1)
        print("[OK] Subscribe confirmado")
    else:
        print(f"[ERROR] Falha na conexão (rc={rc})")

# Callback quando mensagem chega
def on_message(client, userdata, msg):
    print(f"\n[MSG] Mensagem recebida: {msg.topic}")
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        print(f"[DATA] Payload: {json.dumps(payload, indent=2)}")
    except:
        print(f"[DATA] Payload raw: {msg.payload}")

# Callback quando desconecta
def on_disconnect(client, userdata, rc):
    if rc == 0:
        print("\n[INFO] Desconectado (limpo)")
    else:
        print(f"\n[WARN] Desconectado inesperadamente (rc={rc})")

# Criar cliente
client = mqtt.Client(client_id="test_subscriber", protocol=mqtt.MQTTv311, clean_session=True)

# Configurar autenticação
client.username_pw_set("django_backend", "django123")

# Configurar callbacks
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# Conectar
print("[INFO] Conectando ao broker...")
client.connect("localhost", 1883, 60)

# Loop
print("[INFO] Aguardando mensagens (Ctrl+C para sair)...")
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[INFO] Encerrando...")
    client.disconnect()
