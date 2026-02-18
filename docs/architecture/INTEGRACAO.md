# 🔄 Arquitetura de Integração - TDS New

**Projeto:** TDS New - Sistema de Telemetria e Monitoramento IoT  
**Versão:** 1.0  
**Data:** 18/02/2026  
**Autor:** Equipe TDS New

---

## 📋 ÍNDICE

1. [Visão Geral](#-visão-geral)
2. [Diagrama de Sequência End-to-End](#-diagrama-de-sequência-end-to-end)
3. [Camada 1: Firmware (Dispositivo → MQTT)](#-camada-1-firmware-dispositivo--mqtt)
4. [Camada 2: Broker MQTT (mTLS Authentication)](#-camada-2-broker-mqtt-mtls-authentication)
5. [Camada 3: Django Consumer (MQTT → Backend)](#-camada-3-django-consumer-mqtt--backend)
6. [Camada 4: TimescaleDB (Armazenamento e Agregação)](#-camada-4-timescaledb-armazenamento-e-agregação)
7. [Camada 5: Dashboard (Visualização)](#-camada-5-dashboard-visualização)
8. [Formato de Dados por Camada](#-formato-de-dados-por-camada)
9. [Tratamento de Erros e Retry](#-tratamento-de-erros-e-retry)
10. [Performance e Latência](#-performance-e-latência)
11. [Monitoramento e Observabilidade](#-monitoramento-e-observabilidade)
12. [Referências](#-referências)

---

## 🎯 VISÃO GERAL

### Objetivo
Documentar o fluxo completo de integração entre as 5 camadas do sistema TDS New, desde a coleta de dados no dispositivo IoT até a visualização no dashboard web.

### Princípios de Design
- ✅ **Desacoplamento**: Cada camada opera independentemente
- ✅ **Resiliência**: Retry automático em caso de falha
- ✅ **Rastreabilidade**: Logs em todas as etapas
- ✅ **Performance**: Pipeline otimizado para baixa latência
- ✅ **Segurança**: Autenticação e criptografia em todos os pontos

### Stack Tecnológico

| Camada | Tecnologia | Responsabilidade |
|--------|------------|------------------|
| **1. Firmware** | C/Arduino (ESP32) ou Python (RPi) | Coleta Modbus RTU → MQTT |
| **2. Broker** | Eclipse Mosquitto 2.x | Autenticação mTLS, ACL, routing |
| **3. Backend** | Django 5.1 + Celery + Paho-MQTT | Ingestão, validação, persistência |
| **4. Database** | PostgreSQL 17 + TimescaleDB 2.17 | Hypertable, continuous aggregates |
| **5. Frontend** | Django Templates + Bootstrap 5 + Chart.js | Dashboard, relatórios, alertas |

---

## 🔀 DIAGRAMA DE SEQUÊNCIA END-TO-END

```
┌──────────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  DISPOSITIVO │     │    BROKER   │     │    DJANGO    │     │  TIMESCALE   │     │  DASHBOARD   │
│  (Gateway)   │     │  MOSQUITTO  │     │   CONSUMER   │     │      DB      │     │   (Web UI)   │
└──────┬───────┘     └──────┬──────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │                    │
       │ [1] Leitura Modbus │                    │                    │                    │
       │◄───────────────────┤                    │                    │                    │
       │                    │                    │                    │                    │
       │ [2] Constrói JSON  │                    │                    │                    │
       │────────────────────►                    │                    │                    │
       │                    │                    │                    │                    │
       │ [3] PUBLISH MQTT + mTLS                 │                    │                    │
       │────────────────────►                    │                    │                    │
       │                    │                    │                    │                    │
       │                    │ [4] Valida Certificado X.509            │                    │
       │                    │────────────────────►                    │                    │
       │                    │                    │                    │                    │
       │                    │ [5] Verifica ACL (write permission)     │                    │
       │                    │────────────────────►                    │                    │
       │                    │                    │                    │                    │
       │                    │ [6] Roteia mensagem                     │                    │
       │                    │────────────────────►                    │                    │
       │                    │                    │                    │                    │
       │                    │                    │ [7] on_message() callback              │
       │                    │                    │◄───────────────────►                    │
       │                    │                    │                    │                    │
       │                    │                    │ [8] Extrai MAC do topic                │
       │                    │                    │────────────────────►                    │
       │                    │                    │                    │                    │
       │                    │                    │ [9] SELECT Gateway WHERE mac=?         │
       │                    │                    │────────────────────►                    │
       │                    │                    │◄────────────────────                    │
       │                    │                    │                    │                    │
       │                    │                    │ [10] Resolve conta_id                  │
       │                    │                    │────────────────────►                    │
       │                    │                    │                    │                    │
       │                    │                    │ [11] Valida JSON schema                │
       │                    │                    │────────────────────►                    │
       │                    │                    │                    │                    │
       │                    │                    │ [12] Processa leituras (loop)          │
       │                    │                    │────────────────────►                    │
       │                    │                    │                    │                    │
       │                    │                    │ [13] bulk_create(LeituraDispositivo[]) │
       │                    │                    │────────────────────►                    │
       │                    │                    │                    │                    │
       │                    │                    │                    │ [14] INSERT hypertable
       │                    │                    │                    │────────────────────►
       │                    │                    │                    │                    │
       │                    │                    │ [15] UPDATE Gateway.last_seen          │
       │                    │                    │────────────────────►                    │
       │                    │                    │                    │                    │
       │                    │ [16] PUBACK (QoS 1)                     │                    │
       │◄────────────────────                    │                    │                    │
       │                    │                    │                    │                    │
       │                    │                    │                    │ [17] Continuous Aggregate (a cada 1h)
       │                    │                    │                    │────────────────────►
       │                    │                    │                    │                    │
       │                    │                    │                    │                    │ [18] User request
       │                    │                    │                    │                    │◄───────────────
       │                    │                    │                    │                    │
       │                    │                    │ [19] SELECT consumo_mensal             │
       │                    │                    │◄────────────────────────────────────────│
       │                    │                    │                    │                    │
       │                    │                    │                    │ [20] Query aggregate
       │                    │                    │                    │◄────────────────────│
       │                    │                    │                    │────────────────────►
       │                    │                    │                    │                    │
       │                    │                    │ [21] Renderiza Chart.js                │
       │                    │                    │────────────────────────────────────────►
       │                    │                    │                    │                    │
```

---

## 🔧 CAMADA 1: FIRMWARE (Dispositivo → MQTT)

### Responsabilidades
1. **Coleta de dados**: Leitura de registros Modbus RTU (polling a cada 5 minutos)
2. **Agregação local**: Acumular leituras de até 8 dispositivos Modbus
3. **Serialização**: Construir payload JSON conforme schema esperado
4. **Publicação MQTT**: Enviar via mTLS para broker na porta 8883

### Fluxo Detalhado (ESP32/Arduino)

```cpp
// firmware/esp32/main.cpp

void loop() {
    // [Etapa 1.1] Polling Modbus RTU (a cada 5 minutos)
    if (millis() - lastReadTime > MODBUS_READ_INTERVAL) {
        for (int i = 0; i < numDispositivos; i++) {
            // Ler registro Modbus (exemplo: holding register 40001)
            uint16_t valor = modbus.readHoldingRegister(
                dispositivos[i].slave_id, 
                dispositivos[i].register_modbus
            );
            
            leituras[i] = {
                .dispositivo_codigo = dispositivos[i].codigo,
                .valor = valor / 100.0,  // Conversão (ex: 12345 → 123.45)
                .unidade = dispositivos[i].unidade
            };
        }
        
        // [Etapa 1.2] Construir JSON payload
        String payload = construirPayloadJSON(leituras, numDispositivos);
        
        // [Etapa 1.3] Publicar via MQTT com QoS 1 (at least once)
        mqttClient.publish(
            topic.c_str(),        // tds_new/devices/{mac}/telemetry
            payload.c_str(),
            false,                // retain = false (não é estado persistente)
            1                     // QoS 1 (aguarda PUBACK)
        );
        
        lastReadTime = millis();
    }
    
    // [Etapa 1.4] Processar loop MQTT (keepalive, reconnect)
    mqttClient.loop();
}

String construirPayloadJSON(Leitura leituras[], int count) {
    StaticJsonDocument<2048> doc;
    
    doc["gateway_mac"] = MAC_ADDRESS;  // aa:bb:cc:dd:ee:ff
    doc["timestamp"] = getIsoTimestamp();  // 2026-02-18T14:30:00Z
    
    JsonArray arr = doc.createNestedArray("leituras");
    for (int i = 0; i < count; i++) {
        JsonObject obj = arr.createNestedObject();
        obj["dispositivo_codigo"] = leituras[i].dispositivo_codigo;
        obj["valor"] = leituras[i].valor;
        obj["unidade"] = leituras[i].unidade;
    }
    
    String output;
    serializeJson(doc, output);
    return output;
}
```

### Configuração mTLS (ESP32)

```cpp
// firmware/esp32/mqtt_config.cpp

WiFiClientSecure wifiClient;
PubSubClient mqttClient(wifiClient);

void setupMQTT() {
    // [Etapa 1.5] Carregar certificados da SPIFFS
    File caCert = SPIFFS.open("/certs/ca.crt", "r");
    File clientCert = SPIFFS.open("/certs/device-cert.pem", "r");
    File clientKey = SPIFFS.open("/certs/device-key.pem", "r");
    
    wifiClient.setCACert(caCert.readString().c_str());
    wifiClient.setCertificate(clientCert.readString().c_str());
    wifiClient.setPrivateKey(clientKey.readString().c_str());
    
    // [Etapa 1.6] Conectar ao broker com mTLS
    mqttClient.setServer(MQTT_BROKER, 8883);
    mqttClient.connect(MAC_ADDRESS);  // Client ID = MAC address
}
```

### Exemplo de Payload JSON (Saída da Etapa 1.2)

```json
{
  "gateway_mac": "aa:bb:cc:dd:ee:ff",
  "timestamp": "2026-02-18T14:30:00Z",
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
```

**Tamanho médio do payload:** ~350 bytes (8 dispositivos)  
**Frequência de publicação:** A cada 5 minutos  
**Banda mensal por gateway:** ~2.5 MB/mês (com QoS 1)

---

## 🔐 CAMADA 2: BROKER MQTT (mTLS Authentication)

### Responsabilidades
1. **Autenticação mTLS**: Validar certificado X.509 do cliente
2. **Autorização ACL**: Verificar permissões de publicação
3. **Revogação**: Rejeitar certificados na CRL (Certificate Revocation List)
4. **Roteamento**: Entregar mensagem aos subscribers autorizados

### Configuração Mosquitto (mosquitto.conf)

```conf
# /etc/mosquitto/mosquitto.conf

# [Etapa 2.1] Porta TLS obrigatória (porta 1883 desabilitada)
listener 8883
protocol mqtt

# [Etapa 2.2] Exigir autenticação mTLS
require_certificate true
use_identity_as_username true  # CN do certificado = username

# [Etapa 2.3] Certificados CA authority
cafile /etc/mosquitto/certs/ca.crt
certfile /etc/mosquitto/certs/broker-cert.pem
keyfile /etc/mosquitto/certs/broker-key.pem

# [Etapa 2.4] Certificate Revocation List (CRL)
crlfile /etc/mosquitto/certs/crl.pem

# [Etapa 2.5] ACL (Access Control List)
acl_file /etc/mosquitto/acl.conf

# [Etapa 2.6] Logs detalhados
log_type all
log_dest file /var/log/mosquitto/mosquitto.log
```

### ACL Configuration (acl.conf)

```conf
# /etc/mosquitto/acl.conf

# [Etapa 2.7] Permissões por Common Name (CN = MAC address)

# Padrão: Negar tudo
user #

# Gateway pode PUBLICAR apenas em seu próprio topic
# %u = username (CN do certificado = MAC address)
pattern write tds_new/devices/%u/telemetry

# Gateway pode RECEBER comandos OTA
# (ex: atualização de certificado, configuração)
pattern read tds_new/devices/%u/commands/#

# Backend Django pode SUBSCREVER todos os topics de telemetria
user django_consumer
topic read tds_new/devices/+/telemetry

# Backend Django pode PUBLICAR comandos para qualquer gateway
user django_consumer
topic write tds_new/devices/+/commands/#
```

### Fluxo de Validação mTLS (Etapas 2.1 a 2.4)

```
1. Gateway inicia handshake TLS
   ↓
2. Mosquitto solicita certificado cliente
   ↓
3. Gateway envia certificado X.509 (device-cert.pem)
   ↓
4. Mosquitto valida assinatura contra CA (ca.crt)
   ✅ Assinatura válida? Continue
   ❌ Assinatura inválida? Rejeitar conexão
   ↓
5. Mosquitto verifica expiração (expires_at)
   ✅ Certificado válido? Continue
   ❌ Certificado expirado? Rejeitar conexão
   ↓
6. Mosquitto verifica CRL (crl.pem)
   ✅ Serial number NÃO está na CRL? Continue
   ❌ Serial number na CRL? Rejeitar conexão (certificado revogado)
   ↓
7. Mosquitto extrai CN (Common Name) do certificado
   CN = aa:bb:cc:dd:ee:ff
   ↓
8. Mosquitto define username MQTT = CN
   ↓
9. Conexão autenticada: Cliente "aa:bb:cc:dd:ee:ff" conectado
```

### Logs do Mosquitto (Exemplo de Conexão Bem-Sucedida)

```log
1708268400: New connection from 192.168.1.50 on port 8883.
1708268400: Client aa:bb:cc:dd:ee:ff sent CONNECT
1708268400: Certificate verification: Subject CN=aa:bb:cc:dd:ee:ff
1708268400: Certificate verification: Issuer CN=TDS-New-CA
1708268400: Certificate verification: Not before 2024-02-18 00:00:00
1708268400: Certificate verification: Not after 2034-02-18 00:00:00
1708268400: Certificate verification: Serial 4E3F2A1B9C8D7E6F
1708268400: Certificate verification: Not found in CRL ✅
1708268400: New client connected from 192.168.1.50 as aa:bb:cc:dd:ee:ff (p2, c1, k60).
```

---

## ⚙️ CAMADA 3: DJANGO CONSUMER (MQTT → Backend)

### Responsabilidades
1. **Subscribe MQTT**: Conectar ao broker e escutar topic wildcard
2. **Callback on_message**: Processar mensagens recebidas
3. **Lookup de Gateway**: Resolver `conta_id` a partir do MAC address
4. **Validação de payload**: Schema JSON, tipos de dados, ranges
5. **Persistência**: Bulk insert em LeituraDispositivo (TimescaleDB)
6. **Atualização de estado**: `Gateway.last_seen`, `Gateway.is_online`
7. **Auditoria**: Registrar logs de todas as leituras recebidas

### Implementação Django/Celery

**Arquivo: `tds_new/consumers/mqtt_telemetry.py`**

```python
import paho.mqtt.client as mqtt
import json
import logging
from django.utils import timezone
from tds_new.models import Gateway, Dispositivo, LeituraDispositivo
from tds_new.services.telemetry import TelemetryProcessorService

logger = logging.getLogger('mqtt_consumer')

# [Etapa 3.1] Configuração do cliente MQTT
def create_mqtt_client():
    client = mqtt.Client(client_id="django_consumer", protocol=mqtt.MQTTv311)
    
    # [Etapa 3.2] Configurar mTLS
    client.tls_set(
        ca_certs="/app/certs/ca.crt",
        certfile="/app/certs/django-consumer-cert.pem",
        keyfile="/app/certs/django-consumer-key.pem"
    )
    
    # [Etapa 3.3] Callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    return client


# [Etapa 3.4] Callback: Conexão estabelecida
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("✅ Conectado ao broker MQTT")
        
        # [Etapa 3.5] Subscribe ao topic wildcard (QoS 1)
        client.subscribe("tds_new/devices/+/telemetry", qos=1)
        logger.info("📡 Subscrito em: tds_new/devices/+/telemetry")
    else:
        logger.error(f"❌ Falha na conexão MQTT: {rc}")


# [Etapa 3.6] Callback: Mensagem recebida
def on_message(client, userdata, msg):
    try:
        # [Etapa 3.7] Log de recebimento
        logger.info(f"📨 Mensagem recebida: {msg.topic} ({len(msg.payload)} bytes)")
        
        # [Etapa 3.8] Extrair MAC address do topic
        # Topic: tds_new/devices/aa:bb:cc:dd:ee:ff/telemetry
        parts = msg.topic.split('/')
        if len(parts) != 4:
            logger.error(f"❌ Topic inválido: {msg.topic}")
            return
        
        mac_address = parts[2]
        logger.debug(f"🔍 MAC extraído: {mac_address}")
        
        # [Etapa 3.9] Lookup de Gateway (resolve conta_id)
        try:
            gateway = Gateway.objects.select_related('conta').get(mac=mac_address)
            logger.debug(f"✅ Gateway encontrado: {gateway.codigo} (conta={gateway.conta.nome})")
        except Gateway.DoesNotExist:
            logger.error(f"❌ Gateway não encontrado: {mac_address}")
            return
        
        # [Etapa 3.10] Parse JSON payload
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON inválido: {e}")
            return
        
        # [Etapa 3.11] Processar telemetria (service layer)
        service = TelemetryProcessorService(conta_id=gateway.conta_id, gateway=gateway)
        resultado = service.processar_telemetria(payload)
        
        logger.info(f"✅ Processado: {resultado['leituras_criadas']} leituras")
        
    except Exception as e:
        logger.exception(f"💥 Erro ao processar mensagem: {e}")


# [Etapa 3.12] Callback: Desconexão
def on_disconnect(client, userdata, rc):
    if rc != 0:
        logger.warning(f"⚠️ Desconexão inesperada (rc={rc}). Tentando reconectar...")
```

**Arquivo: `tds_new/services/telemetry.py`**

```python
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from tds_new.models import Gateway, Dispositivo, LeituraDispositivo
import logging

logger = logging.getLogger('telemetry_service')

class TelemetryProcessorService:
    """Serviço de negócio para processamento de telemetria"""
    
    def __init__(self, conta_id, gateway):
        self.conta_id = conta_id
        self.gateway = gateway
    
    def processar_telemetria(self, payload):
        """
        Processa payload JSON de telemetria e persiste no banco
        
        Payload esperado:
        {
            "gateway_mac": "aa:bb:cc:dd:ee:ff",
            "timestamp": "2026-02-18T14:30:00Z",
            "leituras": [
                {"dispositivo_codigo": "D01", "valor": 123.45, "unidade": "kWh"},
                ...
            ]
        }
        """
        
        # [Etapa 3.13] Validar schema básico
        if not self._validar_payload(payload):
            raise ValueError("Payload JSON inválido")
        
        timestamp = timezone.datetime.fromisoformat(payload['timestamp'].replace('Z', '+00:00'))
        leituras_data = payload['leituras']
        
        # [Etapa 3.14] Preparar objetos para bulk_create
        leituras_objetos = []
        
        for item in leituras_data:
            # [Etapa 3.15] Lookup de Dispositivo (validar que pertence ao gateway)
            try:
                dispositivo = Dispositivo.objects.get(
                    gateway=self.gateway,
                    codigo=item['dispositivo_codigo']
                )
            except Dispositivo.DoesNotExist:
                logger.warning(f"⚠️ Dispositivo não encontrado: {item['dispositivo_codigo']}")
                continue
            
            # [Etapa 3.16] Criar objeto LeituraDispositivo (ainda não salvo)
            leitura = LeituraDispositivo(
                time=timestamp,
                conta_id=self.conta_id,
                gateway=self.gateway,
                dispositivo=dispositivo,
                valor=Decimal(str(item['valor'])),
                unidade=item['unidade'],
                payload_raw=item  # JSON completo para auditoria
            )
            leituras_objetos.append(leitura)
        
        # [Etapa 3.17] Transação atômica: bulk_create + update Gateway
        with transaction.atomic():
            # [Etapa 3.18] Bulk insert em hypertable (TimescaleDB)
            LeituraDispositivo.objects.bulk_create(leituras_objetos)
            
            # [Etapa 3.19] Atualizar estado do gateway
            self.gateway.last_seen = timezone.now()
            self.gateway.is_online = True
            self.gateway.save(update_fields=['last_seen', 'is_online'])
        
        logger.info(f"✅ {len(leituras_objetos)} leituras persistidas para {self.gateway.codigo}")
        
        return {
            'sucesso': True,
            'leituras_criadas': len(leituras_objetos),
            'timestamp': timestamp
        }
    
    def _validar_payload(self, payload):
        """Validação básica do schema JSON"""
        campos_obrigatorios = ['gateway_mac', 'timestamp', 'leituras']
        
        for campo in campos_obrigatorios:
            if campo not in payload:
                logger.error(f"❌ Campo obrigatório ausente: {campo}")
                return False
        
        if not isinstance(payload['leituras'], list):
            logger.error("❌ Campo 'leituras' deve ser array")
            return False
        
        for item in payload['leituras']:
            if not all(k in item for k in ['dispositivo_codigo', 'valor', 'unidade']):
                logger.error(f"❌ Item de leitura inválido: {item}")
                return False
        
        return True
```

**Arquivo: `tds_new/management/commands/start_mqtt_consumer.py`**

```python
from django.core.management.base import BaseCommand
from tds_new.consumers.mqtt_telemetry import create_mqtt_client
import logging

logger = logging.getLogger('mqtt_consumer')

class Command(BaseCommand):
    help = 'Inicia o consumer MQTT para telemetria'
    
    def handle(self, *args, **options):
        logger.info("🚀 Iniciando MQTT Consumer...")
        
        # [Etapa 3.20] Criar e conectar cliente
        client = create_mqtt_client()
        client.connect("mqtt-broker.tds-new.local", 8883, keepalive=60)
        
        # [Etapa 3.21] Loop infinito (blocking)
        logger.info("📡 Consumer ativo. Aguardando mensagens...")
        client.loop_forever()
```

**Execução via Systemd**:

```bash
# /etc/systemd/system/tds-new-mqtt-consumer.service

[Unit]
Description=TDS New MQTT Consumer
After=network.target postgresql.service mosquitto.service

[Service]
Type=simple
User=tds-new
WorkingDirectory=/var/server-app/apps/prj_tds_new
ExecStart=/var/server-app/apps/prj_tds_new/venv/bin/python manage.py start_mqtt_consumer
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## 💾 CAMADA 4: TIMESCALEDB (Armazenamento e Agregação)

### Responsabilidades
1. **Hypertable**: Particionar automaticamente por timestamp (chunks de 1 dia)
2. **Continuous Aggregate**: Materializar agregações mensais (refresh a cada 1h)
3. **Data Retention**: Política de retenção (manter 2 anos, apagar chunks antigos)
4. **Índices**: Otimizar queries por conta, dispositivo e timestamp

### Configuração da Hypertable

```sql
-- Script: scripts/setup_timescaledb.sql

-- [Etapa 4.1] Criar hypertable para LeituraDispositivo
SELECT create_hypertable(
    'tds_new_leitura_dispositivo',  -- Tabela Django
    'time',                          -- Coluna de particionamento
    chunk_time_interval => INTERVAL '1 day',  -- Chunk de 1 dia
    if_not_exists => TRUE
);

-- [Etapa 4.2] Índices compostos para queries comuns
CREATE INDEX IF NOT EXISTS idx_leitura_conta_time 
ON tds_new_leitura_dispositivo (conta_id, time DESC);

CREATE INDEX IF NOT EXISTS idx_leitura_dispositivo_time 
ON tds_new_leitura_dispositivo (dispositivo_id, time DESC);

CREATE INDEX IF NOT EXISTS idx_leitura_gateway_time 
ON tds_new_leitura_dispositivo (gateway_id, time DESC);
```

### Continuous Aggregate (Consumo Mensal)

```sql
-- [Etapa 4.3] Criar continuous aggregate (view materializada)
CREATE MATERIALIZED VIEW tds_new_consumo_mensal
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 month', time) AS mes_referencia,
    conta_id,
    gateway_id,
    dispositivo_id,
    SUM(valor) AS total_consumo,
    AVG(valor) AS media_diaria,
    MIN(valor) AS min_valor,
    MAX(valor) AS max_valor,
    COUNT(*) AS leituras_count,
    COUNT(DISTINCT DATE(time)) AS dias_com_leitura
FROM tds_new_leitura_dispositivo
GROUP BY mes_referencia, conta_id, gateway_id, dispositivo_id
WITH NO DATA;

-- [Etapa 4.4] Policy de refresh (atualizar a cada 1 hora)
SELECT add_continuous_aggregate_policy(
    'tds_new_consumo_mensal',
    start_offset => INTERVAL '3 months',  -- Janela de 3 meses para trás
    end_offset => INTERVAL '1 hour',      -- Até 1 hora atrás (dados recentes)
    schedule_interval => INTERVAL '1 hour'  -- Executar a cada 1 hora
);
```

### Data Retention Policy

```sql
-- [Etapa 4.5] Política de retenção (apagar chunks > 2 anos)
SELECT add_retention_policy(
    'tds_new_leitura_dispositivo',
    INTERVAL '2 years',
    if_not_exists => TRUE
);
```

### Fluxo de Inserção (Etapa 3.18 → 4.1)

```sql
-- Query gerada pelo Django bulk_create (simplificado)
INSERT INTO tds_new_leitura_dispositivo (
    time, conta_id, gateway_id, dispositivo_id, valor, unidade, payload_raw
) VALUES 
    ('2026-02-18 14:30:00+00', 1, 5, 12, 123.45, 'kWh', '{"dispositivo_codigo": "D01", ...}'),
    ('2026-02-18 14:30:00+00', 1, 5, 13, 67.89, 'm³', '{"dispositivo_codigo": "D02", ...}'),
    ('2026-02-18 14:30:00+00', 1, 5, 14, 22.5, '°C', '{"dispositivo_codigo": "D03", ...}');

-- [Resposta do TimescaleDB]
-- ✅ Chunk [chunk_2026_02_18_00_00] AUTO-CRIADO
-- ✅ 3 rows inserted
-- ⏱️ Query time: 2.3ms
```

### Atualização do Continuous Aggregate (Automática)

```log
# Logs do TimescaleDB (Policy Job)

2026-02-18 15:00:00 UTC [12345]: LOG: starting background worker "Policy Refresh [1000]"
2026-02-18 15:00:00 UTC [12345]: LOG: refreshing continuous aggregate "tds_new_consumo_mensal"
2026-02-18 15:00:00 UTC [12345]: LOG: time window: [2025-11-18 15:00:00+00, 2026-02-18 14:00:00+00]
2026-02-18 15:00:05 UTC [12345]: LOG: ✅ refresh completed (67,234 rows updated, 5.2s)
```

---

## 📊 CAMADA 5: DASHBOARD (Visualização)

### Responsabilidades
1. **Query de dados**: Consultar continuous aggregate para performance
2. **Agregação adicional**: Filtros de data, comparações, rankings
3. **Renderização**: Gráficos Chart.js, tabelas Bootstrap 5
4. **Alertas visuais**: Badges de status (online/offline), thresholds ultrapassados
5. **Exportação**: PDF (reportlab), Excel (openpyxl)

### View Django (Backend)

**Arquivo: `tds_new/views/dashboard.py`**

```python
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Avg
from tds_new.models import Gateway, ConsumoMensal
from datetime import datetime, timedelta

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'tds_new/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conta = self.request.conta_ativa
        
        # [Etapa 5.1] Query de consumo mensal (último 6 meses)
        seis_meses_atras = datetime.now() - timedelta(days=180)
        
        consumo_mensal = ConsumoMensal.objects.filter(
            conta=conta,
            mes_referencia__gte=seis_meses_atras
        ).values(
            'mes_referencia', 'dispositivo__nome'
        ).annotate(
            total=Sum('total_consumo')
        ).order_by('mes_referencia')
        
        # [Etapa 5.2] Preparar dados para Chart.js
        labels = []
        datasets = {}
        
        for item in consumo_mensal:
            mes = item['mes_referencia'].strftime('%m/%Y')
            dispositivo = item['dispositivo__nome']
            total = float(item['total'])
            
            if mes not in labels:
                labels.append(mes)
            
            if dispositivo not in datasets:
                datasets[dispositivo] = []
            
            datasets[dispositivo].append(total)
        
        # [Etapa 5.3] Gateways online/offline
        gateways_online = Gateway.objects.filter(
            conta=conta,
            is_online=True
        ).count()
        
        gateways_offline = Gateway.objects.filter(
            conta=conta,
            is_online=False
        ).count()
        
        context.update({
            'chart_labels': labels,
            'chart_datasets': datasets,
            'gateways_online': gateways_online,
            'gateways_offline': gateways_offline,
            'titulo_pagina': 'Dashboard de Telemetria'
        })
        
        return context
```

### Template Django (Frontend)

**Arquivo: `tds_new/templates/tds_new/dashboard.html`**

```django
{% extends 'layouts/base_cenario.html' %}
{% load static %}

{% block extra_css %}
<style>
    .card-metric {
        border-left: 4px solid #007bff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .status-online { color: #28a745; }
    .status-offline { color: #dc3545; }
</style>
{% endblock %}

{% block content %}
<!-- [Etapa 5.4] Cards de métricas -->
<div class="row mb-4">
    <div class="col-md-6">
        <div class="card card-metric">
            <div class="card-body">
                <h5 class="card-title">Gateways Online</h5>
                <h2 class="status-online">
                    <i class="bi bi-wifi"></i> {{ gateways_online }}
                </h2>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card card-metric">
            <div class="card-body">
                <h5 class="card-title">Gateways Offline</h5>
                <h2 class="status-offline">
                    <i class="bi bi-wifi-off"></i> {{ gateways_offline }}
                </h2>
            </div>
        </div>
    </div>
</div>

<!-- [Etapa 5.5] Gráfico de linha (Chart.js) -->
<div class="card mb-4">
    <div class="card-header">
        <h5>Consumo Mensal por Dispositivo (Últimos 6 Meses)</h5>
    </div>
    <div class="card-body">
        <canvas id="chartConsumoMensal" height="80"></canvas>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
<script>
// [Etapa 5.6] Renderizar gráfico Chart.js
const ctx = document.getElementById('chartConsumoMensal').getContext('2d');

// [Etapa 5.7] Dados do backend (template variables → JS)
const chartData = {
    labels: {{ chart_labels|safe }},  // ['01/2026', '02/2026', ...]
    datasets: [
        {% for dispositivo, valores in chart_datasets.items %}
        {
            label: '{{ dispositivo }}',
            data: {{ valores|safe }},  // [123.45, 156.78, ...]
            borderColor: getRandomColor(),
            backgroundColor: 'rgba(0,0,0,0)',
            tension: 0.3
        },
        {% endfor %}
    ]
};

const chart = new Chart(ctx, {
    type: 'line',
    data: chartData,
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: false
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Consumo (kWh / m³)'
                }
            }
        }
    }
});

function getRandomColor() {
    const colors = ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8'];
    return colors[Math.floor(Math.random() * colors.length)];
}
</script>
{% endblock %}
```

---

## 📐 FORMATO DE DADOS POR CAMADA

### Resumo de Transformações

| Camada | Formato de Entrada | Formato de Saída |
|--------|-------------------|------------------|
| **1. Firmware** | Registros Modbus RTU (binary) | JSON payload (UTF-8) |
| **2. Broker** | MQTT message (topic + payload) | MQTT message roteada |
| **3. Django** | JSON payload | Objetos Django ORM |
| **4. TimescaleDB** | SQL INSERT (bulk) | Rows em hypertable + aggregate |
| **5. Dashboard** | SQL SELECT (aggregate) | HTML + Chart.js JSON |

### Exemplo de Transformação Completa

**1. Firmware (Modbus RTU → Memória):**
```cpp
uint16_t raw_value = 12345;  // Registro Modbus (holding register 40001)
float valor = raw_value / 100.0;  // 12345 → 123.45 kWh
```

**2. Firmware (Memória → JSON):**
```json
{
  "dispositivo_codigo": "D01",
  "valor": 123.45,
  "unidade": "kWh"
}
```

**3. Django (JSON → ORM):**
```python
leitura = LeituraDispositivo(
    time=datetime(2026, 2, 18, 14, 30, 0),
    conta_id=1,
    gateway_id=5,
    dispositivo_id=12,
    valor=Decimal('123.45'),
    unidade='kWh'
)
```

**4. TimescaleDB (ORM → SQL → Row):**
```sql
| time                | conta_id | gateway_id | dispositivo_id | valor  | unidade |
|---------------------|----------|------------|----------------|--------|---------|
| 2026-02-18 14:30:00 | 1        | 5          | 12             | 123.45 | kWh     |
```

**5. Dashboard (Aggregate → Chart.js):**
```javascript
{
  label: 'Medidor Água Sala 1',
  data: [123.45, 156.78, 189.23, ...],  // Consumo mensal
  borderColor: '#007bff'
}
```

---

## 🔁 TRATAMENTO DE ERROS E RETRY

### Estratégias por Camada

| Camada | Tipo de Erro | Estratégia | Timeout | Max Retries |
|--------|--------------|------------|---------|-------------|
| **1. Firmware** | Modbus timeout | Retry com backoff exponencial | 5s | 3 |
| **1. Firmware** | MQTT connection lost | Reconnect automático | 30s | Infinito |
| **2. Broker** | Certificate expired | Rejeitar + log | N/A | N/A |
| **2. Broker** | ACL denied | Rejeitar + log | N/A | N/A |
| **3. Django** | Gateway not found | Log warning + skip | N/A | N/A |
| **3. Django** | JSON parse error | Log error + skip | N/A | N/A |
| **3. Django** | Database timeout | Retry transação | 10s | 3 |
| **4. TimescaleDB** | Chunk creation | Auto-create + retry INSERT | 5s | 1 |
| **5. Dashboard** | Query timeout | Cache + exibir dados antigos | 30s | 1 |

### Exemplo: Retry no Firmware (ESP32)

```cpp
// firmware/esp32/modbus_reader.cpp

uint16_t readModbusWithRetry(uint8_t slaveId, uint16_t registerAddr) {
    const int MAX_RETRIES = 3;
    const int TIMEOUT_MS = 5000;
    
    for (int tentativa = 1; tentativa <= MAX_RETRIES; tentativa++) {
        uint16_t result = modbus.readHoldingRegister(slaveId, registerAddr);
        
        if (result != 0xFFFF) {  // 0xFFFF = erro
            return result;  // ✅ Sucesso
        }
        
        // ❌ Erro: aguardar backoff exponencial
        int delay = 1000 * pow(2, tentativa - 1);  // 1s, 2s, 4s
        Serial.printf("⚠️ Modbus timeout (tentativa %d/%d). Retry em %dms\n", 
                      tentativa, MAX_RETRIES, delay);
        delay(delay);
    }
    
    // ❌ Falha após 3 tentativas
    Serial.printf("💥 Modbus falhou após %d tentativas. Dispositivo offline?\n", MAX_RETRIES);
    return 0;  // Retornar 0 (será logado como leitura falhada)
}
```

### Exemplo: Retry no Django Consumer

```python
# tds_new/consumers/mqtt_telemetry.py

from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def salvar_leituras_com_retry(leituras_objetos, gateway):
    """Retry com backoff exponencial para deadlocks"""
    with transaction.atomic():
        LeituraDispositivo.objects.bulk_create(leituras_objetos)
        gateway.last_seen = timezone.now()
        gateway.is_online = True
        gateway.save(update_fields=['last_seen', 'is_online'])
```

---

## ⏱️ PERFORMANCE E LATÊNCIA

### Latência End-to-End (Dispositivo → Dashboard)

| Etapa | Componente | Latência Típica | Latência Máxima |
|-------|-----------|-----------------|-----------------|
| **1** | Modbus RTU read (8 dispositivos) | 200ms | 500ms |
| **2** | Construir JSON payload | 10ms | 50ms |
| **3** | MQTT publish + TLS handshake | 50ms | 200ms |
| **4** | Broker routing | 5ms | 20ms |
| **5** | Django on_message callback | 10ms | 50ms |
| **6** | Gateway.objects.get(mac=...) | 5ms | 20ms |
| **7** | JSON parse + validação | 5ms | 15ms |
| **8** | Bulk INSERT TimescaleDB | 10ms | 50ms |
| **9** | Continuous aggregate refresh | 0ms (assíncrono) | N/A |
| **10** | Dashboard query (aggregate) | 50ms | 200ms |
| **TOTAL** | Device → Database | **295ms** | **905ms** |
| **TOTAL** | Device → Dashboard (com cache) | **345ms** | **1.1s** |

**Observações:**
- ✅ Latência de **~300ms** é aceitável para telemetria (não tempo real crítico)
- ⚠️ Continuous aggregate tem refresh de **1 hora** (dados não são instantâneos)
- 🚀 Para dados em tempo real, usar WebSocket + query direta (bypass aggregate)

### Performance Esperada (Carga)

| Métrica | Valor | Observações |
|---------|-------|-------------|
| **Messages/segundo/gateway** | 0.0033 msg/s (1 msg a cada 5 min) | Baixa frequência |
| **Messages/segundo/sistema** | 33 msg/s (100 gateways) | Facilmente escalável |
| **Throughput MQTT** | ~11 KB/s (350 bytes × 33 msg/s) | Negligível |
| **Inserts/segundo TimescaleDB** | 264 rows/s (33 msg × 8 dispositivos) | Hypertable suporta 100k+/s |
| **Aggregate refresh time** | ~5s (para 67k rows/mês) | Executado de hora em hora |
| **Dashboard query time** | 50ms (6 meses agregados) | Com índices otimizados |

---

## 📈 MONITORAMENTO E OBSERVABILIDADE

### Métricas Críticas a Monitorar

**1. Firmware (ESP32/RPi):**
- Uptime do gateway
- Modbus read errors (taxa de falha)
- MQTT connection drops (taxa de reconexão)
- Memória livre (heap/RAM)

**2. Broker MQTT:**
- Conexões ativas
- Messages recebidas/segundo
- Certificate validation errors
- ACL denied attempts

**3. Django Consumer:**
- Messages processadas/segundo
- Gateway not found errors (%)
- Database insert errors (%)
- Processing latency (P50, P95, P99)

**4. TimescaleDB:**
- Chunk creation rate
- Hypertable size (GB)
- Continuous aggregate refresh time
- Query latency (P95)

**5. Dashboard:**
- Page load time
- Chart render time
- Cache hit rate

### Stack de Monitoramento Recomendado

- **Metrics**: Prometheus + TimescaleDB (self-scraping)
- **Logs**: Django logs → CloudWatch ou ELK Stack
- **Traces**: OpenTelemetry (opcional, para debugging profundo)
- **Dashboards**: Grafana
- **Alertas**: Prometheus Alertmanager

---

## 📚 REFERÊNCIAS

### Documentação Interna
- **[ROADMAP.md](../ROADMAP.md)**: Cronograma de implementação (Weeks 6-16)
- **[PROVISIONAMENTO_IOT.md](../PROVISIONAMENTO_IOT.md)**: Estratégias de provisionamento
- **[ADR-001](DECISOES.md#adr-001-mqtt-consumer-strategy)**: Decisão de usar Django Consumer
- **[ADR-002](DECISOES.md#adr-002-certificate-management-strategy)**: Certificados de 10 anos
- **[ADR-003](DECISOES.md#adr-003-topic-mqtt-sem-conta_id)**: Topic MQTT sem conta_id
- **[ADR-004](DECISOES.md#adr-004-ota-certificate-renewal-protocol)**: Protocolo OTA renewal

### Documentação Externa
- **[Eclipse Mosquitto](https://mosquitto.org/documentation/)**: Broker MQTT
- **[Paho MQTT Python](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php)**: Cliente MQTT
- **[TimescaleDB Docs](https://docs.timescale.com/)**: Hypertables e continuous aggregates
- **[Chart.js](https://www.chartjs.org/docs/)**: Biblioteca de gráficos
- **[Modbus Protocol](https://modbus.org/)**: Especificação Modbus RTU

---

**Última atualização:** 18/02/2026  
**Versão:** 1.0  
**Responsável:** Equipe TDS New

