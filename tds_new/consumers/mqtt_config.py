# ==============================================================================
# TDS New - MQTT Configuration
# ==============================================================================
# Arquivo: tds_new/consumers/mqtt_config.py
# Responsabilidade: Configurações centralizadas para conexão MQTT
# ==============================================================================

import os
from django.conf import settings

# ==============================================================================
# CONFIGURAÇÕES DE CONEXÃO MQTT
# ==============================================================================

class MQTTConfig:
    """Configurações centralizadas para cliente MQTT"""
    
    # Broker MQTT
    BROKER_HOST = getattr(settings, 'MQTT_BROKER_HOST', 'localhost')
    BROKER_PORT = getattr(settings, 'MQTT_BROKER_PORT', 1883)
    BROKER_PORT_TLS = getattr(settings, 'MQTT_BROKER_PORT_TLS', 8883)
    
    # Autenticação (para ambiente sem mTLS - desenvolvimento)
    BROKER_USER = getattr(settings, 'MQTT_BROKER_USER', None)
    BROKER_PASSWORD = getattr(settings, 'MQTT_BROKER_PASSWORD', None)
    
    # Cliente
    CLIENT_ID = "django_tds_new_consumer"
    KEEPALIVE = getattr(settings, 'MQTT_KEEPALIVE', 60)
    
    # Topics
    TOPIC_PREFIX = getattr(settings, 'MQTT_TOPIC_PREFIX', 'tds_new/devices')
    TOPIC_TELEMETRY = f"{TOPIC_PREFIX}/+/telemetry"  # Wildcard para todos os gateways
    TOPIC_COMMANDS = f"{TOPIC_PREFIX}/+/commands/#"  # Para enviar comandos (futuro)
    
    # QoS (Quality of Service)
    QOS_SUBSCRIBE = 1  # At least once
    QOS_PUBLISH = 1    # At least once
    
    # TLS/mTLS (Certificados X.509)
    USE_TLS = getattr(settings, 'MQTT_USE_TLS', False)
    
    # Caminhos dos certificados (apenas se USE_TLS=True)
    CA_CERTS = getattr(settings, 'MQTT_CA_CERTS', '/app/certs/ca.crt')
    CERTFILE = getattr(settings, 'MQTT_CERTFILE', '/app/certs/django-consumer-cert.pem')
    KEYFILE = getattr(settings, 'MQTT_KEYFILE', '/app/certs/django-consumer-key.pem')
    
    # Reconnect settings
    RECONNECT_DELAY_MIN = 1   # segundos
    RECONNECT_DELAY_MAX = 120  # segundos
    
    @classmethod
    def get_broker_url(cls):
        """Retorna URL do broker para logs"""
        protocol = 'mqtts' if cls.USE_TLS else 'mqtt'
        port = cls.BROKER_PORT_TLS if cls.USE_TLS else cls.BROKER_PORT
        return f"{protocol}://{cls.BROKER_HOST}:{port}"
    
    @classmethod
    def validate(cls):
        """Valida configurações antes de conectar"""
        errors = []
        
        if not cls.BROKER_HOST:
            errors.append("MQTT_BROKER_HOST não configurado")
        
        if cls.USE_TLS:
            if not os.path.exists(cls.CA_CERTS):
                errors.append(f"Certificado CA não encontrado: {cls.CA_CERTS}")
            if not os.path.exists(cls.CERTFILE):
                errors.append(f"Certificado cliente não encontrado: {cls.CERTFILE}")
            if not os.path.exists(cls.KEYFILE):
                errors.append(f"Chave privada não encontrada: {cls.KEYFILE}")
        
        if errors:
            raise ValueError("Erros na configuração MQTT:\\n" + "\\n".join(f"  - {e}" for e in errors))
        
        return True
