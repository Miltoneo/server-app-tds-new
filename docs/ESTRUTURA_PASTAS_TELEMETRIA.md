# 📁 Estrutura de Pastas - Implementação de Telemetria

**Projeto:** TDS New - Sistema de Telemetria e Monitoramento IoT  
**Data:** 18/02/2026  
**Versão:** 1.0

---

## 📋 LEGENDA

```
✅ = Já existe (implementado)
🆕 = Será criado na fase indicada
📝 = Será modificado na fase indicada
⚙️  = Arquivo de configuração
🐍 = Código Python
📊 = SQL/Database
🎨 = Frontend (HTML/CSS/JS)
🧪 = Testes
```

---

## 🌲 ESTRUTURA ATUAL (Antes das Fases)

```
f:/projects/server-app/server-app-tds-new/
│
├── manage.py                           ✅
├── requirements.txt                    ✅ (99 linhas)
├── README.md                           ✅ (580 linhas)
├── CHANGELOG.md                        ✅ (1.393 linhas)
│
├── prj_tds_new/                        ✅
│   ├── __init__.py                     ✅
│   ├── settings.py                     ✅ (350 linhas)
│   ├── urls.py                         ✅
│   ├── wsgi.py                         ✅
│   └── asgi.py                         ✅
│
├── tds_new/                            ✅
│   ├── __init__.py                     ✅
│   ├── apps.py                         ✅
│   ├── constants.py                    ✅
│   ├── middleware.py                   ✅
│   ├── urls.py                         ✅
│   │
│   ├── models/                         ✅
│   │   ├── __init__.py                 ✅
│   │   ├── base.py                     ✅ (377 linhas - CustomUser, Conta)
│   │   ├── dispositivos.py             ✅ (400 linhas - Gateway, Dispositivo)
│   │   ├── telemetria.py               ✅ (150 linhas - LeituraDispositivo)
│   │   └── certificados.py             ✅ (200 linhas - CertificadoDevice)
│   │
│   ├── views/                          ✅
│   │   ├── __init__.py                 ✅
│   │   ├── auth.py                     ✅
│   │   ├── dashboard.py                ✅
│   │   ├── gateway.py                  ✅ (350 linhas - CRUD completo)
│   │   └── dispositivo.py              ✅ (380 linhas - CRUD completo)
│   │
│   ├── forms/                          ✅
│   │   ├── __init__.py                 ✅
│   │   ├── gateway.py                  ✅ (200 linhas)
│   │   └── dispositivo.py              ✅ (250 linhas)
│   │
│   ├── templates/                      ✅
│   │   ├── layouts/
│   │   │   ├── base.html               ✅ (380 linhas)
│   │   │   ├── navbar.html             ✅ (150 linhas)
│   │   │   └── sidebar.html            ✅ (190 linhas)
│   │   ├── auth/
│   │   │   ├── login.html              ✅
│   │   │   └── select_account.html     ✅
│   │   └── tds_new/
│   │       ├── dashboard.html          ✅ (145 linhas - placeholder)
│   │       ├── gateway/
│   │       │   ├── list.html           ✅
│   │       │   ├── form.html           ✅
│   │       │   └── detail.html         ✅
│   │       └── dispositivo/
│   │           ├── list.html           ✅
│   │           └── form.html           ✅
│   │
│   └── migrations/                     ✅
│       ├── 0001_initial.py             ✅
│       └── 0002_consumomensal_...py    ✅
│
├── docs/                               ✅
│   ├── README.md                       ✅ (275 linhas)
│   ├── ROADMAP.md                      ✅ (603 linhas)
│   ├── DIAGRAMA_ER.md                  ✅ (550 linhas)
│   ├── PROVISIONAMENTO_IOT.md          ✅ (1.508 linhas)
│   ├── VIABILIDADE_TELEMETRIA.md       ✅ (1.200 linhas - CRIADO HOJE)
│   └── architecture/
│       ├── DECISOES.md                 ✅ (465 linhas - 4 ADRs)
│       └── INTEGRACAO.md               ✅ (1.000+ linhas - CRIADO HOJE)
│
└── environments/                       ✅
    ├── .env.dev                        ✅
    └── .env.prod                       ✅
```

**Total de Arquivos Existentes:** ~50 arquivos  
**Total de Linhas de Código:** ~8.000 linhas  
**Total de Linhas de Documentação:** ~4.500 linhas

---

## 🔨 FASE 1: TimescaleDB Hypertable (3-4 horas)

### Arquivos a Criar

```diff
f:/projects/server-app/server-app-tds-new/
│
+ ├── scripts/                          🆕 NOVA PASTA
+ │   ├── setup_timescaledb.sql         🆕 📊 (150 linhas)
+ │   ├── create_hypertable.sql         🆕 📊 (50 linhas)
+ │   ├── create_indexes.sql            🆕 📊 (40 linhas)
+ │   └── create_continuous_aggregate.sql 🆕 📊 (80 linhas)
│
+ └── docs/
+     └── SQL_SCRIPTS_README.md         🆕 📝 (100 linhas)
```

### Estrutura da Pasta `scripts/`

```
scripts/
├── setup_timescaledb.sql               🆕 Script principal (all-in-one)
│   ├─ CREATE EXTENSION timescaledb
│   ├─ CREATE HYPERTABLE tds_new_leitura_dispositivo
│   ├─ CREATE INDEXES (conta_id, time, dispositivo_id)
│   ├─ CREATE MATERIALIZED VIEW tds_new_consumo_mensal
│   ├─ CREATE CONTINUOUS AGGREGATE POLICY (refresh 1h)
│   └─ CREATE RETENTION POLICY (2 anos)
│
├── create_hypertable.sql               🆕 Script modular (apenas hypertable)
├── create_indexes.sql                  🆕 Script modular (apenas indexes)
└── create_continuous_aggregate.sql     🆕 Script modular (apenas aggregate)
```

### Comandos de Execução

```bash
# Executar script all-in-one
psql -U tsdb_django_d4j7g9 -d db_tds_new -p 5442 -f scripts/setup_timescaledb.sql

# OU executar modularmente
psql -U tsdb_django_d4j7g9 -d db_tds_new -p 5442 -f scripts/create_hypertable.sql
psql -U tsdb_django_d4j7g9 -d db_tds_new -p 5442 -f scripts/create_indexes.sql
psql -U tsdb_django_d4j7g9 -d db_tds_new -p 5442 -f scripts/create_continuous_aggregate.sql
```

### Resultado Esperado

✅ Hypertable criada: `tds_new_leitura_dispositivo`  
✅ Materialized View criada: `tds_new_consumo_mensal`  
✅ 5 indexes criados  
✅ Policy de refresh ativa (1 hora)  
✅ Policy de retenção ativa (2 anos)

**Arquivos Criados:** 4 arquivos  
**Linhas de Código:** ~320 linhas SQL

---

## 🔨 FASE 2: MQTT Consumer (6-8 horas)

### Arquivos a Criar

```diff
f:/projects/server-app/server-app-tds-new/
│
├── tds_new/
│   │
+   ├── consumers/                      🆕 NOVA PASTA
+   │   ├── __init__.py                 🆕 🐍
+   │   ├── mqtt_telemetry.py           🆕 🐍 (250 linhas)
+   │   └── mqtt_config.py              🆕 🐍 (80 linhas)
│   │
+   ├── services/                       🆕 NOVA PASTA
+   │   ├── __init__.py                 🆕 🐍
+   │   └── telemetry_processor.py      🆕 🐍 (200 linhas)
│   │
+   └── management/                     🆕 NOVA PASTA
+       └── commands/
+           ├── __init__.py             🆕 🐍
+           └── start_mqtt_consumer.py  🆕 🐍 (80 linhas)
│
+ └── tests/                            🆕 NOVA PASTA
+     ├── __init__.py                   🆕 🐍
+     ├── test_mqtt_consumer.py         🆕 🧪 (150 linhas)
+     └── test_telemetry_service.py     🆕 🧪 (120 linhas)
```

### Estrutura Detalhada da Fase 2

```
tds_new/
│
├── consumers/                          🆕 Lógica MQTT
│   ├── __init__.py
│   ├── mqtt_telemetry.py               🆕 Cliente Paho-MQTT
│   │   ├─ create_mqtt_client()
│   │   ├─ on_connect(client, userdata, flags, rc)
│   │   ├─ on_message(client, userdata, msg)
│   │   └─ on_disconnect(client, userdata, rc)
│   │
│   └── mqtt_config.py                  🆕 Configurações MQTT
│       ├─ MQTT_BROKER_HOST = "localhost"
│       ├─ MQTT_BROKER_PORT = 1883
│       ├─ MQTT_TOPIC_PATTERN = "tds_new/devices/+/telemetry"
│       └─ MQTT_QOS = 1
│
├── services/                           🆕 Regras de Negócio
│   ├── __init__.py
│   └── telemetry_processor.py          🆕 Processamento de telemetria
│       ├─ class TelemetryProcessorService:
│       │   ├─ __init__(conta_id, gateway)
│       │   ├─ processar_telemetria(payload)
│       │   └─ _validar_payload(payload)
│       │
│       └─ Lógica:
│           ├─ 1. Validar JSON schema
│           ├─ 2. Extrair timestamp
│           ├─ 3. Loop em leituras[]
│           ├─ 4. Lookup de Dispositivo
│           ├─ 5. Bulk create LeituraDispositivo
│           └─ 6. UPDATE Gateway.last_seen
│
└── management/commands/                🆕 Django Commands
    └── start_mqtt_consumer.py          🆕 Comando de execução
        ├─ class Command(BaseCommand):
        │   └─ handle(*args, **options):
        │       ├─ client = create_mqtt_client()
        │       ├─ client.connect(BROKER, PORT)
        │       └─ client.loop_forever()
        │
        └─ Execução: python manage.py start_mqtt_consumer
```

### Testes Unitários

```
tests/
├── test_mqtt_consumer.py               🆕 Testes do Consumer
│   ├─ test_create_mqtt_client()
│   ├─ test_on_connect_success()
│   ├─ test_on_message_valid_payload()
│   ├─ test_on_message_invalid_json()
│   └─ test_on_message_gateway_not_found()
│
└── test_telemetry_service.py           🆕 Testes do Service
    ├─ test_processar_telemetria_success()
    ├─ test_validar_payload_valid()
    ├─ test_validar_payload_missing_fields()
    ├─ test_bulk_create_leituras()
    └─ test_update_gateway_last_seen()
```

### Comandos de Execução

```bash
# Executar consumer (modo foreground)
python manage.py start_mqtt_consumer

# Executar testes
python manage.py test tests.test_mqtt_consumer
python manage.py test tests.test_telemetry_service
```

**Arquivos Criados:** 9 arquivos  
**Linhas de Código:** ~880 linhas Python

---

## 🔨 FASE 3: Celery + Redis Setup (4-5 horas)

### Arquivos a Criar/Modificar

```diff
f:/projects/server-app/server-app-tds-new/
│
  ├── requirements.txt                  📝 MODIFICAR
+ │   └─ Adicionar: celery==5.3.6
│
+ ├── prj_tds_new/
+ │   ├── celery.py                     🆕 ⚙️ (80 linhas)
+ │   ├── __init__.py                   📝 MODIFICAR (importar celery app)
+ │   └── settings.py                   📝 MODIFICAR (configurar CELERY_*)
│
+ ├── tds_new/
+ │   ├── tasks/                        🆕 NOVA PASTA
+ │   │   ├── __init__.py               🆕 🐍
+ │   │   └── mqtt_consumer_task.py     🆕 🐍 (60 linhas)
+ │   │
+ │   └── management/commands/
+ │       └── start_mqtt_consumer_celery.py 🆕 🐍 (50 linhas)
│
+ └── scripts/
+     ├── start_celery_worker.ps1       🆕 ⚙️ (PowerShell - Windows)
+     └── start_celery_worker.sh        🆕 ⚙️ (Bash - Linux)
```

### Estrutura Detalhada da Fase 3

```
prj_tds_new/
├── celery.py                           🆕 Configuração Celery
│   ├─ app = Celery('tds_new')
│   ├─ app.config_from_object('django.conf:settings', namespace='CELERY')
│   ├─ app.autodiscover_tasks()
│   └─ @app.task debug_task()
│
├── __init__.py                         📝 MODIFICAR
│   └─ Adicionar:
│       from .celery import app as celery_app
│       __all__ = ('celery_app',)
│
└── settings.py                         📝 MODIFICAR
    └─ Adicionar configurações:
        CELERY_BROKER_URL = 'redis://localhost:6379/0'
        CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
        CELERY_ACCEPT_CONTENT = ['json']
        CELERY_TASK_SERIALIZER = 'json'
        CELERY_TIMEZONE = 'America/Sao_Paulo'

tds_new/tasks/
└── mqtt_consumer_task.py               🆕 Task Celery
    ├─ @shared_task
    ├─ def run_mqtt_consumer():
    │   ├─ client = create_mqtt_client()
    │   ├─ client.connect(...)
    │   └─ client.loop_forever()
    │
    └─ Execução: run_mqtt_consumer.delay()

scripts/
├── start_celery_worker.ps1             🆕 Script Windows
│   └─ celery -A prj_tds_new worker -l info
│
└── start_celery_worker.sh              🆕 Script Linux
    └─ celery -A prj_tds_new worker -l info
```

### Comandos de Execução

```bash
# Windows PowerShell
.\scripts\start_celery_worker.ps1

# Linux/Mac
chmod +x scripts/start_celery_worker.sh
./scripts/start_celery_worker.sh

# Manual
celery -A prj_tds_new worker -l info

# Verificar worker ativo
celery -A prj_tds_new inspect ping
```

**Arquivos Criados:** 6 arquivos  
**Arquivos Modificados:** 3 arquivos  
**Linhas de Código:** ~240 linhas Python

---

## 🔨 FASE 4: Dashboard de Telemetria (8-10 horas)

### Arquivos a Criar/Modificar

```diff
f:/projects/server-app/server-app-tds-new/
│
  ├── tds_new/
  │   │
+ │   ├── views/
+ │   │   ├── telemetria.py             🆕 🐍 (250 linhas)
+ │   │   └── api_telemetria.py         🆕 🐍 (100 linhas - AJAX endpoints)
  │   │
+ │   ├── templates/tds_new/
+ │   │   └── telemetria/               🆕 NOVA PASTA
+ │   │       ├── dashboard.html        🆕 🎨 (400 linhas)
+ │   │       ├── list_leituras.html    🆕 🎨 (200 linhas)
+ │   │       └── detail_dispositivo.html 🆕 🎨 (180 linnas)
  │   │
+ │   ├── static/tds_new/               🆕 NOVA PASTA
+ │   │   ├── css/
+ │   │   │   └── telemetria.css        🆕 🎨 (150 linhas)
+ │   │   └── js/
+ │   │       ├── telemetria.js         🆕 🎨 (300 linhas)
+ │   │       └── chart-config.js       🆕 🎨 (200 linhas)
  │   │
  │   └── urls.py                       📝 MODIFICAR (adicionar rotas telemetria)
│
+ └── tests/
+     └── test_telemetria_views.py      🆕 🧪 (150 linhas)
```

### Estrutura Detalhada da Fase 4

```
tds_new/views/
├── telemetria.py                       🆕 Views principais
│   ├─ class TelemetriaView(TemplateView):
│   │   ├─ get_context_data():
│   │   │   ├─ ultimas_leituras (50)
│   │   │   ├─ consumo_mensal (6 meses)
│   │   │   ├─ gateways_online/offline
│   │   │   └─ chart_data (Chart.js format)
│   │   └─ _prepare_chart_data()
│   │
│   ├─ class ListLeiturasView(ListView):
│   │   └─ Paginação (50 itens/página)
│   │
│   └─ class DetailDispositivoTelemetriaView(DetailView):
│       ├─ Últimas 100 leituras do dispositivo
│       └─ Estatísticas (média, min, max)
│
└── api_telemetria.py                   🆕 AJAX endpoints
    ├─ @require_GET
    ├─ def ultimas_leituras_json(request):
    │   └─ JsonResponse (últimas 10 leituras)
    │
    └─ @require_GET
    └─ def gateways_status_json(request):
        └─ JsonResponse (online/offline count)

tds_new/templates/tds_new/telemetria/
├── dashboard.html                      🆕 Dashboard principal
│   ├─ {% extends 'layouts/base_cenario.html' %}
│   ├─ Cards de métricas (3 cards)
│   ├─ Gráfico Chart.js (consumo mensal)
│   ├─ Tabela últimas 50 leituras
│   └─ Auto-refresh (30s via AJAX)
│
├── list_leituras.html                  🆕 Lista completa
│   ├─ Filtros (gateway, dispositivo, data range)
│   ├─ Paginação Bootstrap
│   └─ Export CSV button
│
└── detail_dispositivo.html             🆕 Detalhes por dispositivo
    ├─ Info do dispositivo
    ├─ Gráfico histórico (últimos 7 dias)
    └─ Tabela leituras (últimas 100)

tds_new/static/tds_new/
├── css/telemetria.css                  🆕 Estilos customizados
│   ├─ .card-metric { ... }
│   ├─ .status-online { color: #28a745 }
│   ├─ .status-offline { color: #dc3545 }
│   └─ Responsive design (mobile-first)
│
└── js/
    ├── telemetria.js                   🆕 Lógica principal
    │   ├─ autoRefreshDashboard() - AJAX refresh 30s
    │   ├─ updateTable(data) - Atualiza tabela
    │   ├─ updateMetrics(data) - Atualiza cards
    │   └─ initWebSocket() - (Fase futura)
    │
    └── chart-config.js                 🆕 Configuração Chart.js
        ├─ createLineChart(canvasId, data)
        ├─ createBarChart(canvasId, data)
        ├─ updateChart(chart, newData)
        └─ Color palette definition
```

### URLs Adicionadas

```python
# tds_new/urls.py (modificar)

urlpatterns = [
    # ... URLs existentes ...
    
    # Telemetria
    path('telemetria/', TelemetriaView.as_view(), name='telemetria_dashboard'),
    path('telemetria/leituras/', ListLeiturasView.as_view(), name='telemetria_leituras'),
    path('telemetria/dispositivo/<int:pk>/', DetailDispositivoTelemetriaView.as_view(), name='telemetria_dispositivo'),
    
    # AJAX API
    path('api/telemetria/ultimas/', ultimas_leituras_json, name='api_ultimas_leituras'),
    path('api/telemetria/gateways-status/', gateways_status_json, name='api_gateways_status'),
]
```

### Comandos de Execução

```bash
# Coletar static files
python manage.py collectstatic --noinput

# Testar views
python manage.py test tests.test_telemetria_views

# Acessar dashboard
# http://localhost:8000/telemetria/
```

**Arquivos Criados:** 9 arquivos  
**Arquivos Modificados:** 1 arquivo  
**Linhas de Código:** ~1.930 linhas (Python + HTML + CSS + JS)

---

## 🔨 FASE 5: Mosquitto + mTLS (6-10 horas)

### Arquivos a Criar

```diff
f:/projects/server-app/server-app-tds-new/
│
+ ├── certs/                            🆕 NOVA PASTA (certificados)
+ │   ├── ca-key.pem                    🆕 🔒 (Chave privada CA - NUNCA commitar)
+ │   ├── ca.crt                        🆕 🔒 (Certificado CA público)
+ │   ├── broker-key.pem                🆕 🔒 (Chave privada Mosquitto)
+ │   ├── broker-cert.pem               🆕 🔒 (Certificado Mosquitto)
+ │   ├── django-consumer-key.pem       🆕 🔒 (Chave privada Django)
+ │   ├── django-consumer-cert.pem      🆕 🔒 (Certificado Django)
+ │   └── README.md                     🆕 📝 (Instruções de uso)
│
+ ├── scripts/
+ │   ├── certificados/                 🆕 NOVA PASTA
+ │   │   ├── gerar_ca.py               🆕 🐍 (150 linhas)
+ │   │   ├── gerar_certificado_broker.py 🆕 🐍 (120 linhas)
+ │   │   ├── gerar_certificado_client.py 🆕 🐍 (130 linhas)
+ │   │   ├── gerar_certificado_lote.py 🆕 🐍 (200 linhas)
+ │   │   └── atualizar_crl.py          🆕 🐍 (100 linhas)
+ │   │
+ │   └── mosquitto/                    🆕 NOVA PASTA
+ │       ├── mosquitto.conf            🆕 ⚙️ (80 linhas)
+ │       ├── acl.conf                  🆕 ⚙️ (50 linhas)
+ │       ├── start_mosquitto.ps1       🆕 ⚙️ (PowerShell)
+ │       └── start_mosquitto.sh        🆕 ⚙️ (Bash)
│
+ ├── tds_new/
+ │   └── management/commands/
+ │       ├── gerar_certificado_gateway.py 🆕 🐍 (180 linhas)
+ │       └── revogar_certificado.py    🆕 🐍 (120 linhas)
│
+ └── docs/
+     └── MOSQUITTO_SETUP.md            🆕 📝 (300 linhas)
```

### Estrutura Detalhada da Fase 5

```
certs/                                  🆕 Certificados X.509
├── ca-key.pem                          🆕 Chave privada CA (RSA 2048)
├── ca.crt                              🆕 Certificado CA (10 anos)
├── broker-key.pem                      🆕 Chave Mosquitto
├── broker-cert.pem                     🆕 Cert Mosquitto (CN=mqtt-broker)
├── django-consumer-key.pem             🆕 Chave Django Consumer
├── django-consumer-cert.pem            🆕 Cert Django (CN=django_consumer)
└── README.md                           🆕 Instruções
    ├─ Nunca commitar chaves privadas (.gitignore)
    ├─ Renovação a cada 2 anos (OTA para gateways)
    └─ Backup em local seguro

scripts/certificados/
├── gerar_ca.py                         🆕 Gera CA authority
│   ├─ from cryptography import x509
│   ├─ Gera RSA 2048 key
│   ├─ Subject: CN=TDS-New-CA
│   ├─ Validade: 10 anos
│   └─ Salva: certs/ca-key.pem, certs/ca.crt
│
├── gerar_certificado_broker.py         🆕 Cert Mosquitto
│   ├─ Assina com CA
│   ├─ Subject: CN=mqtt-broker.tds-new.local
│   └─ Salva: certs/broker-*.pem
│
├── gerar_certificado_client.py         🆕 Cert único (manual)
│   ├─ Recebe MAC address como argumento
│   ├─ Subject: CN=aa:bb:cc:dd:ee:ff
│   └─ Salva em CertificadoDevice model + filesystem
│
├── gerar_certificado_lote.py           🆕 Lote (CSV)
│   ├─ Lê CSV com lista de MACs
│   ├─ Loop: gera certificado para cada MAC
│   ├─ Salva em pasta certs/devices/
│   └─ Cria ZIP com todos os certificados
│
└── atualizar_crl.py                    🆕 Certificate Revocation List
    ├─ Query CertificadoDevice.filter(is_revoked=True)
    ├─ Gera crl.pem
    └─ Copia para /etc/mosquitto/certs/

scripts/mosquitto/
├── mosquitto.conf                      🆕 Config Mosquitto
│   ├─ listener 8883 (TLS only)
│   ├─ require_certificate true
│   ├─ use_identity_as_username true
│   ├─ cafile certs/ca.crt
│   ├─ certfile certs/broker-cert.pem
│   ├─ keyfile certs/broker-key.pem
│   ├─ crlfile certs/crl.pem
│   └─ acl_file mosquitto/acl.conf
│
├── acl.conf                            🆕 Access Control List
│   ├─ user #  (negar tudo por padrão)
│   ├─ pattern write tds_new/devices/%u/telemetry
│   └─ user django_consumer (read all)
│
├── start_mosquitto.ps1                 🆕 Script Windows
│   └─ mosquitto -c scripts/mosquitto/mosquitto.conf
│
└── start_mosquitto.sh                  🆕 Script Linux
    └─ mosquitto -c scripts/mosquitto/mosquitto.conf

tds_new/management/commands/
├── gerar_certificado_gateway.py        🆕 Django command
│   ├─ python manage.py gerar_certificado_gateway --mac aa:bb:cc:dd:ee:ff
│   ├─ Cria CertificadoDevice no DB
│   ├─ Gera arquivo ZIP (cert + key + ca.crt)
│   └─ Atualiza CRL automaticamente
│
└── revogar_certificado.py              🆕 Django command
    ├─ python manage.py revogar_certificado --serial 4E3F2A1B...
    ├─ UPDATE CertificadoDevice SET is_revoked=True
    ├─ Atualiza CRL
    └─ Reinicia Mosquitto (reload config)
```

### Comandos de Execução

```bash
# 1. Gerar CA (uma vez, no início)
python scripts/certificados/gerar_ca.py

# 2. Gerar certificados do broker
python scripts/certificados/gerar_certificado_broker.py

# 3. Gerar certificado do Django Consumer
python scripts/certificados/gerar_certificado_client.py --cn django_consumer

# 4. Gerar certificados de gateways (lote)
python scripts/certificados/gerar_certificado_lote.py --csv gateways.csv

# 5. Iniciar Mosquitto
.\scripts\mosquitto\start_mosquitto.ps1  # Windows
./scripts/mosquitto/start_mosquitto.sh   # Linux

# 6. Testar conexão mTLS
mosquitto_sub -h localhost -p 8883 \
  --cafile certs/ca.crt \
  --cert certs/django-consumer-cert.pem \
  --key certs/django-consumer-key.pem \
  -t "tds_new/devices/+/telemetry"
```

### Integração com MQTT Consumer (Fase 2)

```python
# tds_new/consumers/mqtt_telemetry.py (modificar)

def create_mqtt_client():
    client = mqtt.Client(client_id="django_consumer", protocol=mqtt.MQTTv311)
    
    # ✅ ADICIONAR: Configuração mTLS
    client.tls_set(
        ca_certs="certs/ca.crt",
        certfile="certs/django-consumer-cert.pem",
        keyfile="certs/django-consumer-key.pem"
    )
    
    # Callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    
    return client
```

**Arquivos Criados:** 18 arquivos  
**Arquivos Modificados:** 2 arquivos (mqtt_telemetry.py, .gitignore)  
**Linhas de Código:** ~1.230 linhas (Python + Config)

---

## 🔨 FASE 6: Testes de Integração E2E (6-8 horas)

### Arquivos a Criar

```diff
f:/projects/server-app/server-app-tds-new/
│
+ ├── tests/                            (expandir pasta existente)
+ │   │
+ │   ├── integration/                  🆕 NOVA PASTA
+ │   │   ├── __init__.py               🆕 🐍
+ │   │   ├── test_e2e_telemetria.py    🆕 🧪 (300 linhas)
+ │   │   ├── test_mqtt_to_database.py  🆕 🧪 (200 linhas)
+ │   │   └── test_dashboard_realtime.py 🆕 🧪 (150 linhas)
+ │   │
+ │   ├── simuladores/                  🆕 NOVA PASTA
+ │   │   ├── __init__.py               🆕 🐍
+ │   │   ├── simulador_gateway.py      🆕 🐍 (250 linhas)
+ │   │   ├── simulador_carga.py        🆕 🐍 (180 linhas)
+ │   │   └── simulador_payload.py      🆕 🐍 (120 linhas)
+ │   │
+ │   ├── fixtures/                     🆕 NOVA PASTA
+ │   │   ├── gateways.json             🆕 📊 (Dados de teste)
+ │   │   ├── dispositivos.json         🆕 📊
+ │   │   └── leituras_exemplo.json     🆕 📊
+ │   │
+ │   └── performance/                  🆕 NOVA PASTA
+ │       ├── __init__.py               🆕 🐍
+ │       ├── test_latency.py           🆕 🧪 (150 linhas)
+ │       └── test_throughput.py        🆕 🧪 (180 linhas)
│
+ ├── scripts/
+ │   └── testes/                       🆕 NOVA PASTA
+ │       ├── run_e2e_tests.ps1         🆕 ⚙️ (PowerShell)
+ │       ├── run_e2e_tests.sh          🆕 ⚙️ (Bash)
+ │       └── setup_test_data.py        🆕 🐍 (100 linhas)
│
+ └── docs/
+     └── TESTES_E2E.md                 🆕 📝 (250 linhas)
```

### Estrutura Detalhada da Fase 6

```
tests/integration/
├── test_e2e_telemetria.py              🆕 Teste End-to-End completo
│   ├─ class TestE2ETelemetria(TestCase):
│   │   ├─ setUpClass(): Cria gateway, dispositivo, certificado
│   │   ├─ test_fluxo_completo():
│   │   │   ├─ 1. Simulador publica MQTT
│   │   │   ├─ 2. Consumer processa
│   │   │   ├─ 3. Leitura salva no DB
│   │   │   ├─ 4. Gateway.last_seen atualizado
│   │   │   ├─ 5. Dashboard exibe dados
│   │   │   └─ 6. Validar latência < 500ms
│   │   ├─ test_payload_invalido()
│   │   ├─ test_gateway_nao_encontrado()
│   │   └─ tearDownClass()
│   │
│   └─ Validações:
│       ├─ ✅ Mensagem MQTT recebida
│       ├─ ✅ JSON parseado corretamente
│       ├─ ✅ Leitura inserida no hypertable
│       ├─ ✅ Continuous aggregate atualizado
│       └─ ✅ Dashboard renderiza sem erros
│
├── test_mqtt_to_database.py            🆕 Teste MQTT → DB
│   ├─ test_bulk_insert_performance()
│   ├─ test_transacao_atomica()
│   └─ test_erro_nao_quebra_consumer()
│
└── test_dashboard_realtime.py          🆕 Teste Dashboard
    ├─ test_auto_refresh_ajax()
    ├─ test_chart_js_rendering()
    └─ test_pagination_leituras()

tests/simuladores/
├── simulador_gateway.py                🆕 Simulador de Gateway IoT
│   ├─ class GatewaySimulator:
│   │   ├─ __init__(mac_address, broker_host, broker_port)
│   │   ├─ gerar_payload_fake() - Dados aleatórios
│   │   ├─ publicar_telemetria(interval=5) - Loop infinito
│   │   └─ stop() - Parar simulação
│   │
│   └─ Execução:
│       python tests/simuladores/simulador_gateway.py \
│         --mac aa:bb:cc:dd:ee:ff \
│         --broker localhost \
│         --port 1883 \
│         --interval 5
│
├── simulador_carga.py                  🆕 Teste de Carga
│   ├─ class LoadSimulator:
│   │   ├─ simular_n_gateways(n=100) - Múltiplos gateways
│   │   ├─ rate_messages_per_second=10
│   │   └─ Métricas: throughput, latência P50/P95/P99
│   │
│   └─ Execução:
│       python tests/simuladores/simulador_carga.py \
│         --gateways 100 \
│         --rate 10 \
│         --duration 60
│
└── simulador_payload.py                🆕 Gerador de Payloads
    ├─ gerar_payload_agua(valor_min, valor_max)
    ├─ gerar_payload_energia(...)
    ├─ gerar_payload_gas(...)
    └─ gerar_payload_temperatura(...)

tests/fixtures/
├── gateways.json                       🆕 Fixtures Django
│   └─ 5 gateways de teste com MACs válidos
│
├── dispositivos.json                   🆕
│   └─ 20 dispositivos (4 por gateway)
│
└── leituras_exemplo.json               🆕
    └─ 100 leituras de teste (últimas 24h)

tests/performance/
├── test_latency.py                     🆕 Teste de Latência
│   ├─ test_latency_mqtt_to_db() - < 300ms
│   ├─ test_latency_db_to_dashboard() - < 100ms
│   └─ test_latency_end_to_end() - < 500ms
│
└── test_throughput.py                  🆕 Teste de Throughput
    ├─ test_insert_1000_leituras() - Bulk insert
    ├─ test_query_agregacao_mensal() - Query speed
    └─ test_concurrent_consumers() - Paralelismo
```

### Scripts de Execução de Testes

```
scripts/testes/
├── run_e2e_tests.ps1                   🆕 Script Windows
│   ├─ # Iniciar serviços
│   ├─ Start-Service PostgreSQL
│   ├─ Start-Process mosquitto
│   ├─ celery -A prj_tds_new worker -D
│   ├─ python manage.py start_mqtt_consumer &
│   ├─ # Executar testes
│   ├─ python manage.py test tests.integration
│   └─ # Parar serviços
│
├── run_e2e_tests.sh                    🆕 Script Linux
│   └─ (equivalente ao PS1)
│
└── setup_test_data.py                  🆕 Popular banco de testes
    ├─ Carrega fixtures (gateways, dispositivos)
    ├─ Gera certificados fake
    └─ Cria continuous aggregates
```

### Comandos de Execução

```bash
# 1. Setup dados de teste
python scripts/testes/setup_test_data.py

# 2. Executar testes E2E (todos)
python manage.py test tests.integration

# 3. Executar teste específico
python manage.py test tests.integration.test_e2e_telemetria

# 4. Executar simulador de gateway
python tests/simuladores/simulador_gateway.py \
  --mac aa:bb:cc:dd:ee:ff \
  --broker localhost \
  --port 1883

# 5. Teste de carga (100 gateways, 10 msg/s, 60s)
python tests/simuladores/simulador_carga.py \
  --gateways 100 \
  --rate 10 \
  --duration 60

# 6. Executar testes de performance
python manage.py test tests.performance

# 7. Gerar relatório de cobertura
coverage run --source='tds_new' manage.py test
coverage report
coverage html
```

**Arquivos Criados:** 17 arquivos  
**Linhas de Código:** ~1.880 linhas (Python + JSON + Scripts)

---

## 📊 RESUMO FINAL - ESTRUTURA COMPLETA

### Estatísticas Gerais

| Fase | Arquivos Criados | Arquivos Modificados | Linhas de Código | Tempo Estimado |
|------|------------------|----------------------|------------------|----------------|
| **Fase 1** | 4 | 0 | ~320 SQL | 3-4 horas |
| **Fase 2** | 9 | 0 | ~880 Python | 6-8 horas |
| **Fase 3** | 6 | 3 | ~240 Python | 4-5 horas |
| **Fase 4** | 9 | 1 | ~1.930 Python/HTML/JS/CSS | 8-10 horas |
| **Fase 5** | 18 | 2 | ~1.230 Python/Config | 6-10 horas |
| **Fase 6** | 17 | 0 | ~1.880 Python/JSON | 6-8 horas |
| **TOTAL** | **63** | **6** | **~6.480** | **33-45 horas** |

### Estrutura Final Consolidada

```
f:/projects/server-app/server-app-tds-new/
│
├── 📁 RAIZ
│   ├── manage.py                       ✅
│   ├── requirements.txt                ✅ 📝 (+celery)
│   ├── README.md                       ✅
│   └── CHANGELOG.md                    ✅
│
├── 📁 prj_tds_new/                     ✅ Configuração Django
│   ├── __init__.py                     ✅ 📝 (+celery import)
│   ├── settings.py                     ✅ 📝 (+CELERY_*)
│   ├── celery.py                       🆕 FASE 3
│   ├── urls.py                         ✅
│   ├── wsgi.py                         ✅
│   └── asgi.py                         ✅
│
├── 📁 tds_new/                         ✅ App principal
│   ├── models/                         ✅ (4 arquivos)
│   ├── views/                          ✅ (+telemetria.py 🆕)
│   ├── forms/                          ✅ (2 arquivos)
│   ├── consumers/                      🆕 FASE 2 (2 arquivos)
│   ├── services/                       🆕 FASE 2 (1 arquivo)
│   ├── tasks/                          🆕 FASE 3 (1 arquivo)
│   ├── management/commands/            🆕 FASE 2,5 (4 arquivos)
│   ├── templates/                      ✅ (+telemetria/ 🆕)
│   ├── static/tds_new/                 🆕 FASE 4 (3 arquivos)
│   ├── migrations/                     ✅ (2 migrations)
│   └── urls.py                         ✅ 📝 (+telemetria rotas)
│
├── 📁 scripts/                         🆕 FASE 1,3,5,6
│   ├── setup_timescaledb.sql           🆕 FASE 1
│   ├── create_*.sql                    🆕 FASE 1 (3 arquivos)
│   ├── certificados/                   🆕 FASE 5 (5 scripts)
│   ├── mosquitto/                      🆕 FASE 5 (4 arquivos)
│   ├── testes/                         🆕 FASE 6 (3 scripts)
│   ├── start_celery_worker.*           🆕 FASE 3 (2 arquivos)
│   └── start_mosquitto.*               🆕 FASE 5 (2 arquivos)
│
├── 📁 tests/                           🆕 FASE 2,6
│   ├── test_mqtt_consumer.py           🆕 FASE 2
│   ├── test_telemetry_service.py       🆕 FASE 2
│   ├── test_telemetria_views.py        🆕 FASE 4
│   ├── integration/                    🆕 FASE 6 (3 arquivos)
│   ├── simuladores/                    🆕 FASE 6 (3 arquivos)
│   ├── fixtures/                       🆕 FASE 6 (3 arquivos)
│   └── performance/                    🆕 FASE 6 (2 arquivos)
│
├── 📁 certs/                           🆕 FASE 5 (7 certificados)
│   ├── ca.crt                          🆕
│   ├── *.pem                           🆕 (6 arquivos)
│   └── README.md                       🆕
│
├── 📁 docs/                            ✅ Documentação
│   ├── README.md                       ✅
│   ├── ROADMAP.md                      ✅
│   ├── DIAGRAMA_ER.md                  ✅
│   ├── PROVISIONAMENTO_IOT.md          ✅
│   ├── VIABILIDADE_TELEMETRIA.md       ✅
│   ├── SQL_SCRIPTS_README.md           🆕 FASE 1
│   ├── MOSQUITTO_SETUP.md              🆕 FASE 5
│   ├── TESTES_E2E.md                   🆕 FASE 6
│   └── architecture/
│       ├── DECISOES.md                 ✅
│       └── INTEGRACAO.md               ✅
│
└── 📁 environments/                    ✅
    ├── .env.dev                        ✅
    └── .env.prod                       ✅
```

### Total de Arquivos no Projeto

**Antes das Fases:** ~50 arquivos  
**Depois das Fases:** ~113 arquivos  
**Incremento:** +63 arquivos (+126%)

### Total de Linhas de Código

**Existente:** ~8.000 linhas  
**Novo:** ~6.480 linhas  
**Total Final:** ~14.480 linhas Python/SQL/HTML/JS/CSS

**Documentação:**  
**Existente:** ~4.500 linhas  
**Novo:** ~650 linhas  
**Total Final:** ~5.150 linhas Markdown

---

## 🚀 PRÓXIMOS PASSOS

### 1. Iniciar Fase 1 (HOJE - 18/02/2026)

```bash
# Criar estrutura de pastas
mkdir scripts
mkdir scripts/testes
mkdir certs
mkdir tests/integration
mkdir tests/simuladores
mkdir tests/fixtures
mkdir tests/performance

# Criar arquivo SQL (copiar de INTEGRACAO.md)
# Código disponível em docs/architecture/INTEGRACAO.md linhas 500-650

# Executar script TimescaleDB
psql -U tsdb_django_d4j7g9 -d db_tds_new -p 5442 -f scripts/setup_timescaledb.sql
```

**✅ FASE 1 CONCLUÍDA EM 1 HORA**

### 2. Continuar para Fase 2 (AMANHÃ - 19/02/2026)

```bash
# Criar pastas
mkdir tds_new/consumers
mkdir tds_new/services
mkdir tds_new/management/commands

# Implementar arquivos (código em INTEGRACAO.md)
# - tds_new/consumers/mqtt_telemetry.py
# - tds_new/services/telemetry_processor.py
# - tds_new/management/commands/start_mqtt_consumer.py

# Testar consumer
python manage.py start_mqtt_consumer
```

**✅ FASE 2 CONCLUÍDA EM 1 DIA**

---

**Data de Criação:** 18/02/2026  
**Versão:** 1.0  
**Status:** Documentação completa da estrutura de pastas

