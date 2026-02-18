# 📋 Plano de Implementação - Telemetria IoT

**Projeto:** TDS New - Sistema de Telemetria e Monitoramento IoT  
**Data:** 18/02/2026  
**Abordagem:** ✅ **Arquitetura Evolutiva** (MVP → Crescimento → Alta Escala)

---

## 🎯 RESUMO EXECUTIVO

### Decisão Arquitetural
✅ **MQTT Consumer dentro do Backend Django** (MVP/Fase 1)
- Simplicidade > Escalabilidade Prematura
- Latência <200ms (crítico para IoT)
- Código DRY (reutiliza models/services)
- Migração futura facilitada

**Fonte:** [ADR-005](architecture/ADR-005-MQTT-CONSUMER-LOCATION.md) - MQTT Consumer Location

---

## 📊 VISÃO GERAL

```
Estado Atual:  85% pronto (models, views, templates, DB)
Falta:         15% (4 pastas, 8 arquivos, ~500 linhas)
Tempo Total:   33-45 horas (6 fases)
MVP Funcional: 3 dias (20 horas - Fases 1+2+4)
```

### Componentes Prontos ✅
- Models (Gateway, Dispositivo, LeituraDispositivo, CertificadoDevice)
- Views CRUD (Gateway, Dispositivo)
- Forms com validações
- Templates Bootstrap 5.3.2
- PostgreSQL 17 + TimescaleDB 2.17.2
- Migrations aplicadas

### Componentes a Criar 🆕
- MQTT Consumer (Fase 2)
- TimescaleDB Hypertable (Fase 1)
- Dashboard Telemetria (Fase 4)
- Celery (Fase 3 - opcional para MVP)
- mTLS (Fase 5 - opcional para MVP)
- Testes E2E (Fase 6)

---

## 🚀 PLANO DE IMPLEMENTAÇÃO (6 Fases)

### 📅 FASE 1: TimescaleDB Hypertable
**Duração:** 3-4 horas | **Prioridade:** 🔴 Crítica

**O que fazer:**
```bash
# 1. Criar scripts SQL
mkdir scripts
touch scripts/setup_timescaledb.sql

# 2. Executar hypertable
psql -U tsdb_django_d4j7g9 -d db_tds_new -p 5442 -f scripts/setup_timescaledb.sql
```

**Arquivos a criar:**
- `scripts/setup_timescaledb.sql` (150 linhas)
- `scripts/create_hypertable.sql` (50 linhas)
- `scripts/create_indexes.sql` (40 linhas)
- `scripts/create_continuous_aggregate.sql` (80 linhas)

**SQL:**
```sql
-- CREATE HYPERTABLE
SELECT create_hypertable('tds_new_leitura_dispositivo', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

-- CREATE MATERIALIZED VIEW (consumo mensal)
CREATE MATERIALIZED VIEW tds_new_consumo_mensal ...

-- CREATE INDEXES
CREATE INDEX idx_conta_time ON tds_new_leitura_dispositivo (conta_id, timestamp DESC);
```

**Resultado:** Hypertable operacional, pronta para receber telemetria

---

### 📅 FASE 2: MQTT Consumer
**Duração:** 6-8 horas | **Prioridade:** 🔴 Crítica

**O que fazer:**
```bash
# 1. Criar estrutura
mkdir -p tds_new/consumers
mkdir -p tds_new/services
mkdir -p tds_new/management/commands

# 2. Implementar arquivos
# Código fornecido em VIABILIDADE_TELEMETRIA.md linhas 500-870
```

**Arquivos a criar:**
- `tds_new/consumers/mqtt_telemetry.py` (250 linhas)
- `tds_new/consumers/mqtt_config.py` (80 linhas)
- `tds_new/services/telemetry_processor.py` (200 linhas)
- `tds_new/management/commands/start_mqtt_consumer.py` (80 linhas)
- `tests/test_mqtt_consumer.py` (150 linhas)
- `tests/test_telemetry_service.py` (120 linhas)

**Lógica:**
```python
# Consumer MQTT → Processar JSON → Salvar no TimescaleDB
def on_message(client, userdata, msg):
    payload = json.loads(msg.payload)
    service = TelemetryProcessorService(conta_id, gateway)
    service.processar_telemetria(payload)
```

**Executar:**
```bash
python manage.py start_mqtt_consumer
```

**Resultado:** Consumer processando mensagens MQTT e salvando no banco

---

### 📅 FASE 3: Celery + Redis (OPCIONAL PARA MVP)
**Duração:** 4-5 horas | **Prioridade:** 🟡 Média

**O que fazer:**
```bash
# 1. Adicionar dependência
echo "celery==5.3.6" >> requirements.txt
pip install celery==5.3.6

# 2. Criar configuração Celery
touch prj_tds_new/celery.py

# 3. Executar worker
celery -A prj_tds_new worker -l info
```

**Quando implementar:**
- ⏸️ Pode ser pulado no MVP
- ✅ Implementar quando escala justificar (>100 gateways)

**Resultado:** Consumer roda como Celery task (mais robusto)

---

### 📅 FASE 4: Dashboard de Telemetria
**Duração:** 8-10 horas | **Prioridade:** 🔴 Crítica

**O que fazer:**
```bash
# 1. Criar views de telemetria
touch tds_new/views/telemetria.py

# 2. Criar templates
mkdir -p tds_new/templates/tds_new/telemetria
touch tds_new/templates/tds_new/telemetria/dashboard.html

# 3. Criar static files (CSS/JS)
mkdir -p tds_new/static/tds_new/js
mkdir -p tds_new/static/tds_new/css
```

**Arquivos a criar:**
- `tds_new/views/telemetria.py` (250 linhas)
- `tds_new/views/api_telemetria.py` (100 linhas)
- `tds_new/templates/tds_new/telemetria/dashboard.html` (400 linhas)
- `tds_new/static/tds_new/js/telemetria.js` (300 linhas)
- `tds_new/static/tds_new/css/telemetria.css` (150 linhas)

**Features:**
- 📊 Gráficos Chart.js (consumo mensal)
- 📋 Tabela últimas 50 leituras
- 🔄 Auto-refresh AJAX (30 segundos)
- 📈 Cards de métricas (gateways online, leituras/dia)

**Resultado:** Dashboard funcional exibindo telemetria em tempo real

---

### 📅 FASE 5: Mosquitto + mTLS (OPCIONAL PARA MVP)
**Duração:** 6-10 horas | **Prioridade:** 🟡 Baixa

**O que fazer:**
```bash
# 1. Gerar certificados X.509
python scripts/certificados/gerar_ca.py
python scripts/certificados/gerar_certificado_broker.py

# 2. Configurar Mosquitto
# Editar mosquitto.conf (porta 8883, TLS obrigatório)
```

**Quando implementar:**
- ⏸️ Pode ser pulado no MVP (usar MQTT sem TLS)
- ✅ Implementar antes de produção (segurança)

**Resultado:** Broker MQTT com mTLS (autenticação por certificado)

---

### 📅 FASE 6: Testes E2E (OPCIONAL PARA MVP)
**Duração:** 6-8 horas | **Prioridade:** 🟡 Média

**O que fazer:**
```bash
# 1. Criar simuladores de gateway
mkdir -p tests/simuladores
touch tests/simuladores/simulador_gateway.py

# 2. Executar testes
python manage.py test tests.integration
```

**Quando implementar:**
- ⏸️ Pode ser pulado no MVP
- ✅ Implementar antes de escalar (>100 gateways)

**Resultado:** Suite de testes automatizados validando fluxo completo

---

## ⚡ OPÇÕES DE IMPLEMENTAÇÃO

### 🏃 MVP Mínimo (3 dias - 20 horas)
**Fases:** 1 + 2 + 4  
**Resultado:** Telemetria funcional com dashboard

```
Dia 1 (8h):  Fase 1 (3h) + Fase 2 início (5h)
Dia 2 (8h):  Fase 2 fim (3h) + Fase 4 início (5h)
Dia 3 (4h):  Fase 4 fim (4h)
```

**✅ O que funciona:**
- ✅ Gateway envia telemetria via MQTT
- ✅ Consumer processa e salva no TimescaleDB
- ✅ Dashboard exibe gráficos e métricas
- ✅ Auto-refresh (30s)

**❌ O que falta:**
- ❌ Celery (consumer roda como Django command)
- ❌ mTLS (MQTT sem TLS)
- ❌ Testes E2E

---

### 🚀 MVP Completo (7 dias - 35 horas)
**Fases:** 1 + 2 + 3 + 4  
**Resultado:** Telemetria funcional + Celery + Dashboard

```
Semana 1: Fases 1+2+3+4 (35 horas)
```

**✅ O que funciona:**
- ✅ Tudo do MVP Mínimo
- ✅ Celery Worker processando mensagens
- ✅ Mais robusto (auto-restart, fila de tarefas)

---

### 🏭 Produção (17 dias - 40 horas)
**Fases:** 1 + 2 + 3 + 4 + 5 + 6  
**Resultado:** Sistema completo pronto para produção

**✅ O que funciona:**
- ✅ Tudo do MVP Completo
- ✅ mTLS (segurança)
- ✅ Testes E2E (qualidade)
- ✅ Certificados X.509
- ✅ Suite de testes

---

## 📅 CRONOGRAMA RECOMENDADO (MVP Mínimo)

### 🗓️ Dia 1 - Terça (18/02/2026)
**8h de trabalho**

| Hora | Atividade | Fase | Duração |
|------|-----------|------|---------|
| 09:00-10:00 | Criar scripts SQL | Fase 1 | 1h |
| 10:00-11:00 | Executar hypertable + indexes | Fase 1 | 1h |
| 11:00-12:00 | Validar hypertable funcionando | Fase 1 | 1h |
| **12:00-13:00** | **Almoço** | - | 1h |
| 13:00-15:00 | Implementar MQTT Consumer | Fase 2 | 2h |
| 15:00-17:00 | Implementar Telemetry Service | Fase 2 | 2h |
| 17:00-18:00 | Implementar Django Command | Fase 2 | 1h |

**✅ Entregável:** Hypertable criado + Consumer 70% implementado

---

### 🗓️ Dia 2 - Quarta (19/02/2026)
**8h de trabalho**

| Hora | Atividade | Fase | Duração |
|------|-----------|------|---------|
| 09:00-11:00 | Finalizar MQTT Consumer | Fase 2 | 2h |
| 11:00-12:00 | Testar Consumer (simulador) | Fase 2 | 1h |
| **12:00-13:00** | **Almoço** | - | 1h |
| 13:00-15:00 | Criar views telemetria | Fase 4 | 2h |
| 15:00-17:00 | Criar template dashboard | Fase 4 | 2h |
| 17:00-18:00 | Integrar Chart.js | Fase 4 | 1h |

**✅ Entregável:** Consumer funcional + Dashboard 60% implementado

---

### 🗓️ Dia 3 - Quinta (20/02/2026)
**4h de trabalho**

| Hora | Atividade | Fase | Duração |
|------|-----------|------|---------|
| 09:00-11:00 | Implementar auto-refresh AJAX | Fase 4 | 2h |
| 11:00-12:00 | Implementar cards de métricas | Fase 4 | 1h |
| **12:00-13:00** | **Almoço** | - | 1h |
| 13:00-14:00 | Testes manuais E2E | Fase 4 | 1h |

**✅ Entregável:** Dashboard 100% funcional

---

### 🗓️ Sexta (21/02/2026)
**Validação Final**

| Hora | Atividade | Duração |
|------|-----------|---------|
| 09:00-10:00 | Teste com gateway real | 1h |
| 10:00-11:00 | Ajustes finais | 1h |
| 11:00-12:00 | Deploy em ambiente de testes | 1h |

**✅ MVP MÍNIMO CONCLUÍDO** 🎉

---

## 🔍 VALIDAÇÃO DE SUCESSO

### Critérios Técnicos
- ✅ Gateway envia telemetria → Consumer processa → DB salva
- ✅ Latência end-to-end <500ms
- ✅ Dashboard exibe dados em tempo real
- ✅ Auto-refresh funciona (30s)
- ✅ 100% leituras persistidas (sem perda)

### Critérios de Negócio
- ✅ Stakeholder vê telemetria em dashboard
- ✅ Demonstração funcional para clientes
- ✅ ROI validado (tempo investido vs valor entregue)

---

## 🛠️ PRÓXIMOS PASSOS IMEDIATOS

### 1️⃣ HOJE (18/02/2026 - 1 hora)

```bash
# Terminal 1: Criar estrutura
cd f:/projects/server-app/server-app-tds-new

# Criar pastas
mkdir scripts
mkdir scripts\certificados
mkdir tests\integration
mkdir tests\simuladores

# Criar arquivo SQL
code scripts/setup_timescaledb.sql
```

**Conteúdo do SQL:**
```sql
-- Código completo disponível em:
-- docs/architecture/INTEGRACAO.md linhas 500-650
-- OU docs/VIABILIDADE_TELEMETRIA.md linhas 350-450
```

**Executar:**
```bash
# Terminal 2: Executar script
psql -U tsdb_django_d4j7g9 -d db_tds_new -p 5442 -f scripts/setup_timescaledb.sql

# Validar
psql -U tsdb_django_d4j7g9 -d db_tds_new -p 5442 -c "SELECT * FROM timescaledb_information.hypertables;"
```

**✅ Resultado esperado:** Hypertable `tds_new_leitura_dispositivo` criado

---

### 2️⃣ AMANHÃ (19/02/2026 - 6 horas)

```bash
# Criar estrutura de pastas
mkdir tds_new\consumers
mkdir tds_new\services
mkdir tds_new\management\commands

# Criar arquivos Python
# Código completo em docs/VIABILIDADE_TELEMETRIA.md linhas 500-870
code tds_new/consumers/mqtt_telemetry.py
code tds_new/services/telemetry_processor.py
code tds_new/management/commands/start_mqtt_consumer.py

# Testar consumer
python manage.py start_mqtt_consumer
```

---

### 3️⃣ SEXTA (21/02/2026 - 8 horas)

```bash
# Implementar dashboard
mkdir tds_new\templates\tds_new\telemetria
mkdir tds_new\static\tds_new\js
mkdir tds_new\static\tds_new\css

# Código completo em docs/VIABILIDADE_TELEMETRIA.md linhas 900-1100
code tds_new/views/telemetria.py
code tds_new/templates/tds_new/telemetria/dashboard.html
```

---

## 📚 DOCUMENTAÇÃO DE REFERÊNCIA

### Documentos Criados (18/02/2026)
1. **[VIABILIDADE_TELEMETRIA.md](VIABILIDADE_TELEMETRIA.md)** (1.200 linhas)
   - Análise completa de viabilidade
   - Código completo de todas as fases
   - 3 planos de implementação

2. **[ESTRUTURA_PASTAS_TELEMETRIA.md](ESTRUTURA_PASTAS_TELEMETRIA.md)** (1.400 linhas)
   - Estrutura detalhada de cada fase
   - Visualização de pastas
   - Comandos de execução

3. **[ARQUITETURA_PASTAS_COMPLETA.md](ARQUITETURA_PASTAS_COMPLETA.md)** (1.800 linhas)
   - Proposta de estrutura global
   - Backend + Firmware + Infraestrutura
   - Docker Compose completo

4. **[ADR-005-MQTT-CONSUMER-LOCATION.md](architecture/ADR-005-MQTT-CONSUMER-LOCATION.md)** (2.000 linhas)
   - Decisão arquitetural (Consumer no backend)
   - Análise de 3 opções
   - Estratégia de evolução

5. **[DECISOES.md](architecture/DECISOES.md)** (600 linhas)
   - 5 ADRs documentados
   - Todas as decisões arquiteturais

### Documentos Existentes
- [ROADMAP.md](ROADMAP.md) - Status do projeto
- [INTEGRACAO.md](architecture/INTEGRACAO.md) - Fluxo end-to-end
- [PROVISIONAMENTO_IOT.md](PROVISIONAMENTO_IOT.md) - Gestão de dispositivos

---

## 🎯 DECISÃO FINAL

### ✅ Implementar MVP Mínimo (3 dias)
**Fases:** 1 + 2 + 4  
**Prazo:** 18/02 a 21/02/2026  
**Esforço:** 20 horas

**Motivos:**
1. ✅ Entrega funcionalidade completa rapidamente
2. ✅ Valida arquitetura e stack tecnológico
3. ✅ Demonstrável para stakeholders
4. ✅ ROI alto (20h investidas = telemetria funcional)
5. ✅ Fases 3+5+6 podem ser incrementais depois

**Migração Futura:**
- Fase 3 (Celery) → Quando >100 gateways
- Fase 5 (mTLS) → Antes de produção
- Fase 6 (Testes) → Quando escalar

---

## 📊 RESUMO VISUAL

```
HOJE (18/02)         AMANHÃ (19/02)      SEXTA (21/02)
┌─────────────┐      ┌─────────────┐     ┌─────────────┐
│  Fase 1     │  →   │  Fase 2     │  →  │  Fase 4     │
│  3 horas    │      │  6 horas    │     │  8 horas    │
└─────────────┘      └─────────────┘     └─────────────┘
   Hypertable          MQTT Consumer      Dashboard
   
                                            ↓
                                       
                                    🎉 MVP FUNCIONAL
                                    
                                    Gateway → MQTT → Consumer
                                            ↓
                                       TimescaleDB
                                            ↓
                                        Dashboard
```

---

**Status:** ✅ Plano Aprovado  
**Início:** 18/02/2026 (HOJE)  
**Conclusão MVP:** 21/02/2026 (Sexta)  
**Próxima Revisão:** Após 100 gateways OU 6 meses

