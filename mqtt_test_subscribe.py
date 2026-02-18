#!/usr/bin/env python
"""
Teste direto de subscribe MQTT - Sem Django
"""
import paho.mqtt.client as mqtt
import time

BROKER = "localhost"
PORT = 1883
USER = "admin"
PASSWORD = "admin"
TOPIC = "tds_new/devices/+/telemetry"

def on_connect(client, userdata, flags, rc):
    print(f"[CONNECT] Connected with result code {rc}")
    client.subscribe(TOPIC, qos=1)
    print(f"[SUBSCRIBE] Subscribed to: {TOPIC}")

def on_message(client, userdata, msg):
    print(f"[MESSAGE] Topic: {msg.topic}")
    print(f"[MESSAGE] Payload: {msg.payload.decode('utf-8')}")

def on_subscribe(client, userdata, mid, granted_qos):
    print(f"[SUBSCRIBE] OK - mid={mid}, QoS={granted_qos}")

client = mqtt.Client(client_id="test_subscriber")
client.username_pw_set(USER, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.on_subscribe = on_subscribe

print(f"[CONNECT] Connecting to {BROKER}:{PORT}...")
client.connect(BROKER, PORT, keepalive=60)

print("[LOOP] Starting loop (Ctrl+C to stop)...")
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[STOP] Interrupted by user")
    client.disconnect()
