# Fase 2 - Testes do MQTT Consumer

## 📋 Pré-requisitos

- ✅ Fase 1 concluída (Hypertable TimescaleDB criado)
- ✅ Mosquitto (broker MQTT) rodando em `localhost:1883`
- ✅ Gateway cadastrado no sistema com MAC `aa:bb:cc:dd:ee:ff`
- ✅ Dispositivos D01, D02, D03 vinculados ao gateway

## 🧪 Testes

### 1. Verificar Mosquitto Broker

```bash
# Verificar se Mosquitto está rodando
docker ps | grep mosquitto

# OU (se instalado localmente)
sudo systemctl status mosquitto
```

### 2. Iniciar Consumer Django

```bash
# Terminal 1: Consumer em modo debug
python manage.py start_mqtt_consumer --debug
```

**Saída esperada:**
```
╔═══════════════════════════════════════════════════╗
║   TDS NEW - MQTT TELEMETRY CONSUMER              ║
╚═══════════════════════════════════════════════════╝

📋 Configurações:
   • Broker: localhost:1883
   • Client ID: django_tds_new_consumer
   • Topic: tds_new/devices/+/telemetry
   • QoS: 1
   • TLS: Desabilitado ⚠️
   • Keepalive: 60s

🔧 Criando cliente MQTT...
   ✅ Cliente criado
🔗 Conectando ao broker localhost:1883...
   ✅ Conexão iniciada

╔═══════════════════════════════════════════════════╗
║   CONSUMER ATIVO - Aguardando mensagens          ║
╚═══════════════════════════════════════════════════╝
📡 Pressione Ctrl+C para encerrar

✅ Conectado ao broker MQTT com sucesso
📡 Subscribe solicitado: tds_new/devices/+/telemetry (QoS 1)
✅ Subscribe confirmado (mid=1, QoS=1)
🎯 Aguardando mensagens em: tds_new/devices/+/telemetry
```

### 3. Enviar Mensagem de Teste

```bash
# Terminal 2: Simulador MQTT
python tests/simuladores/mqtt_simulator.py
```

**Saída esperada (Terminal 2 - Simulador):**
```
🚀 Simulador MQTT - Telemetria de Teste
==================================================
Broker: localhost:1883
Topic: tds_new/devices/aa:bb:cc:dd:ee:ff/telemetry
Payload: {
  "gateway_mac": "aa:bb:cc:dd:ee:ff",
  "timestamp": "2026-02-18T10:30:00+00:00",
  "leituras": [
    {
      "dispositivo_codigo": "D01",
      "valor": 123.45,
      "unidade": "kWh"
    },
    ...
  ]
}
==================================================

🔗 Conectando ao broker...
✅ Conectado!

📤 Publicando mensagem...
✅ Mensagem publicada (mid=1)
✅ Mensagem enviada com sucesso!

💡 Verifique o consumer Django para confirmar recebimento

👋 Desconectado
```

**Saída esperada (Terminal 1 - Consumer):**
```
📨 Mensagem recebida: tds_new/devices/aa:bb:cc:dd:ee:ff/telemetry (342 bytes)
🔍 MAC extraído do topic: aa:bb:cc:dd:ee:ff
✅ Gateway encontrado: GTW001 (conta=Empresa Teste)
📦 Payload JSON: {...}
✅ Telemetria processada com sucesso:
   - Leituras criadas: 3
   - Timestamp: 2026-02-18 10:30:00+00:00
   - Gateway: GTW001
   - Conta: Empresa Teste
```

### 4. Validar Persistência no Banco

```bash
# Terminal 3: Verificar dados no TimescaleDB
docker exec -i tsdb_c psql -U postgres -d db_tds_new -c "
  SELECT 
    time, 
    dispositivo_id, 
    valor, 
    unidade 
  FROM tds_new_leitura_dispositivo 
  ORDER BY time DESC 
  LIMIT 5;
"
```

**Saída esperada:**
```
           time            | dispositivo_id | valor  | unidade 
---------------------------+----------------+--------+---------
 2026-02-18 10:30:00+00:00 |             12 | 123.45 | kWh
 2026-02-18 10:30:00+00:00 |             13 |  67.89 | m³
 2026-02-18 10:30:00+00:00 |             14 |  22.50 | °C
(3 rows)
```

## ✅ Critérios de Sucesso

- [x] Consumer conecta ao broker sem erros
- [x] Subscribe confirmado no topic correto
- [x] Mensagem recebida e parseada
- [x] Gateway encontrado pelo MAC
- [x] Dispositivos validados
- [x] 3 leituras criadas no banco
- [x] Gateway atualizado (last_seen, is_online)
- [x] Logs detalhados exibidos

## 🐛 Troubleshooting

### Erro: "Connection refused"

**Causa:** Mosquitto não está rodando

**Solução:**
```bash
# Iniciar Mosquitto (Docker)
docker start mosquitto_c

# OU (Linux local)
sudo systemctl start mosquitto
```

### Erro: "Gateway não encontrado"

**Causa:** Gateway não cadastrado no banco

**Solução:**
```python
# Django shell
python manage.py shell

from tds_new.models import Gateway, Conta
conta = Conta.objects.first()
gateway = Gateway.objects.create(
    conta=conta,
    codigo="GTW001",
    mac="aa:bb:cc:dd:ee:ff",
    nome="Gateway de Teste",
    is_online=False
)
```

### Erro: "Dispositivo não encontrado"

**Causa:** Dispositivos D01, D02, D03 não cadastrados

**Solução:**
```python
# Django shell
from tds_new.models import Dispositivo, Gateway

gateway = Gateway.objects.get(mac="aa:bb:cc:dd:ee:ff")

for codigo in ["D01", "D02", "D03"]:
    Dispositivo.objects.get_or_create(
        gateway=gateway,
        codigo=codigo,
        defaults={
            'nome': f'Dispositivo {codigo}',
            'tipo': 'SENSOR'
        }
    )
```

## 📊 Métricas de Performance

**Latência esperada (end-to-end):**
- Gateway → MQTT → Consumer → DB: **< 500ms**

**Throughput:**
- Mensagens/segundo: **100-500** (ambiente de desenvolvimento)
- Leituras/segundo: **300-1500** (3 leituras por mensagem)

## 🔍 Logs Detalhados

Para habilitar logs completos do Paho MQTT:

```python
# tds_new/consumers/mqtt_telemetry.py
import logging
logging.getLogger('mqtt_consumer').setLevel(logging.DEBUG)
```

Ou via CLI:

```bash
python manage.py start_mqtt_consumer --debug
```

## 📁 Estrutura de Arquivos

```
tds_new/
├── consumers/
│   ├── __init__.py
│   ├── mqtt_config.py          # ✅ Configurações MQTT
│   └── mqtt_telemetry.py       # ✅ Cliente MQTT + callbacks
├── services/
│   ├── __init__.py
│   └── telemetry_processor.py  # ✅ Business logic
└── management/
    └── commands/
        └── start_mqtt_consumer.py  # ✅ Django command

tests/
└── simuladores/
    └── mqtt_simulator.py       # ✅ Simulador de teste
```

## ⏭️ Próximos Passos

- **Fase 3 (Opcional):** Celery Worker para processamento assíncrono
- **Fase 4:** Dashboard com Chart.js para visualização
- **Fase 5 (Opcional):** mTLS (Certificados X.509)
- **Fase 6 (Opcional):** Testes E2E automatizados
