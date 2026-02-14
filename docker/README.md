# 🐳 Docker Setup - TDS New

## 📋 Visão Geral

Stack de desenvolvimento completa usando Docker Compose com **paridade total de produção**.

### Serviços Disponíveis:

| Serviço | Imagem | Versão | Porta | Descrição |
|---------|--------|--------|-------|-----------|
| **db** | timescale/timescaledb | 2.17.2-pg17 | 5432 | PostgreSQL 17 + TimescaleDB |
| **redis** | redis | 7.2-alpine | 6379 | Cache e sessões |
| **mqtt** | eclipse-mosquitto | 2.0 | 1883, 9001 | Broker MQTT |

---

## 🚀 Quick Start

### 1. Iniciar Stack Completa

```bash
# Subir todos os serviços
docker compose -f docker-compose.dev.yml up -d

# Ver logs
docker compose -f docker-compose.dev.yml logs -f

# Ver status
docker compose -f docker-compose.dev.yml ps
```

### 2. Aplicar Migrations

```bash
# Com os containers rodando
python manage.py migrate
python manage.py createsuperuser
```

### 3. Executar Django

```bash
python manage.py runserver
```

### 4. Parar Stack

```bash
docker compose -f docker-compose.dev.yml down
```

---

## 🔧 Comandos Úteis

### Gerenciamento de Containers

```bash
# Reiniciar apenas um serviço
docker compose -f docker-compose.dev.yml restart db

# Parar sem remover volumes (dados persistem)
docker compose -f docker-compose.dev.yml stop

# Parar e remover TUDO (inclusive dados)
docker compose -f docker-compose.dev.yml down -v
```

### Acesso Direto aos Serviços

```bash
# PostgreSQL (psql)
docker exec -it tds_new_db_dev psql -U tsdb_django_d4j7g9 -d db_tds_new

# Redis CLI
docker exec -it tds_new_redis_dev redis-cli -a StrongRedisPass2024!

# Mosquitto logs
docker logs -f tds_new_mqtt_dev
```

### Verificar TimescaleDB

```sql
-- Conectar ao PostgreSQL
docker exec -it tds_new_db_dev psql -U tsdb_django_d4j7g9 -d db_tds_new

-- Verificar extensão
SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';

-- Listar hypertables (após criar modelos)
SELECT * FROM timescaledb_information.hypertables;
```

---

## 📂 Estrutura de Arquivos

```
docker/
├── init-db/                           # Scripts de inicialização do PostgreSQL
│   └── 01-init-timescaledb.sql       # Cria extensão TimescaleDB
└── mosquitto/
    ├── config/
    │   └── mosquitto.conf            # Configuração do MQTT broker
    ├── data/                          # Mensagens persistidas
    └── log/                           # Logs do Mosquitto
```

---

## ✅ Validação do Setup

### Healthchecks

Todos os serviços possuem healthchecks automáticos:

```bash
# Status dos healthchecks
docker compose -f docker-compose.dev.yml ps

# Exemplo de output esperado:
# NAME                 STATUS              PORTS
# tds_new_db_dev      Up (healthy)        0.0.0.0:5432->5432/tcp
# tds_new_redis_dev   Up (healthy)        0.0.0.0:6379->6379/tcp
# tds_new_mqtt_dev    Up (healthy)        0.0.0.0:1883->1883/tcp, 0.0.0.0:9001->9001/tcp
```

### Testar Conexões

```python
# test_docker_connections.py
import psycopg2
import redis
import paho.mqtt.client as mqtt

# PostgreSQL + TimescaleDB
conn = psycopg2.connect(
    dbname="db_tds_new",
    user="tsdb_django_d4j7g9",
    password="DjangoTS2025TimeSeries",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()
cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'")
print(f"✅ TimescaleDB version: {cursor.fetchone()[0]}")
conn.close()

# Redis
r = redis.Redis(host='localhost', port=6379, password='StrongRedisPass2024!', db=0)
r.ping()
print("✅ Redis conectado")

# MQTT
def on_connect(client, userdata, flags, rc):
    print(f"✅ MQTT conectado com código: {rc}")

client = mqtt.Client()
client.on_connect = on_connect
client.connect("localhost", 1883, 60)
client.loop_start()
```

---

## 🐛 Troubleshooting

### Erro: "port is already allocated"

```bash
# Ver quem está usando a porta 5432
netstat -ano | findstr :5432

# Parar PostgreSQL local (Windows)
Stop-Service postgresql-x64-17

# Ou mudar porta no docker-compose.dev.yml:
ports:
  - "5433:5432"  # Usar 5433 no host
```

### Erro: "timescaledb extension not available"

```bash
# Verificar se container subiu corretamente
docker logs tds_new_db_dev

# Recriar container e volumes
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d
```

### Container não inicia

```bash
# Ver logs completos
docker compose -f docker-compose.dev.yml logs db

# Remover volumes órfãos
docker volume prune
```

---

## 🎯 Vantagens do Docker Compose

### ✅ **Paridade Dev/Prod**
- TimescaleDB 2.17.2 em dev **IGUAL** produção
- Evita bugs do tipo "funciona na minha máquina"
- Testa funcionalidades de time-series localmente

### ✅ **Setup Rápido**
- Um comando: `docker compose up -d`
- Não precisa instalar PostgreSQL, Redis, MQTT localmente
- Novo dev: clone repo + docker compose + pronto

### ✅ **Isolamento**
- Cada projeto tem sua stack
- Não conflita com outras instalações
- Fácil de resetar: `down -v` + `up -d`

### ✅ **Reprodutibilidade**
- Versionado no Git
- Todos os devs têm exatamente o mesmo ambiente
- CI/CD usa mesma configuração

---

## 🔄 Migração de Setup Local para Docker

### Se você já tem PostgreSQL local instalado:

```bash
# 1. Fazer backup (opcional)
pg_dump -U postgres db_tds_new > backup.sql

# 2. Parar PostgreSQL local
Stop-Service postgresql-x64-17

# 3. Subir Docker Compose
docker compose -f docker-compose.dev.yml up -d

# 4. Restaurar backup (se necessário)
cat backup.sql | docker exec -i tds_new_db_dev psql -U tsdb_django_d4j7g9 -d db_tds_new

# 5. Aplicar migrations
python manage.py migrate
```

### Atualizar .env.dev:

```ini
# Usar TimescaleDB backend (mesma config de produção)
DATABASE_ENGINE=timescale.db.backends.postgresql
DATABASE_HOST=localhost  # Docker expõe na porta 5432 do host
```

---

## 📚 Referências

- TimescaleDB Docker: https://docs.timescale.com/self-hosted/latest/install/installation-docker/
- Docker Compose: https://docs.docker.com/compose/
- Mosquitto: https://mosquitto.org/documentation/
- Redis: https://redis.io/docs/

---

**Última atualização:** 14/02/2026 - Semana 2 (Modelos e Autenticação)
