# 🏗️ Arquitetura de Pastas - Projeto IoT TDS New

**Projeto:** TDS New - Sistema de Telemetria e Monitoramento IoT  
**Data:** 18/02/2026  
**Versão:** 1.0

---

## 📋 ANÁLISE DA ESTRUTURA ATUAL

### Situação Encontrada

```
f:/projects/
│
├── server-app/
│   └── server-app-tds-new/         ✅ Backend Django (85% implementado)
│
├── firmware/                        ✅ Firmware ESP32 (PlatformIO)
│
└── server-iot/                      ⚠️  Projeto IoT genérico (pode ser aproveitado)
    ├── infrastructure/
    │   ├── databases/
    │   ├── messaging/
    │   └── scripts/
    └── docs/
```

### Problemas Identificados

1. ❌ **Dispersão de Infraestrutura**: Docker configs podem estar duplicados entre projetos
2. ❌ **Scripts Desorganizados**: Scripts de deploy/setup espalhados
3. ❌ **Consumers no Backend**: Correto, mas falta estrutura de execução
4. ❌ **Falta de Centralização**: Configs de MQTT, PostgreSQL, Redis dispersos

---

## 🎯 PROPOSTA DE ESTRUTURA IDEAL

### Princípios Adotados

1. **Separation of Concerns**: Backend, Firmware, Infraestrutura separados
2. **Infrastructure as Code**: Tudo versionado e reproduzível
3. **Single Source of Truth**: Configs centralizadas por ambiente
4. **Monorepo para Infra**: Facilita deploy e manutenção
5. **Multi-repo para Apps**: Backend e Firmware independentes

---

## 🌲 ESTRUTURA COMPLETA PROPOSTA

```
f:/projects/
│
├── 📁 server-app/                           ✅ BACKEND (Multi-tenant SaaS)
│   └── server-app-tds-new/
│       ├── manage.py
│       ├── requirements.txt
│       ├── README.md
│       ├── CHANGELOG.md
│       │
│       ├── prj_tds_new/                     ⚙️  Configuração Django
│       │   ├── settings.py
│       │   ├── celery.py                    🆕 CRIAR (Fase 3)
│       │   ├── urls.py
│       │   ├── wsgi.py
│       │   └── asgi.py
│       │
│       ├── tds_new/                         🐍 App Principal
│       │   ├── models/                      ✅ Implementado
│       │   ├── views/                       ✅ Implementado
│       │   ├── forms/                       ✅ Implementado
│       │   ├── templates/                   ✅ Implementado
│       │   ├── static/                      🆕 CRIAR (Fase 4)
│       │   ├── consumers/                   🆕 CRIAR (Fase 2) - MQTT Consumers
│       │   ├── services/                    🆕 CRIAR (Fase 2) - Business Logic
│       │   ├── tasks/                       🆕 CRIAR (Fase 3) - Celery Tasks
│       │   └── management/commands/         🆕 CRIAR (Fase 2) - Django Commands
│       │
│       ├── scripts/                         🆕 CRIAR - Scripts específicos do backend
│       │   ├── setup_timescaledb.sql        🆕 CRIAR (Fase 1)
│       │   ├── create_*.sql                 🆕 CRIAR (Fase 1)
│       │   ├── certificados/                🆕 CRIAR (Fase 5) - Gestão X.509
│       │   │   ├── gerar_ca.py
│       │   │   ├── gerar_certificado_broker.py
│       │   │   ├── gerar_certificado_client.py
│       │   │   └── gerar_certificado_lote.py
│       │   └── testes/                      🆕 CRIAR (Fase 6)
│       │       ├── run_e2e_tests.ps1
│       │       ├── run_e2e_tests.sh
│       │       └── setup_test_data.py
│       │
│       ├── tests/                           🆕 CRIAR - Testes automatizados
│       │   ├── unit/                        🆕 Testes unitários
│       │   ├── integration/                 🆕 Testes E2E (Fase 6)
│       │   ├── simuladores/                 🆕 Simuladores de gateway (Fase 6)
│       │   ├── fixtures/                    🆕 Dados de teste
│       │   └── performance/                 🆕 Load tests
│       │
│       ├── certs/                           🆕 CRIAR (Fase 5) - Certificados X.509
│       │   ├── ca.crt                       🔒 Certificado CA
│       │   ├── broker-*.pem                 🔒 Mosquitto
│       │   ├── django-consumer-*.pem        🔒 Django Consumer
│       │   ├── devices/                     🔒 Certificados de dispositivos
│       │   └── README.md
│       │
│       ├── docs/                            ✅ Documentação
│       │   ├── README.md                    ✅ (275 linhas)
│       │   ├── ROADMAP.md                   ✅ (603 linhas)
│       │   ├── DIAGRAMA_ER.md               ✅ (550 linhas)
│       │   ├── PROVISIONAMENTO_IOT.md       ✅ (1.508 linhas)
│       │   ├── VIABILIDADE_TELEMETRIA.md    ✅ (1.200 linhas)
│       │   ├── ESTRUTURA_PASTAS_TELEMETRIA.md ✅ (1.400 linhas)
│       │   └── architecture/
│       │       ├── DECISOES.md              ✅ (465 linhas - 4 ADRs)
│       │       └── INTEGRACAO.md            ✅ (1.000+ linhas)
│       │
│       ├── environments/                    ✅ Variáveis de ambiente
│       │   ├── .env.dev                     ✅
│       │   ├── .env.prod                    ✅
│       │   └── README.md
│       │
│       └── logs/                            📊 Logs da aplicação
│           ├── django.log
│           ├── celery.log                   🆕 (Fase 3)
│           └── mqtt_consumer.log            🆕 (Fase 2)
│
├── 📁 firmware/                             ✅ FIRMWARE ESP32 (PlatformIO)
│   ├── common/                              ✅ Componentes compartilhados
│   │   ├── components/
│   │   ├── config/
│   │   └── libraries/
│   │
│   ├── devices/                             ✅ Projetos por dispositivo
│   │   ├── dcu-0080/                        ✅ Concentrador água/gás
│   │   ├── dcu-1800/                        ✅ Concentrador energia
│   │   ├── dcu-6100-lan/                    ✅ Concentrador ethernet
│   │   └── dcu-8210/                        ✅ Meter reader
│   │
│   ├── tests/                               ✅ Testes de firmware
│   │   ├── integration/
│   │   └── unit/
│   │
│   ├── tools/                               ✅ Ferramentas de build
│   │   └── auto_clean_common.ps1
│   │
│   └── docs/                                ✅ Documentação firmware
│       ├── I2C_ARCHITECTURE.md
│       ├── MIGRATION_NOTES.md
│       └── WORKSPACE_GUIDE.md
│
├── 📁 infrastructure/                       🆕 CRIAR - Infraestrutura Centralizada
│   │
│   ├── 📁 docker/                           🆕 Docker Compose Stacks
│   │   │
│   │   ├── 📁 development/                  🆕 Ambiente DEV
│   │   │   ├── compose.yml                  🆕 Stack completo (PostgreSQL + Redis + Mosquitto)
│   │   │   ├── .env.example                 🆕 Template de variáveis
│   │   │   └── README.md                    🆕 Instruções de uso
│   │   │
│   │   ├── 📁 production/                   🆕 Ambiente PROD
│   │   │   ├── compose.yml                  🆕 Stack otimizado
│   │   │   ├── .env.example                 🆕
│   │   │   └── README.md                    🆕
│   │   │
│   │   ├── 📁 postgres/                     🆕 PostgreSQL + TimescaleDB
│   │   │   ├── Dockerfile                   🆕 Custom image com TimescaleDB
│   │   │   ├── postgresql.conf              🆕 Otimizações para IoT
│   │   │   ├── pg_hba.conf                  🆕 Autenticação
│   │   │   ├── init-timescaledb.sh          🆕 Script de inicialização
│   │   │   └── backup/                      🆕 Scripts de backup
│   │   │       ├── backup_postgres.sh
│   │   │       └── restore_postgres.sh
│   │   │
│   │   ├── 📁 redis/                        🆕 Redis (Cache + Celery Broker)
│   │   │   ├── Dockerfile                   🆕 Custom image
│   │   │   ├── redis.conf                   🆕 Config otimizada
│   │   │   └── README.md                    🆕
│   │   │
│   │   ├── 📁 mosquitto/                    🆕 MQTT Broker (Mosquitto)
│   │   │   ├── Dockerfile                   🆕 Mosquitto + plugins
│   │   │   ├── mosquitto.conf               🆕 Config mTLS (Fase 5)
│   │   │   ├── acl.conf                     🆕 Access Control List
│   │   │   ├── password.txt                 🆕 Usuários/senhas (dev)
│   │   │   ├── certs/                       🔒 Certificados broker
│   │   │   │   ├── ca.crt                   🔒 CA compartilhado
│   │   │   │   ├── broker-cert.pem          🔒
│   │   │   │   └── broker-key.pem           🔒
│   │   │   └── scripts/
│   │   │       ├── start_mosquitto.sh       🆕
│   │   │       └── test_connection.sh       🆕 Testa conexão MQTT
│   │   │
│   │   ├── 📁 nginx/                        🆕 Reverse Proxy (produção)
│   │   │   ├── Dockerfile                   🆕 Nginx otimizado
│   │   │   ├── nginx.conf                   🆕 Config principal
│   │   │   ├── sites-available/
│   │   │   │   └── tds-new.conf             🆕 Virtual host
│   │   │   ├── ssl/                         🔒 Certificados SSL
│   │   │   └── README.md                    🆕
│   │   │
│   │   └── 📁 monitoring/                   🆕 Monitoramento (opcional)
│   │       ├── prometheus/
│   │       │   ├── prometheus.yml
│   │       │   └── alerts.yml
│   │       └── grafana/
│   │           ├── dashboards/
│   │           └── datasources.yml
│   │
│   ├── 📁 scripts/                          🆕 Scripts de Deploy e Manutenção
│   │   │
│   │   ├── 📁 deploy/                       🆕 Scripts de deploy
│   │   │   ├── deploy_dev.sh                🆕 Deploy desenvolvimento
│   │   │   ├── deploy_dev.ps1               🆕 Windows
│   │   │   ├── deploy_prod.sh               🆕 Deploy produção (Ubuntu)
│   │   │   └── rollback.sh                  🆕 Rollback em caso de erro
│   │   │
│   │   ├── 📁 setup/                        🆕 Setup inicial
│   │   │   ├── setup_docker.sh              🆕 Instala Docker + Compose
│   │   │   ├── setup_postgres.sh            🆕 Config PostgreSQL standalone
│   │   │   ├── setup_mosquitto.sh           🆕 Config Mosquitto standalone
│   │   │   ├── setup_redis.sh               🆕 Config Redis standalone
│   │   │   ├── setup_nginx.sh               🆕 Config Nginx standalone
│   │   │   └── setup_all.sh                 🆕 Setup completo (orquestrador)
│   │   │
│   │   ├── 📁 backup/                       🆕 Backup e restore
│   │   │   ├── backup_full.sh               🆕 Backup completo (DB + files)
│   │   │   ├── backup_postgres.sh           🆕 Backup PostgreSQL
│   │   │   ├── backup_redis.sh              🆕 Backup Redis
│   │   │   ├── restore_full.sh              🆕 Restore completo
│   │   │   └── cron_backup.sh               🆕 Configurar cron de backup
│   │   │
│   │   ├── 📁 maintenance/                  🆕 Manutenção
│   │   │   ├── update_ssl_certs.sh          🆕 Renovar SSL (Let's Encrypt)
│   │   │   ├── clean_logs.sh                🆕 Limpar logs antigos
│   │   │   ├── vacuum_postgres.sh           🆕 Vacuum PostgreSQL
│   │   │   └── restart_services.sh          🆕 Restart seguro de serviços
│   │   │
│   │   └── 📁 monitoring/                   🆕 Scripts de monitoramento
│   │       ├── check_services.sh            🆕 Verifica status de serviços
│   │       ├── check_disk_space.sh          🆕 Monitora espaço em disco
│   │       ├── check_mqtt_broker.sh         🆕 Verifica broker MQTT
│   │       └── send_alerts.sh               🆕 Envia alertas (email/Telegram)
│   │
│   ├── 📁 systemd/                          🆕 Systemd Services (Linux Prod)
│   │   ├── tds-new-django.service           🆕 Gunicorn service
│   │   ├── tds-new-celery-worker.service    🆕 Celery worker
│   │   ├── tds-new-celery-beat.service      🆕 Celery scheduler
│   │   ├── tds-new-mqtt-consumer.service    🆕 MQTT Consumer daemon
│   │   ├── mosquitto.service                🆕 Mosquitto override
│   │   └── README.md                        🆕 Instruções systemd
│   │
│   ├── 📁 ansible/                          🆕 Ansible Playbooks (futuro)
│   │   ├── inventory/
│   │   │   ├── dev.yml
│   │   │   └── prod.yml
│   │   ├── playbooks/
│   │   │   ├── deploy.yml
│   │   │   └── setup.yml
│   │   └── README.md
│   │
│   └── 📁 docs/                             🆕 Documentação de infraestrutura
│       ├── DOCKER_SETUP.md                  🆕 Como usar Docker
│       ├── DEPLOYMENT_GUIDE.md              🆕 Guia de deploy
│       ├── SYSTEMD_SERVICES.md              🆕 Configurar systemd
│       ├── MOSQUITTO_SETUP.md               🆕 Configurar MQTT broker
│       ├── NGINX_CONFIGURATION.md           🆕 Configurar Nginx
│       └── TROUBLESHOOTING.md               🆕 Solução de problemas comuns
│
├── 📁 tools/                                🆕 CRIAR - Ferramentas compartilhadas
│   ├── 📁 ota/                              🆕 OTA Updates (futuro)
│   │   ├── flash_firmware.py
│   │   ├── generate_ota_package.py
│   │   └── README.md
│   │
│   ├── 📁 provisioning/                     🆕 Provisionamento em lote
│   │   ├── provision_gateways.py            🆕 Provisiona N gateways
│   │   ├── generate_certs_batch.py          🆕 Gera certificados em lote
│   │   └── templates/
│   │       └── gateway_config.json          🆕 Template de config
│   │
│   └── 📁 cli/                              🆕 CLI Tools
│       ├── tds-cli.py                       🆕 CLI principal
│       ├── commands/
│       │   ├── device.py                    🆕 Comandos de dispositivos
│       │   ├── telemetry.py                 🆕 Comandos de telemetria
│       │   └── deploy.py                    🆕 Comandos de deploy
│       └── README.md
│
└── 📁 docs-global/                          🆕 CRIAR - Documentação do ecossistema
    ├── README.md                            🆕 Overview do projeto completo
    ├── ARCHITECTURE.md                      🆕 Arquitetura global
    ├── GETTING_STARTED.md                   🆕 Quick start para devs
    ├── CONTRIBUTING.md                      🆕 Guia de contribuição
    └── diagrams/                            🆕 Diagramas do sistema
        ├── architecture.drawio
        ├── data-flow.png
        └── deployment.png
```

---

## 📊 MAPEAMENTO DE COMPONENTES POR PASTA

### 1️⃣ Backend Django (`/server-app/server-app-tds-new`)

| Componente | Localização | Status | Fase |
|------------|-------------|--------|------|
| Models (Gateway, Dispositivo) | `tds_new/models/` | ✅ Implementado | - |
| Views CRUD | `tds_new/views/` | ✅ Implementado | - |
| Forms | `tds_new/forms/` | ✅ Implementado | - |
| Templates Bootstrap | `tds_new/templates/` | ✅ Implementado | - |
| **MQTT Consumer** | `tds_new/consumers/` | 🆕 Criar | Fase 2 |
| **Telemetry Service** | `tds_new/services/` | 🆕 Criar | Fase 2 |
| **Celery Tasks** | `tds_new/tasks/` | 🆕 Criar | Fase 3 |
| **Django Commands** | `tds_new/management/commands/` | 🆕 Criar | Fase 2 |
| **Static Files** | `tds_new/static/tds_new/` | 🆕 Criar | Fase 4 |
| **Certificados X.509** | `certs/` | 🆕 Criar | Fase 5 |
| **Scripts SQL** | `scripts/` | 🆕 Criar | Fase 1 |
| **Testes E2E** | `tests/integration/` | 🆕 Criar | Fase 6 |

**Responsabilidade:** Lógica de negócio, API REST, dashboard, processamento de telemetria

---

### 2️⃣ Firmware ESP32 (`/firmware`)

| Componente | Localização | Status |
|------------|-------------|--------|
| Bibliotecas Compartilhadas | `common/libraries/` | ✅ Implementado |
| ESP-IDF Components | `common/components/` | ✅ Implementado |
| Projetos por Dispositivo | `devices/dcu-*/` | ✅ Implementado |
| Testes Unitários | `tests/unit/` | ✅ Implementado |
| Build Tools | `tools/` | ✅ Implementado |

**Responsabilidade:** Código embarcado, comunicação MQTT, leitura de sensores, OTA

---

### 3️⃣ Infraestrutura (`/infrastructure`)

#### Docker Compose

| Stack | Localização | Ambiente | Serviços |
|-------|-------------|----------|----------|
| **Dev Stack** | `docker/development/compose.yml` | Desenvolvimento | PostgreSQL + Redis + Mosquitto + Adminer |
| **Prod Stack** | `docker/production/compose.yml` | Produção | PostgreSQL + Redis + Mosquitto + Nginx + Prometheus |
| **Test Stack** | `docker/testing/compose.yml` | CI/CD | PostgreSQL + Redis + Mosquitto (volumes efêmeros) |

#### Scripts de Deploy

| Script | Localização | Plataforma | Função |
|--------|-------------|------------|--------|
| `deploy_dev.sh` | `scripts/deploy/` | Linux/Mac | Deploy ambiente dev |
| `deploy_dev.ps1` | `scripts/deploy/` | Windows | Deploy ambiente dev |
| `deploy_prod.sh` | `scripts/deploy/` | Ubuntu Server | Deploy produção |
| `rollback.sh` | `scripts/deploy/` | Linux | Rollback seguro |

#### Scripts de Setup

| Script | Localização | Função |
|--------|-------------|--------|
| `setup_all.sh` | `scripts/setup/` | Setup completo (orquestrador) |
| `setup_docker.sh` | `scripts/setup/` | Instala Docker + Compose |
| `setup_postgres.sh` | `scripts/setup/` | Config PostgreSQL standalone |
| `setup_mosquitto.sh` | `scripts/setup/` | Config Mosquitto standalone |
| `setup_redis.sh` | `scripts/setup/` | Config Redis standalone |
| `setup_nginx.sh` | `scripts/setup/` | Config Nginx standalone |

#### Systemd Services (Produção Linux)

| Service | Arquivo | Função |
|---------|---------|--------|
| Django/Gunicorn | `tds-new-django.service` | Servidor web |
| Celery Worker | `tds-new-celery-worker.service` | Processamento async |
| Celery Beat | `tds-new-celery-beat.service` | Tarefas agendadas |
| MQTT Consumer | `tds-new-mqtt-consumer.service` | Consumer daemon |
| Mosquitto | `mosquitto.service` | MQTT Broker |

**Responsabilidade:** Deploy, configuração, monitoramento, backup

---

### 4️⃣ Ferramentas (`/tools`)

| Ferramenta | Localização | Função |
|------------|-------------|--------|
| **OTA Manager** | `tools/ota/` | Gera e distribui firmware OTA |
| **Gateway Provisioning** | `tools/provisioning/` | Provisiona gateways em lote |
| **TDS CLI** | `tools/cli/` | Interface linha de comando |

**Responsabilidade:** Automação, provisionamento, OTA, CLI

---

## 🔄 FLUXO DE TRABALHO POR AMBIENTE

### Desenvolvimento (Local - Windows/Linux)

```bash
# 1. Iniciar infraestrutura Docker
cd f:/projects/infrastructure/docker/development
docker compose up -d

# 2. Ativar ambiente virtual Python
cd f:/projects/server-app/server-app-tds-new
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux

# 3. Executar migrations
python manage.py migrate

# 4. Iniciar Django development server
python manage.py runserver

# 5. Iniciar MQTT Consumer (terminal separado)
python manage.py start_mqtt_consumer

# 6. Iniciar Celery Worker (terminal separado)
celery -A prj_tds_new worker -l info
```

**Docker Stack (Development):**
- PostgreSQL 17 + TimescaleDB (porta 5442)
- Redis 7.2 (porta 6379)
- Mosquitto MQTT (porta 1883)
- Adminer (porta 8080 - GUI PostgreSQL)

---

### Produção (Ubuntu Server)

```bash
# 1. Clone repositórios
git clone https://github.com/Miltoneo/server-app-tds-new.git /var/www/tds-new
git clone https://github.com/Miltoneo/infrastructure.git /var/infrastructure

# 2. Executar setup completo
cd /var/infrastructure/scripts/setup
sudo chmod +x setup_all.sh
sudo ./setup_all.sh

# 3. Deploy aplicação
cd /var/infrastructure/scripts/deploy
sudo chmod +x deploy_prod.sh
sudo ./deploy_prod.sh

# 4. Verificar serviços
sudo systemctl status tds-new-django
sudo systemctl status tds-new-celery-worker
sudo systemctl status tds-new-mqtt-consumer
sudo systemctl status mosquitto
sudo systemctl status nginx
```

**Serviços Systemd (Production):**
- `tds-new-django.service` → Gunicorn (porta 8000, Unix socket)
- `tds-new-celery-worker.service` → Celery worker
- `tds-new-celery-beat.service` → Celery scheduler
- `tds-new-mqtt-consumer.service` → MQTT Consumer daemon
- `mosquitto.service` → MQTT Broker (porta 8883 mTLS)
- `nginx.service` → Reverse proxy (porta 443 HTTPS)

---

## 📁 ONDE FICA O QUE?

### MQTT Consumer

**Localização:** `/server-app/server-app-tds-new/tds_new/consumers/`

**Arquivos:**
- `mqtt_telemetry.py` - Cliente Paho-MQTT (250 linhas)
- `mqtt_config.py` - Configurações MQTT (80 linhas)

**Execução:**
- **Dev:** `python manage.py start_mqtt_consumer`
- **Prod:** `systemctl start tds-new-mqtt-consumer`

**Por que aqui?**
- ✅ Próximo aos models e services (baixo acoplamento)
- ✅ Fácil acesso ao Django ORM
- ✅ Pode usar middlewares e context processors
- ✅ Logs integrados com Django

---

### Scripts SQL (TimescaleDB)

**Localização:** `/server-app/server-app-tds-new/scripts/`

**Arquivos:**
- `setup_timescaledb.sql` - Script principal (150 linhas)
- `create_hypertable.sql` - CREATE HYPERTABLE (50 linhas)
- `create_indexes.sql` - Indexes otimizados (40 linhas)
- `create_continuous_aggregate.sql` - Materialized views (80 linhas)

**Execução:**
```bash
psql -U tsdb_django_d4j7g9 -d db_tds_new -p 5442 -f scripts/setup_timescaledb.sql
```

**Por que aqui?**
- ✅ Próximo ao projeto Django (migrations)
- ✅ Versionado junto com código do backend
- ✅ Fácil referência na documentação

---

### Docker Compose MQTT

**Localização:** `/infrastructure/docker/development/compose.yml`

**Conteúdo:**
```yaml
services:
  mosquitto:
    image: eclipse-mosquitto:2.0
    container_name: tds-new-mosquitto-dev
    ports:
      - "1883:1883"  # MQTT
      - "9001:9001"  # WebSocket
    volumes:
      - ./mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf
      - ./mosquitto/password.txt:/mosquitto/config/password.txt
      - mosquitto-data:/mosquitto/data
      - mosquitto-logs:/mosquitto/log
    restart: unless-stopped
```

**Execução:**
```bash
cd /infrastructure/docker/development
docker compose up -d mosquitto
```

**Por que aqui?**
- ✅ Separado do backend (infraestrutura compartilhada)
- ✅ Pode ser usado por múltiplos backends
- ✅ Fácil de substituir por serviço gerenciado (AWS IoT Core, Azure IoT Hub)

---

### Docker Compose PostgreSQL

**Localização:** `/infrastructure/docker/development/compose.yml`

**Conteúdo:**
```yaml
services:
  postgres:
    image: timescale/timescaledb:2.17.2-pg17
    container_name: tds-new-postgres-dev
    environment:
      POSTGRES_DB: db_tds_new
      POSTGRES_USER: tsdb_django_d4j7g9
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_INITDB_ARGS: "-E UTF8"
    ports:
      - "5442:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./postgres/postgresql.conf:/etc/postgresql/postgresql.conf
      - ./postgres/init-timescaledb.sh:/docker-entrypoint-initdb.d/init.sh
    restart: unless-stopped
```

**Execução:**
```bash
cd /infrastructure/docker/development
docker compose up -d postgres
```

**Por que aqui?**
- ✅ Infraestrutura compartilhada
- ✅ Fácil backup/restore (volumes Docker)
- ✅ Config otimizada para IoT (postgresql.conf customizado)

---

### Certificados X.509 (mTLS)

**Localização:** `/server-app/server-app-tds-new/certs/`

**Estrutura:**
```
certs/
├── ca.crt                  🔒 Certificado CA (compartilhado)
├── ca-key.pem              🔒 Chave privada CA (NÃO commitar)
├── broker-cert.pem         🔒 Cert Mosquitto
├── broker-key.pem          🔒 Key Mosquitto
├── django-consumer-cert.pem 🔒 Cert Django Consumer
├── django-consumer-key.pem  🔒 Key Django Consumer
├── devices/                🔒 Certificados de dispositivos
│   ├── aa-bb-cc-dd-ee-ff.zip
│   └── 11-22-33-44-55-66.zip
└── README.md
```

**Scripts de Gestão:** `/server-app/server-app-tds-new/scripts/certificados/`

**Por que aqui?**
- ✅ Usado pelo Django Consumer (autenticação MQTT)
- ✅ Próximo aos management commands de geração
- ✅ `.gitignore` protege chaves privadas

**Atenção:** Certificados do broker também ficam em `/infrastructure/docker/mosquitto/certs/` (cópia)

---

### Testes E2E

**Localização:** `/server-app/server-app-tds-new/tests/integration/`

**Arquivos:**
- `test_e2e_telemetria.py` - Teste completo (300 linhas)
- `test_mqtt_to_database.py` - MQTT → DB (200 linhas)
- `test_dashboard_realtime.py` - Dashboard (150 linhas)

**Simuladores:** `/server-app/server-app-tds-new/tests/simuladores/`
- `simulador_gateway.py` - Simula gateway enviando telemetria
- `simulador_carga.py` - Load test (100+ gateways)

**Por que aqui?**
- ✅ Testes do backend ficam no backend
- ✅ Acesso direto a models e views
- ✅ Integração com pytest/Django TestCase

---

## 🎯 DECISÕES DE ARQUITETURA

### 1. Por que Consumers dentro do Backend?

**Decisão:** `tds_new/consumers/` em vez de pasta separada

**Motivo:**
- ✅ Acesso direto ao Django ORM (models)
- ✅ Usa context processors e middlewares
- ✅ Logs integrados com Django
- ✅ Pode importar services e tasks facilmente
- ✅ Padrão Django Channels (mesmo para MQTT)

**Alternativa Rejeitada:** `/infrastructure/mqtt-consumer/` (serviço separado)
- ❌ Requer comunicação via API REST (latência)
- ❌ Duplicação de lógica de negócio
- ❌ Mais complexo de deployar e debugar

---

### 2. Por que Scripts SQL no Backend?

**Decisão:** `/server-app/server-app-tds-new/scripts/` em vez de `/infrastructure/`

**Motivo:**
- ✅ Versionado junto com models (migrations)
- ✅ Fácil referência na documentação do projeto
- ✅ Executado após migrations Django
- ✅ Desenvolvedor backend tem contexto completo

**Alternativa Rejeitada:** `/infrastructure/docker/postgres/init-scripts/`
- ❌ Separado do contexto do projeto Django
- ❌ Dificulta rastreamento de mudanças
- ❌ Requer sincronização manual entre repos

---

### 3. Por que Docker Compose em Infraestrutura Separada?

**Decisão:** `/infrastructure/docker/` em vez de `/server-app/server-app-tds-new/docker/`

**Motivo:**
- ✅ Reutilizável por múltiplos backends (TDS, Construtora, etc.)
- ✅ Facilita deploy de serviços standalone (sem backend)
- ✅ Separação de concerns (infra ≠ app)
- ✅ CI/CD independente (infra muda menos que app)

**Alternativa Rejeitada:** Docker no backend
- ❌ Duplicação entre projetos
- ❌ Dificulta deploy híbrido (Docker + Systemd)
- ❌ Mistura responsabilidades (app + infra)

---

### 4. Por que Systemd Services em Infraestrutura?

**Decisão:** `/infrastructure/systemd/` com service files

**Motivo:**
- ✅ Produção Linux usa systemd (não Docker)
- ✅ Melhor controle de recursos (cgroups, limits)
- ✅ Logs integrados com journald
- ✅ Auto-restart e dependências entre serviços
- ✅ Padrão Ubuntu Server

**Produção Stack:**
- PostgreSQL: Instalado via APT (não Docker)
- Redis: Instalado via APT (não Docker)
- Mosquitto: Instalado via APT (não Docker)
- Django: Gunicorn via systemd
- MQTT Consumer: Django command via systemd
- Celery: Worker + Beat via systemd

**Por que não Docker em produção?**
- ❌ Overhead de container (IoT precisa performance)
- ❌ Complexidade de networking (mTLS, WebSocket)
- ❌ Dificuldade de monitoring nativo (journald, Prometheus)
- ✅ Systemd é padrão Ubuntu, robusto, bem documentado

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### ✅ Fase 0: Reorganização (HOJE - 1 hora)

```bash
# 1. Criar estrutura de infraestrutura
mkdir -p /infrastructure/docker/development
mkdir -p /infrastructure/docker/production
mkdir -p /infrastructure/docker/postgres
mkdir -p /infrastructure/docker/redis
mkdir -p /infrastructure/docker/mosquitto
mkdir -p /infrastructure/docker/nginx
mkdir -p /infrastructure/scripts/deploy
mkdir -p /infrastructure/scripts/setup
mkdir -p /infrastructure/scripts/backup
mkdir -p /infrastructure/systemd
mkdir -p /infrastructure/docs

# 2. Mover Docker Compose existente (se houver)
# Verificar se existe docker-compose.yml em server-app-tds-new
# Se sim, mover para /infrastructure/docker/development/compose.yml

# 3. Criar .gitignore em /infrastructure
echo "*.env" > /infrastructure/.gitignore
echo "*.env.local" >> /infrastructure/.gitignore
echo "*.log" >> /infrastructure/.gitignore
echo "certs/*.pem" >> /infrastructure/.gitignore
echo "certs/*.key" >> /infrastructure/.gitignore

# 4. Criar README.md em /infrastructure
# (conteúdo fornecido abaixo)
```

---

### 🔨 Fase 1: TimescaleDB Hypertable (3-4 horas)

**Localização:** `/server-app/server-app-tds-new/scripts/`

```bash
# Criar scripts SQL
scripts/setup_timescaledb.sql
scripts/create_hypertable.sql
scripts/create_indexes.sql
scripts/create_continuous_aggregate.sql
```

**Executar:**
```bash
psql -U tsdb_django_d4j7g9 -d db_tds_new -p 5442 -f scripts/setup_timescaledb.sql
```

---

### 🔨 Fase 2: MQTT Consumer (6-8 horas)

**Localização:** `/server-app/server-app-tds-new/tds_new/`

```bash
# Criar estrutura
mkdir -p tds_new/consumers
mkdir -p tds_new/services
mkdir -p tds_new/management/commands

# Implementar arquivos
tds_new/consumers/mqtt_telemetry.py        (250 linhas)
tds_new/consumers/mqtt_config.py           (80 linhas)
tds_new/services/telemetry_processor.py    (200 linhas)
tds_new/management/commands/start_mqtt_consumer.py (80 linhas)
```

**Executar:**
```bash
python manage.py start_mqtt_consumer
```

---

### 🔨 Fase 3: Celery + Redis (4-5 horas)

**Localização:** `/server-app/server-app-tds-new/`

```bash
# Criar configuração Celery
prj_tds_new/celery.py                      (80 linhas)

# Criar tasks
mkdir -p tds_new/tasks
tds_new/tasks/mqtt_consumer_task.py        (60 linhas)
```

**Localização Scripts:** `/infrastructure/scripts/`

```bash
# Scripts de execução
infrastructure/scripts/start_celery_worker.ps1
infrastructure/scripts/start_celery_worker.sh
```

**Executar:**
```bash
celery -A prj_tds_new worker -l info
```

---

### 🔨 Fase 4: Dashboard Telemetria (8-10 horas)

**Localização:** `/server-app/server-app-tds-new/tds_new/`

```bash
# Views
tds_new/views/telemetria.py                (250 linhas)
tds_new/views/api_telemetria.py            (100 linhas)

# Templates
mkdir -p tds_new/templates/tds_new/telemetria
tds_new/templates/tds_new/telemetria/dashboard.html (400 linhas)
tds_new/templates/tds_new/telemetria/list_leituras.html (200 linhas)

# Static
mkdir -p tds_new/static/tds_new/css
mkdir -p tds_new/static/tds_new/js
tds_new/static/tds_new/css/telemetria.css  (150 linhas)
tds_new/static/tds_new/js/telemetria.js    (300 linhas)
tds_new/static/tds_new/js/chart-config.js  (200 linhas)
```

---

### 🔨 Fase 5: Mosquitto + mTLS (6-10 horas)

**Localização Certificados:** `/server-app/server-app-tds-new/certs/`

```bash
# Estrutura de certificados
mkdir -p certs/devices
certs/ca.crt
certs/ca-key.pem
certs/broker-cert.pem
certs/broker-key.pem
certs/django-consumer-cert.pem
certs/django-consumer-key.pem
```

**Localização Scripts:** `/server-app/server-app-tds-new/scripts/certificados/`

```bash
# Scripts de gestão de certificados
scripts/certificados/gerar_ca.py           (150 linhas)
scripts/certificados/gerar_certificado_broker.py (120 linhas)
scripts/certificados/gerar_certificado_client.py (130 linhas)
scripts/certificados/gerar_certificado_lote.py (200 linhas)
```

**Localização Docker:** `/infrastructure/docker/mosquitto/`

```bash
# Config Mosquitto
infrastructure/docker/mosquitto/mosquitto.conf (80 linhas)
infrastructure/docker/mosquitto/acl.conf       (50 linhas)
infrastructure/docker/mosquitto/Dockerfile
```

---

### 🔨 Fase 6: Testes E2E (6-8 horas)

**Localização:** `/server-app/server-app-tds-new/tests/`

```bash
# Estrutura de testes
mkdir -p tests/integration
mkdir -p tests/simuladores
mkdir -p tests/fixtures
mkdir -p tests/performance

# Arquivos
tests/integration/test_e2e_telemetria.py    (300 linhas)
tests/simuladores/simulador_gateway.py      (250 linhas)
tests/simuladores/simulador_carga.py        (180 linhas)
tests/performance/test_latency.py           (150 linhas)
```

---

## 🚀 PRÓXIMOS PASSOS IMEDIATOS

### 1. Criar Estrutura de Infraestrutura (HOJE - 30 min)

```powershell
# Windows PowerShell
cd f:/projects

# Criar pasta principal
mkdir infrastructure
cd infrastructure

# Criar subpastas
mkdir docker, scripts, systemd, docs, ansible
mkdir docker\development, docker\production, docker\postgres, docker\redis, docker\mosquitto, docker\nginx
mkdir scripts\deploy, scripts\setup, scripts\backup, scripts\maintenance, scripts\monitoring

# Criar README.md
@"
# Infrastructure - TDS New IoT Platform

Infraestrutura centralizada para deploy e manutenção do TDS New.

## Estrutura

- **docker/**: Docker Compose stacks (dev, prod)
- **scripts/**: Scripts de deploy, setup, backup
- **systemd/**: Systemd service files (produção)
- **docs/**: Documentação de infraestrutura

## Quick Start

### Development
\`\`\`bash
cd docker/development
docker compose up -d
\`\`\`

### Production
\`\`\`bash
cd scripts/setup
sudo ./setup_all.sh
\`\`\`
"@ > README.md
```

---

### 2. Criar Docker Compose Development (HOJE - 1 hora)

**Arquivo:** `/infrastructure/docker/development/compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: timescale/timescaledb:2.17.2-pg17
    container_name: tds-new-postgres-dev
    environment:
      POSTGRES_DB: db_tds_new
      POSTGRES_USER: tsdb_django_d4j7g9
      POSTGRES_PASSWORD: ${DB_PASSWORD:-admin}
      POSTGRES_INITDB_ARGS: "-E UTF8"
    ports:
      - "5442:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ../postgres/postgresql.conf:/etc/postgresql/postgresql.conf:ro
      - ../postgres/init-timescaledb.sh:/docker-entrypoint-initdb.d/init.sh:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tsdb_django_d4j7g9 -d db_tds_new"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7.2-alpine
    container_name: tds-new-redis-dev
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
      - ../redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
    command: redis-server /usr/local/etc/redis/redis.conf
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  mosquitto:
    image: eclipse-mosquitto:2.0
    container_name: tds-new-mosquitto-dev
    ports:
      - "1883:1883"   # MQTT
      - "9001:9001"   # WebSocket
    volumes:
      - ../mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf:ro
      - ../mosquitto/password.txt:/mosquitto/config/password.txt:ro
      - mosquitto-data:/mosquitto/data
      - mosquitto-logs:/mosquitto/log
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "mosquitto_sub", "-t", "$$SYS/#", "-C", "1", "-i", "healthcheck"]
      interval: 10s
      timeout: 5s
      retries: 5

  adminer:
    image: adminer:latest
    container_name: tds-new-adminer-dev
    ports:
      - "8080:8080"
    environment:
      ADMINER_DEFAULT_SERVER: postgres
    restart: unless-stopped
    depends_on:
      - postgres

volumes:
  postgres-data:
  redis-data:
  mosquitto-data:
  mosquitto-logs:
```

**Arquivo:** `/infrastructure/docker/development/.env.example`

```bash
# PostgreSQL
DB_PASSWORD=admin

# Redis
REDIS_PASSWORD=

# Mosquitto
MQTT_PASSWORD=admin
```

---

### 3. Testar Docker Stack (HOJE - 15 min)

```powershell
# Copiar .env.example para .env
cd f:/projects/infrastructure/docker/development
Copy-Item .env.example .env

# Iniciar stack
docker compose up -d

# Verificar status
docker compose ps

# Verificar logs
docker compose logs -f postgres
docker compose logs -f mosquitto

# Testar conexão PostgreSQL
psql -h localhost -p 5442 -U tsdb_django_d4j7g9 -d db_tds_new

# Testar conexão MQTT
mosquitto_sub -h localhost -p 1883 -t "test/#" -v
```

---

## 📚 DOCUMENTAÇÃO A CRIAR

### `/infrastructure/docs/`

1. **DOCKER_SETUP.md** - Como usar Docker Compose
2. **DEPLOYMENT_GUIDE.md** - Guia completo de deploy
3. **SYSTEMD_SERVICES.md** - Configurar systemd
4. **MOSQUITTO_SETUP.md** - Configurar MQTT broker
5. **TROUBLESHOOTING.md** - Solução de problemas

### `/docs-global/`

1. **README.md** - Overview do ecossistema completo
2. **ARCHITECTURE.md** - Arquitetura global
3. **GETTING_STARTED.md** - Quick start para novos devs
4. **CONTRIBUTING.md** - Guia de contribuição

---

## ✅ RESUMO DA ESTRUTURA FINAL

| Componente | Localização | Responsabilidade |
|------------|-------------|------------------|
| **Backend Django** | `/server-app/server-app-tds-new/` | Lógica de negócio, API, dashboard |
| **Firmware ESP32** | `/firmware/` | Código embarcado, MQTT, leitura sensores |
| **Infraestrutura** | `/infrastructure/` | Docker, scripts deploy, systemd |
| **Ferramentas** | `/tools/` | OTA, provisionamento, CLI |
| **Docs Global** | `/docs-global/` | Documentação do ecossistema |

**Total de Pastas Principais:** 5  
**Total de Subpastas:** ~40  
**Total de Arquivos a Criar (Fases 1-6):** ~90 arquivos  
**Linhas de Código/Config:** ~10.000 linhas  

---

**Data de Criação:** 18/02/2026  
**Autor:** Milton (via GitHub Copilot)  
**Versão:** 1.0  
**Status:** ✅ Estrutura definida, pronta para implementação

