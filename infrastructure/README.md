# 🏗️ TDS New - Infraestrutura Docker

**Infraestrutura completa para o projeto TDS New (Telemetria IoT)**

## 📂 Estrutura de Pastas

```
infrastructure/
├── docker/
│   ├── development/          🆕 Stack DEV (PostgreSQL + Redis + Mosquitto)
│   │   ├── compose.yml
│   │   ├── .env.example
│   │   └── README.md
│   │
│   ├── production/           🔜 Stack PROD (otimizado)
│   │
│   ├── postgres/             🆕 PostgreSQL + TimescaleDB
│   │   └── init-timescaledb.sh
│   │
│   ├── redis/                🆕 Redis config
│   │   └── redis.conf
│   │
│   └── mosquitto/            🆕 MQTT Broker (Mosquitto)
│       ├── mosquitto.conf
│       ├── acl.conf
│       ├── password.txt
│       ├── scripts/
│       │   ├── setup_passwords.sh
│       │   └── test_connection.sh
│       └── certs/            🔜 Certificados mTLS (Fase 5)
│
└── scripts/
    ├── setup/                🔜 Scripts de instalação
    └── deploy/               🔜 Scripts de deploy
```

## 🚀 Quick Start (Development)

### 1. Iniciar Stack Docker

```powershell
# Navegar até pasta de desenvolvimento
cd f:/projects/infrastructure/docker/development

# Copiar arquivo de variáveis de ambiente
Copy-Item .env.example .env

# Iniciar todos os serviços (PostgreSQL + Redis + Mosquitto + Adminer)
docker compose up -d

# Verificar status
docker compose ps
```

### 2. Configurar Senhas do Mosquitto

```powershell
# Windows (Git Bash ou WSL)
bash ../mosquitto/scripts/setup_passwords.sh

# Ou manualmente dentro do container
docker exec tds-new-mosquitto-dev mosquitto_passwd -b /mosquitto/config/password.txt admin admin
docker exec tds-new-mosquitto-dev kill -HUP 1
```

### 3. Testar Mosquitto

```powershell
# Testar conexão MQTT
bash ../mosquitto/scripts/test_connection.sh

# Ou manualmente
docker exec tds-new-mosquitto-dev mosquitto_sub -t '$SYS/#' -C 5 -u admin -P admin
```

### 4. Configurar Django

No arquivo `.env.dev` do projeto Django (`server-app-tds-new/environments/.env.dev`):

```bash
# Database
DATABASE_HOST=localhost
DATABASE_PORT=5442
DATABASE_NAME=db_tds_new
DATABASE_USER=tsdb_django_d4j7g9
DATABASE_PASSWORD=admin

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# MQTT
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=django_backend
MQTT_PASSWORD=django123
```

### 5. Executar Migrations

```powershell
cd f:/projects/server-app/server-app-tds-new
python manage.py migrate
```

### 6. Iniciar MQTT Consumer

```powershell
python manage.py start_mqtt_consumer --debug
```

## 📦 Serviços Disponíveis

| Serviço | Porta | URL/Comando | Credenciais |
|---------|-------|-------------|-------------|
| **PostgreSQL + TimescaleDB** | 5442 | `psql -h localhost -p 5442 -U tsdb_django_d4j7g9 -d db_tds_new` | tsdb_django_d4j7g9 / admin |
| **Redis** | 6379 | `redis-cli -h localhost -p 6379` | - |
| **Mosquitto MQTT** | 1883 | `mosquitto_sub -h localhost -p 1883 -t '#' -u admin -P admin` | admin / admin |
| **Mosquitto WebSocket** | 9001 | `ws://localhost:9001` | admin / admin |
| **Adminer (GUI PostgreSQL)** | 8080 | http://localhost:8080 | tsdb_django_d4j7g9 / admin |

## 🔧 Comandos Úteis

### Docker Compose

```powershell
# Iniciar stack
docker compose up -d

# Ver logs
docker compose logs -f

# Ver logs de um serviço específico
docker compose logs -f mosquitto

# Parar stack
docker compose down

# Parar e remover volumes (CUIDADO: apaga dados!)
docker compose down -v

# Recriar serviço
docker compose up -d --force-recreate postgres

# Ver uso de recursos
docker stats
```

### PostgreSQL

```powershell
# Conectar ao banco
docker exec -it tds-new-postgres-dev psql -U tsdb_django_d4j7g9 -d db_tds_new

# Verificar TimescaleDB
docker exec -it tds-new-postgres-dev psql -U tsdb_django_d4j7g9 -d db_tds_new -c "\dx"

# Listar hypertables
docker exec -it tds-new-postgres-dev psql -U tsdb_django_d4j7g9 -d db_tds_new -c "SELECT * FROM timescaledb_information.hypertables;"

# Backup
docker exec tds-new-postgres-dev pg_dump -U tsdb_django_d4j7g9 db_tds_new > backup.sql
```

### Redis

```powershell
# Conectar ao Redis
docker exec -it tds-new-redis-dev redis-cli

# Verificar chaves
docker exec tds-new-redis-dev redis-cli KEYS '*'

# Flush all (CUIDADO!)
docker exec tds-new-redis-dev redis-cli FLUSHALL
```

### Mosquitto

```powershell
# Publicar mensagem
docker exec tds-new-mosquitto-dev mosquitto_pub -t 'tds_new/devices/aa:bb:cc:dd:ee:ff/telemetry' -m '{"gateway_mac":"aa:bb:cc:dd:ee:ff","timestamp":"2026-02-18T10:00:00Z","leituras":[{"codigo_dispositivo":"D01","valor_leitura":"123.45","unidade":"kWh"}]}' -u admin -P admin

# Subscrever a todos os topics
docker exec tds-new-mosquitto-dev mosquitto_sub -t '#' -v -u admin -P admin

# Subscrever a telemetria
docker exec tds-new-mosquitto-dev mosquitto_sub -t 'tds_new/devices/+/telemetry' -v -u admin -P admin

# Ver logs
docker logs -f tds-new-mosquitto-dev

# Recarregar configuração
docker exec tds-new-mosquitto-dev kill -HUP 1
```

## 🐛 Troubleshooting

### Porta já em uso

```powershell
# Verificar processo usando a porta
netstat -ano | findstr :5442
netstat -ano | findstr :1883

# Matar processo (Windows)
taskkill /PID <PID> /F
```

### Mosquitto: Connection Refused

```powershell
# Verificar se container está rodando
docker ps | Select-String mosquitto

# Verificar logs
docker logs tds-new-mosquitto-dev

# Verificar arquivo de senhas
docker exec tds-new-mosquitto-dev cat /mosquitto/config/password.txt

# Recriar senhas
bash mosquitto/scripts/setup_passwords.sh
```

### PostgreSQL: Password authentication failed

```powershell
# Verificar senha no .env
cat .env

# Recriar container
docker compose down
docker compose up -d postgres

# Resetar senha (dentro do container)
docker exec -it tds-new-postgres-dev psql -U postgres -c "ALTER USER tsdb_django_d4j7g9 WITH PASSWORD 'admin';"
```

## 📊 Monitoramento

```powershell
# Ver uso de recursos
docker stats

# Verificar saúde dos containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Ver logs consolidados
docker compose logs -f --tail=100

# Verificar network
docker network inspect tds-network
```

## 🗑️ Limpeza

```powershell
# Parar todos os containers
docker compose down

# Remover volumes nomeados
docker volume rm tds-new-postgres-data tds-new-redis-data tds-new-mosquitto-data tds-new-mosquitto-logs

# Remover network
docker network rm tds-network

# Limpar imagens não usadas
docker image prune -a

# Limpar tudo (CUIDADO!)
docker system prune -a --volumes
```

## 📚 Documentação Adicional

- [README Development](docker/development/README.md) - Detalhes do stack de desenvolvimento
- [Setup TimescaleDB](docker/postgres/init-timescaledb.sh) - Script de inicialização do PostgreSQL
- [Redis Config](docker/redis/redis.conf) - Configuração otimizada do Redis
- [Mosquitto Config](docker/mosquitto/mosquitto.conf) - Configuração do MQTT broker
- [Mosquitto ACL](docker/mosquitto/acl.conf) - Access Control List

## 🔐 Segurança

### Development

- ⚠️ Senhas padrão (`admin`, `django123`) - **OK para desenvolvimento**
- ⚠️ Portas expostas no host - **OK para desenvolvimento local**
- ✅ ACL configurado no Mosquitto
- ✅ Autenticação obrigatória no MQTT

### Production (TODO)

- 🔐 Variáveis de ambiente com senhas fortes
- 🔐 Certificados mTLS para Mosquitto (Fase 5)
- 🔐 Firewall restringindo acesso externo
- 🔐 Network isolada (apenas containers)
- 🔐 TLS/SSL habilitado em todos os serviços

## 🚀 Próximos Passos

- [ ] Testar stack completo
- [ ] Integrar com Django
- [ ] Rodar MQTT Consumer
- [ ] Validar telemetria end-to-end
- [ ] Criar stack de produção
- [ ] Implementar mTLS (Fase 5)
- [ ] Configurar backup automático

## 📝 Changelog

- **18/02/2026** - Criação inicial da infraestrutura Docker Development
- **18/02/2026** - Configuração Mosquitto MQTT + ACL
- **18/02/2026** - Scripts de setup e teste

---

**Projeto:** TDS New - Sistema de Telemetria IoT  
**Data:** 18/02/2026  
**Versão:** 1.0
