# 🐳 Docker Stack - Development

Stack completo para desenvolvimento local do TDS New.

## 📦 Serviços Incluídos

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| **PostgreSQL 17 + TimescaleDB** | 5442 | Banco de dados principal |
| **Redis 7.2** | 6379 | Cache + Celery broker |
| **Mosquitto 2.0** | 1883 | MQTT broker |
| **Mosquitto WebSocket** | 9001 | MQTT via WebSocket |
| **Adminer** | 8080 | GUI PostgreSQL |

## 🚀 Iniciar Stack

```powershell
# 1. Copiar .env.example
Copy-Item .env.example .env

# 2. Iniciar todos os serviços
docker compose up -d

# 3. Verificar status
docker compose ps

# 4. Ver logs
docker compose logs -f
```

## 🔍 Verificar Serviços

### PostgreSQL + TimescaleDB

```powershell
# Conectar ao PostgreSQL
docker exec -it tds-new-postgres-dev psql -U tsdb_django_d4j7g9 -d db_tds_new

# Verificar extensão TimescaleDB
\dx

# Listar hypertables
SELECT * FROM timescaledb_information.hypertables;
```

### Redis

```powershell
# Conectar ao Redis
docker exec -it tds-new-redis-dev redis-cli

# Testar
PING
# Deve retornar: PONG
```

### Mosquitto MQTT

```powershell
# Testar conexão MQTT
docker exec tds-new-mosquitto-dev mosquitto_sub -t '$SYS/#' -C 1 -u admin -P admin

# Publicar mensagem de teste
docker exec tds-new-mosquitto-dev mosquitto_pub -t 'test/topic' -m 'Hello MQTT' -u admin -P admin

# Ver logs
docker logs tds-new-mosquitto-dev
```

### Adminer (GUI PostgreSQL)

Acesse: http://localhost:8080

- **Sistema:** PostgreSQL
- **Servidor:** postgres
- **Usuário:** tsdb_django_d4j7g9
- **Senha:** admin (ou valor do .env)
- **Base de dados:** db_tds_new

## 🛑 Parar Stack

```powershell
# Parar todos os serviços
docker compose down

# Parar e remover volumes (CUIDADO: apaga dados!)
docker compose down -v
```

## 🔧 Troubleshooting

### Porta já em uso

Se receber erro "port is already allocated":

```powershell
# Verificar qual processo está usando a porta
netstat -ano | findstr :5442

# Matar processo (substitua <PID>)
taskkill /PID <PID> /F
```

### Serviço não inicia

```powershell
# Ver logs de um serviço específico
docker compose logs postgres
docker compose logs mosquitto

# Recriar serviço
docker compose up -d --force-recreate postgres
```

### Mosquitto: Connection Refused

```powershell
# Verificar se está rodando
docker ps | Select-String mosquitto

# Verificar portas
docker port tds-new-mosquitto-dev

# Testar internamente
docker exec tds-new-mosquitto-dev mosquitto_sub -t '$SYS/#' -C 1 -u admin -P admin
```

## 📊 Monitoramento

```powershell
# Ver uso de recursos
docker stats

# Ver logs em tempo real
docker compose logs -f --tail=100

# Ver logs de um serviço específico
docker compose logs -f mosquitto
```

## 🗑️ Limpeza Completa

```powershell
# Parar stack
docker compose down

# Remover volumes
docker volume rm tds-new-postgres-data tds-new-redis-data tds-new-mosquitto-data tds-new-mosquitto-logs

# Remover network
docker network rm tds-network

# Limpar imagens não usadas
docker image prune -a
```

## 🔗 Integração com Django

No arquivo `.env` do Django (`server-app-tds-new/environments/.env.dev`):

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

# MQTT
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=admin
MQTT_PASSWORD=admin
```

## 📝 Notas

- **Volumes nomeados:** Os dados persistem mesmo após `docker compose down`
- **Network isolada:** Todos os serviços estão na rede `tds-network`
- **Healthchecks:** Todos os serviços têm verificação de saúde automática
- **Auto-restart:** Serviços reiniciam automaticamente em caso de falha
