# ADR-005: Localização do MQTT Consumer

**Status:** ✅ Em Análise  
**Data:** 18/02/2026  
**Contexto:** Decisão sobre onde implementar o MQTT Consumer  
**Decisores:** Equipe de Arquitetura

---

## 📋 Contexto

O sistema TDS New precisa de um **MQTT Consumer** para processar telemetria de dispositivos IoT em tempo real. A questão é: **onde deve ficar esse componente?**

### Opções Identificadas

1. **Dentro do Backend Django** (`/server-app/server-app-tds-new/tds_new/consumers/`)
2. **Na Infraestrutura Separada** (`/infrastructure/mqtt-consumer/`)
3. **Híbrido: Container Separado usando Django** (`/infrastructure/django-mqtt-consumer/`)

---

## 🔍 Análise Comparativa

### Opção 1: Consumer DENTRO do Backend Django

**Localização:** `/server-app/server-app-tds-new/tds_new/consumers/`

```
server-app-tds-new/
├── tds_new/
│   ├── consumers/           ← MQTT Consumer aqui
│   │   ├── mqtt_telemetry.py
│   │   └── mqtt_config.py
│   ├── services/
│   ├── models/
│   └── views/
```

#### ✅ Vantagens

1. **Acesso Direto ao ORM**
   - Sem overhead de API REST (~50-100ms economizados)
   - Transações atômicas garantidas
   - Bulk inserts eficientes no TimescaleDB

2. **Reutilização de Código**
   - Usa models, services, validators do Django
   - Usa middlewares (multi-tenant, logging)
   - Usa context processors

3. **Simplicidade de Deploy**
   - 1 serviço em vez de 2
   - 1 Dockerfile em vez de 2
   - Menos configuração (sem autenticação entre serviços)

4. **Debugging Mais Fácil**
   - Mesmo ambiente Python
   - Logs integrados com Django logging
   - Django Debug Toolbar funciona

5. **Baixa Latência**
   - Latência típica: **100-200ms** (MQTT → Consumer → TimescaleDB)
   - Sem overhead de HTTP/REST

#### ❌ Desvantagens

1. **Escalabilidade Acoplada**
   - Para escalar consumer, precisa escalar todo o Django
   - Não pode ter 10 consumers e 2 Gunicorn workers

2. **Deploy Acoplado**
   - Mudança no consumer requer restart do Django REST API
   - Downtime afeta frontend e telemetria simultaneamente

3. **Arquitetura Monolítica**
   - Violação de SRP (Single Responsibility Principle)
   - Backend REST + Message Consumer no mesmo processo

4. **Consumo de Recursos**
   - Django é pesado para apenas processar mensagens
   - Overhead de carregar toda a aplicação

---

### Opção 2: Consumer NA INFRAESTRUTURA (Microservice Puro)

**Localização:** `/infrastructure/mqtt-consumer/`

```
infrastructure/
└── mqtt-consumer/
    ├── Dockerfile
    ├── requirements.txt
    ├── consumer.py          ← Consumer standalone
    ├── api_client.py        ← Chama backend via REST
    └── config.py
```

#### ✅ Vantagens

1. **Separação de Responsabilidades**
   - Consumer só consome mensagens
   - Backend só serve API REST
   - SRP respeitado

2. **Escalabilidade Independente**
   - Pode rodar 10 consumers e 2 Gunicorn workers
   - Escala horizontalmente conforme carga de telemetria

3. **Deploy Independente**
   - Atualizar lógica do consumer não afeta backend
   - Zero downtime para frontend

4. **Flexibilidade de Tecnologia**
   - Pode usar Go, Rust, Node.js para melhor performance
   - Não precisa carregar todo o Django

5. **Isolamento de Falhas**
   - Consumer crashar não afeta API REST
   - API crashar não afeta Consumer

#### ❌ Desvantagens

1. **Latência Adicional**
   - Precisa chamar API REST do backend (~50-100ms)
   - Latência típica: **200-400ms** (MQTT → Consumer → REST API → DB)

2. **Duplicação de Lógica**
   - Validações precisam ser duplicadas
   - Transformações de dados duplicadas
   - Manutenibilidade reduzida

3. **Complexidade de Deploy**
   - 2 serviços para gerenciar
   - 2 Dockerfiles
   - Autenticação entre serviços (JWT, API keys)

4. **Transações Distribuídas**
   - Dificulta atomicidade
   - Consumer salva → API falha = inconsistência

5. **Overhead de Infraestrutura**
   - Mais containers
   - Mais configuração
   - Maior consumo de recursos

---

### Opção 3: Híbrido (Container Separado usando Django)

**Localização:** `/infrastructure/django-mqtt-consumer/`

```
infrastructure/
└── django-mqtt-consumer/
    ├── Dockerfile
    ├── requirements.txt     ← Mesmas deps do backend
    ├── settings.py          ← Django settings mínimas
    ├── consumer.py          ← Importa tds_new.consumers
    └── docker-compose.yml
```

**Como Funciona:**
1. Consumer roda em container separado
2. Importa código do backend Django (models, services)
3. Conecta ao mesmo banco de dados
4. Usa Django ORM, mas não serve HTTP

#### ✅ Vantagens

1. **Separação de Deploy** (melhor que Opção 1)
   - Consumer escala independente
   - Backend escala independente

2. **Acesso Direto ao ORM** (melhor que Opção 2)
   - Sem overhead de API REST
   - Transações atômicas

3. **Reutilização de Código** (melhor que Opção 2)
   - Usa models, services do Django
   - DRY principle respeitado

4. **Isolamento de Falhas** (melhor que Opção 1)
   - Consumer crashar não afeta API
   - API crashar não afeta Consumer

#### ❌ Desvantagens

1. **Complexidade Moderada**
   - Precisa configurar Django no consumer
   - Precisa sincronizar código (ci/cd ou pip package)

2. **Acoplamento de Banco**
   - Ambos acessam mesmo banco
   - Schema migration afeta ambos

3. **Gestão de Código**
   - Precisa fazer backend virar package (`pip install -e .`)
   - OU copiar código no Dockerfile

---

## 📊 Comparação por Critério

| Critério | Opção 1: Django | Opção 2: Microservice | Opção 3: Híbrido |
|----------|-----------------|----------------------|------------------|
| **Latência** | 🟢 100-200ms | 🟡 200-400ms | 🟢 100-200ms |
| **Escalabilidade** | 🔴 Acoplada | 🟢 Independente | 🟢 Independente |
| **Deploy** | 🔴 Acoplado | 🟢 Independente | 🟢 Independente |
| **Simplicidade** | 🟢 1 serviço | 🔴 2 serviços + REST | 🟡 2 serviços |
| **Reutilização Código** | 🟢 Total | 🔴 Duplicação | 🟢 Total |
| **Isolamento Falhas** | 🔴 Acoplado | 🟢 Isolado | 🟢 Isolado |
| **Transações** | 🟢 Atômicas | 🔴 Distribuídas | 🟢 Atômicas |
| **Manutenibilidade** | 🟢 Alta | 🔴 Duplicação | 🟡 Moderada |
| **Overhead Infra** | 🟢 Baixo | 🔴 Alto | 🟡 Moderado |

**Legenda:** 🟢 Excelente | 🟡 Aceitável | 🔴 Problemático

---

## 🎯 Decisão Recomendada (Evolutionary Architecture)

### Fase 1: MVP (AGORA - Primeiros 6 meses)
**Escolha:** ✅ **Opção 1 - Consumer DENTRO do Django**

**Justificativa:**
- ✅ Projeto em estágio inicial (85% base, 15% implementação)
- ✅ Ainda não há escala significativa (<100 gateways no MVP)
- ✅ Prioridade é validar produto (time-to-market)
- ✅ Latência baixa é crítica (<300ms)
- ✅ Equipe pequena (simplicidade > escalabilidade prematura)

**Implementação:**
```
server-app-tds-new/
├── tds_new/
│   ├── consumers/
│   │   ├── __init__.py
│   │   ├── mqtt_telemetry.py        # Cliente Paho-MQTT
│   │   └── mqtt_config.py           # Configurações
│   ├── services/
│   │   └── telemetry_processor.py   # Business logic
│   └── management/commands/
│       └── start_mqtt_consumer.py   # Django command
```

**Execução:**
```bash
# Development
python manage.py start_mqtt_consumer

# Production (systemd)
systemctl start tds-new-mqtt-consumer
```

---

### Fase 2: Crescimento (6-12 meses após MVP)
**Escolha:** ✅ **Opção 3 - Híbrido (Container Separado)**

**Justificativa:**
- ✅ Escala aumentou (>100 gateways, >1000 leituras/min)
- ✅ Necessidade de escalar consumer independente
- ✅ Backend já estabilizado (menos mudanças)
- ✅ Budget para infraestrutura aumentou

**Implementação:**
```
infrastructure/
└── django-mqtt-consumer/
    ├── Dockerfile
    │   FROM python:3.12
    │   COPY --from=backend /app /app
    │   RUN pip install -e /app
    │   CMD ["python", "manage.py", "start_mqtt_consumer"]
    │
    ├── docker-compose.yml
    │   services:
    │     mqtt-consumer:
    │       build: .
    │       environment:
    │         DJANGO_SETTINGS_MODULE: prj_tds_new.settings
    │       depends_on:
    │         - postgres
    │         - mosquitto
    │
    └── kubernetes/
        └── deployment.yaml
            replicas: 5   # Escala horizontal
```

**Vantagens nesta fase:**
- ✅ Escala 5 consumers enquanto backend mantém 2 workers
- ✅ Deploy independente (consumer muda mais que views)
- ✅ Ainda usa Django ORM (sem duplicação de código)

---

### Fase 3: Alta Escala (>12 meses, 1000+ gateways)
**Escolha:** ✅ **Opção 2 - Microservice Puro (Go/Rust)**

**Justificativa:**
- ✅ Escala massiva (>10.000 leituras/min)
- ✅ Necessidade de otimização extrema
- ✅ Python/Django é gargalo de performance
- ✅ Equipe e budget suportam microservices

**Implementação:**
```
infrastructure/
└── mqtt-consumer-go/        # Reescrever em Go
    ├── main.go              # Consumer otimizado
    ├── grpc_client.go       # Comunica com backend via gRPC (não REST)
    └── Dockerfile
        FROM golang:1.21-alpine
        ...
```

**Performance esperada:**
- 🚀 Latência: 50-100ms (vs 100-200ms Python)
- 🚀 Throughput: 50.000 msgs/s (vs 5.000 msgs/s Python)
- 🚀 Memória: 50MB (vs 200MB Python/Django)

**Trade-off:**
- ❌ Duplicação de lógica de negócio (validações em Go e Python)
- ❌ Complexidade de manutenção (2 linguagens)
- ✅ Justificável apenas em alta escala

---

## 🏗️ Arquitetura Evolutiva (Resumo)

```
Fase 1 (MVP - 0-6 meses)
┌─────────────────────────────────────┐
│  Django Backend + MQTT Consumer     │  ← 1 serviço
│  ├── REST API (Gunicorn)            │
│  ├── MQTT Consumer (thread)         │  ← AQUI
│  └── Celery Tasks                   │
└─────────────────────────────────────┘
   ↓ acesso direto ORM
┌─────────────────────────────────────┐
│  PostgreSQL + TimescaleDB           │
└─────────────────────────────────────┘

Fase 2 (Crescimento - 6-12 meses)
┌──────────────────┐  ┌───────────────────┐
│ Django Backend   │  │ MQTT Consumer     │  ← 2 serviços
│ (2 replicas)     │  │ (5 replicas)      │  ← Escala separado
└──────────────────┘  └───────────────────┘
        ↓                     ↓
        └─────────┬───────────┘
                  ↓ ORM compartilhado
        ┌─────────────────────┐
        │ PostgreSQL 17 +     │
        │ TimescaleDB 2.17    │
        └─────────────────────┘

Fase 3 (Alta Escala - >12 meses)
┌──────────────────┐  ┌───────────────────┐
│ Django Backend   │  │ Go Consumer       │  ← Consumer reescrito
│ (2 replicas)     │  │ (10 replicas)     │
└──────────────────┘  └───────────────────┘
        ↓                     ↓
      REST API             gRPC/Direct DB
        ↓                     ↓
        └─────────┬───────────┘
                  ↓
        ┌─────────────────────┐
        │ PostgreSQL Cluster  │  ← Cluster para escala
        │ TimescaleDB         │
        └─────────────────────┘
```

---

## 📝 Decisão Final para AGORA (Fase 1)

### ✅ Consumer PERMANECE no Backend Django

**Localização:** `/server-app/server-app-tds-new/tds_new/consumers/`

**Motivos:**
1. **Simplicidade** - 1 serviço, 1 deploy, 1 Dockerfile
2. **Baixa Latência** - <200ms end-to-end (crítico para IoT)
3. **DRY** - Reutiliza 100% do código Django
4. **Transações Atômicas** - Garantia de consistência
5. **Fase MVP** - Escala prematura é overengineering
6. **Equipe Pequena** - Menos complexidade para gerenciar

**Quando Reavaliar:**
- ✅ Se >100 gateways ativos
- ✅ Se >5.000 leituras/min
- ✅ Se consumer consumir >50% CPU do backend
- ✅ Se deploy do consumer precisar ser independente

**Migração Futura:**
- O código já fica em `tds_new/consumers/` (isolado)
- Fácil mover para container separado (Opção 3)
- Ou reescrever em Go depois (Opção 2)

---

## 🔄 Estratégia de Migração (Quando Chegar a Hora)

### De Opção 1 → Opção 3 (Sem Downtime)

```bash
# 1. Criar Dockerfile do consumer
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY tds_new/ /app/tds_new/
CMD ["python", "manage.py", "start_mqtt_consumer"]

# 2. Deploy gradual (Blue-Green)
docker compose up -d mqtt-consumer-new  # Nova versão
# Testar
systemctl stop tds-new-mqtt-consumer    # Parar antiga
docker compose rm mqtt-consumer-old     # Remover antiga

# 3. Monitorar latência, throughput, erros
# Se OK: commit
# Se problema: rollback
```

---

## 📚 Referências

- **Martin Fowler - Monolith First**: https://martinfowler.com/bliki/MonolithFirst.html
  > "Almost all the successful microservice stories have started with a monolith that got too big"

- **12-Factor App - Processes**: https://12factor.net/processes
  > "Execute the app as one or more stateless processes"

- **Django Channels Documentation**: https://channels.readthedocs.io/
  > "Extends Django to handle WebSockets, MQTT, and other protocols"

- **Sam Newman - Building Microservices**
  > "Don't start with microservices. Extract them when you have clear bounded contexts"

---

## ✅ Conclusão

### Para o TDS New AGORA (Fase 1 - MVP):

**✅ MANTER Consumer no Backend Django** (`tds_new/consumers/`)

**Razão:** Simplicidade > Escalabilidade Prematura

**Próxima Revisão:** Após 100 gateways OU 6 meses de operação

---

**Aprovado por:** Equipe de Arquitetura  
**Data:** 18/02/2026  
**Próxima Revisão:** Agosto/2026 (6 meses)  
**Status ADR:** ✅ Aceito

