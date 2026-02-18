# ==============================================================================
# TDS New - MQTT Telemetry Consumer
# ==============================================================================
# Arquivo: tds_new/consumers/mqtt_telemetry.py
# Responsabilidade: Cliente MQTT com callbacks para recebimento de telemetria
# ==============================================================================

import paho.mqtt.client as mqtt
import json
import logging
from django.utils import timezone
from tds_new.consumers.mqtt_config import MQTTConfig
from tds_new.models import Gateway
from tds_new.services.telemetry_processor import TelemetryProcessorService

logger = logging.getLogger('mqtt_consumer')

# ==============================================================================
# CLIENTE MQTT - CONFIGURAÇÃO E CALLBACKS
# ==============================================================================

def create_mqtt_client():
    """
    Cria e configura cliente MQTT com callbacks
    
    Returns:
        mqtt.Client: Cliente MQTT configurado
    """
    # Validar configurações antes de criar cliente
    try:
        MQTTConfig.validate()
    except ValueError as e:
        logger.error(f"[ERROR] Configuração MQTT inválida: {e}")
        raise
    
    # Criar cliente MQTT (protocolo v3.1.1)
    client = mqtt.Client(
        client_id=MQTTConfig.CLIENT_ID,
        protocol=mqtt.MQTTv311,
        clean_session=True  # TODO: False para QoS 1 persistente (após fix de múltiplas instâncias)
    )
    
    # Configurar TLS/mTLS (se habilitado)
    if MQTTConfig.USE_TLS:
        logger.info("[SETUP] Configurando mTLS...")
        try:
            client.tls_set(
                ca_certs=MQTTConfig.CA_CERTS,
                certfile=MQTTConfig.CERTFILE,
                keyfile=MQTTConfig.KEYFILE
            )
            logger.info(f"[OK] Certificados TLS carregados:")
            logger.info(f"   - CA: {MQTTConfig.CA_CERTS}")
            logger.info(f"   - Cert: {MQTTConfig.CERTFILE}")
            logger.info(f"   - Key: {MQTTConfig.KEYFILE}")
        except Exception as e:
            logger.error(f"[ERROR] Erro ao configurar TLS: {e}")
            raise
    
    # Configurar autenticação username/password (se configurado - desenvolvimento)
    if MQTTConfig.BROKER_USER and MQTTConfig.BROKER_PASSWORD:
        client.username_pw_set(
            username=MQTTConfig.BROKER_USER,
            password=MQTTConfig.BROKER_PASSWORD
        )
        logger.info(f"🔑 Autenticação configurada: {MQTTConfig.BROKER_USER}")
    
    # Registrar callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe
    client.on_log = on_log
    
    # Habilitar auto-reconnect
    client.reconnect_delay_set(
        min_delay=MQTTConfig.RECONNECT_DELAY_MIN,
        max_delay=MQTTConfig.RECONNECT_DELAY_MAX
    )
    
    logger.info(f"📡 Cliente MQTT configurado: {MQTTConfig.CLIENT_ID}")
    logger.info(f"🔗 Broker: {MQTTConfig.get_broker_url()}")
    
    return client


# ==============================================================================
# CALLBACK: ON_CONNECT
# ==============================================================================

def on_connect(client, userdata, flags, rc):
    """
    Callback chamado quando conexão com broker é estabelecida
    
    Args:
        client: Instância do cliente MQTT
        userdata: Dados do usuário (não usado)
        flags: Flags de resposta do broker
        rc: Result code (0 = sucesso)
    """
    if rc == 0:
        logger.info("[OK] Conectado ao broker MQTT com sucesso")
        logger.info(f"[INFO] Flags: {flags}")
        
        # Subscribe ao topic de telemetria (wildcard para todos os gateways)
        topic = MQTTConfig.TOPIC_TELEMETRY
        qos = MQTTConfig.QOS_SUBSCRIBE
        
        result, mid = client.subscribe(topic, qos=qos)
        
        if result == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"[LISTEN] Subscribe solicitado: {topic} (QoS {qos})")
            logger.info(f"   Message ID: {mid}")
        else:
            logger.error(f"[ERROR] Erro ao solicitar subscribe: {result}")
    else:
        error_messages = {
            1: "Connection refused - incorrect protocol version",
            2: "Connection refused - invalid client identifier",
            3: "Connection refused - server unavailable",
            4: "Connection refused - bad username or password",
            5: "Connection refused - not authorized"
        }
        error_msg = error_messages.get(rc, f"Unknown error code: {rc}")
        logger.error(f"[ERROR] Falha na conexão MQTT: {error_msg}")


# ==============================================================================
# CALLBACK: ON_SUBSCRIBE
# ==============================================================================

def on_subscribe(client, userdata, mid, granted_qos):
    """
    Callback chamado quando subscribe é confirmado pelo broker
    
    Args:
        client: Instância do cliente MQTT
        userdata: Dados do usuário (não usado)
        mid: Message ID do subscribe
        granted_qos: QoS garantido pelo broker
    """
    logger.info(f"[OK] Subscribe confirmado (mid={mid}, QoS={granted_qos[0]})")
    logger.info(f"[LISTEN] Aguardando mensagens em: {MQTTConfig.TOPIC_TELEMETRY}")


# ==============================================================================
# CALLBACK: ON_MESSAGE
# ==============================================================================

def on_message(client, userdata, msg):
    """
    Callback chamado quando mensagem é recebida
    
    Args:
        client: Instância do cliente MQTT
        userdata: Dados do usuário (não usado)
        msg: Mensagem MQTT (topic + payload)
    """
    try:
        # Log de recebimento
        logger.info(f"[MSG] Mensagem recebida: {msg.topic} ({len(msg.payload)} bytes)")
        
        # Extrair MAC address do topic
        # Formato esperado: tds_new/devices/<MAC>/telemetry
        parts = msg.topic.split('/')
        
        if len(parts) != 4:
            logger.error(f"[ERROR] Topic inválido: {msg.topic} (esperado 4 partes, recebido {len(parts)})")
            return
        
        if parts[0] != 'tds_new' or parts[1] != 'devices' or parts[3] != 'telemetry':
            logger.error(f"[ERROR] Formato de topic incorreto: {msg.topic}")
            return
        
        mac_address = parts[2]
        logger.debug(f"[DEBUG] MAC extraído do topic: {mac_address}")
        
        # Lookup de Gateway (resolve conta_id)
        try:
            gateway = Gateway.objects.select_related('conta').get(mac=mac_address)
            logger.debug(f"[OK] Gateway encontrado: {gateway.codigo} (conta={gateway.conta.name})")
        except Gateway.DoesNotExist:
            logger.warning(f"[WARN] Gateway não encontrado: {mac_address}")
            logger.warning(f"   Sugestão: Cadastrar gateway com MAC {mac_address} no sistema")
            return
        except Exception as e:
            logger.error(f"[ERROR] Erro ao buscar gateway: {e}")
            return
        
        # Parse JSON payload
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            logger.debug(f"[DATA] Payload JSON: {json.dumps(payload, indent=2)}")
        except json.JSONDecodeError as e:
            logger.error(f"[ERROR] JSON inválido: {e}")
            logger.error(f"   Payload recebido: {msg.payload[:200]}")  # Primeiros 200 bytes
            return
        except Exception as e:
            logger.error(f"[ERROR] Erro ao decodificar payload: {e}")
            return
        
        # Processar telemetria via service layer
        try:
            service = TelemetryProcessorService(
                conta_id=gateway.conta_id,
                gateway=gateway
            )
            
            resultado = service.processar_telemetria(payload)
            
            logger.info(f"[OK] Telemetria processada com sucesso:")
            logger.info(f"   - Leituras criadas: {resultado['leituras_criadas']}")
            logger.info(f"   - Timestamp: {resultado['timestamp']}")
            logger.info(f"   - Gateway: {gateway.codigo}")
            logger.info(f"   - Conta: {gateway.conta.name}")
            
        except ValueError as e:
            logger.error(f"[ERROR] Validação falhou: {e}")
        except Exception as e:
            logger.exception(f"[CRITICAL] Erro ao processar telemetria: {e}")
    
    except Exception as e:
        logger.exception(f"[CRITICAL] Erro crítico no callback on_message: {e}")


# ==============================================================================
# CALLBACK: ON_DISCONNECT
# ==============================================================================

def on_disconnect(client, userdata, rc):
    """
    Callback chamado quando conexão com broker é perdida
    
    Args:
        client: Instância do cliente MQTT
        userdata: Dados do usuário (não usado)
        rc: Result code (0 = desconexão limpa)
    """
    if rc == 0:
        logger.info("[INFO] Desconexão limpa do broker MQTT")
    else:
        logger.warning(f"[WARN] Desconexão inesperada (rc={rc})")
        logger.warning(f"[INFO] Auto-reconnect habilitado (min={MQTTConfig.RECONNECT_DELAY_MIN}s, max={MQTTConfig.RECONNECT_DELAY_MAX}s)")


# ==============================================================================
# CALLBACK: ON_LOG (DEBUG)
# ==============================================================================

def on_log(client, userdata, level, buf):
    """
    Callback para logs detalhados do Paho MQTT (apenas em DEBUG)
    
    Args:
        client: Instância do cliente MQTT
        userdata: Dados do usuário (não usado)
        level: Nível de log do Paho
        buf: Mensagem de log
    """
    # Mapear níveis Paho para níveis Python logging
    if level == mqtt.MQTT_LOG_DEBUG:
        logger.debug(f"[Paho] {buf}")
    elif level == mqtt.MQTT_LOG_INFO:
        logger.debug(f"[Paho] {buf}")  # Info do Paho vira debug no Python
    elif level == mqtt.MQTT_LOG_NOTICE:
        logger.info(f"[Paho] {buf}")
    elif level == mqtt.MQTT_LOG_WARNING:
        logger.warning(f"[Paho] {buf}")
    elif level == mqtt.MQTT_LOG_ERR:
        logger.error(f"[Paho] {buf}")
