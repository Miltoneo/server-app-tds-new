# 🗺️ ROADMAP - Sistema TDS New

**Projeto:** TDS New - Sistema de Telemetria e Monitoramento IoT  
**Repositório:** [Miltoneo/server-app-tds-new](https://github.com/Miltoneo/server-app-tds-new)  
**Versão:** 2.0  
**Última Atualização:** 18/02/2026  
**Status Geral:** 🟢 **Weeks 1-5 CONCLUÍDAS** | 🔵 **Pronto para Week 6-7**

---

## 📖 DOCUMENTAÇÃO COMPLEMENTAR

Este roadmap foca no **planejamento** e **timeline** do projeto. Para detalhes técnicos, consulte:

- **[PROVISIONAMENTO_IOT.md](PROVISIONAMENTO_IOT.md)**: Guia operacional completo de provisionamento de dispositivos (Manual, API, Zero-Touch)
- **[architecture/DECISOES.md](architecture/DECISOES.md)**: Decisões arquiteturais detalhadas (ADRs)
  - ADR-001: Estratégia de MQTT Consumer (Django vs Telegraf)
  - ADR-002: Gerenciamento de Certificados (10 anos)
  - ADR-003: Estrutura de Tópicos MQTT (sem conta_id)
  - ADR-004: Protocolo de Renovação OTA
- **[README.md](README.md)**: Índice central de toda documentação do projeto

**Princípio:** Este documento mantém **resumos executivos** das decisões com links para documentação técnica detalhada (Separation of Concerns, Single Source of Truth).

---

## 📊 VISÃO GERAL DO PROJETO

### Objetivo
Desenvolver um sistema SaaS multi-tenant moderno para telemetria e monitoramento de dispositivos IoT, com foco em consumo de recursos (água, energia, gás) através de comunicação MQTT e armazenamento otimizado em TimescaleDB.

### Arquitetura Base
- **Backend:** Django 5.1.6 + Python 3.12.10
- **Database:** PostgreSQL 17 + TimescaleDB 2.17 (porta 5442)
- **IoT:** MQTT Mosquitto + mTLS authentication
- **Frontend:** Bootstrap 5.3.2 + Chart.js
- **Background Tasks:** Celery + Redis
- **Hardware:** ESP32 (C/Arduino) + Raspberry Pi (Python)

### Modelo de Referência
100% baseado na arquitetura validada do projeto **CONSTRUTORA** (multi-tenant, SaaSBaseModel, middleware, context processors, sistema de cenários).

---

## ✅ FASES CONCLUÍDAS (100%)

### 📦 WEEK 1: SETUP E FOUNDATION
**Status:** ✅ **CONCLUÍDO**  
**Data:** 14/02/2026  
**Commits:** `6dc8273`, `6979e6d`, `2b8a9f5`, `6c3d7e3`

#### Entregas
- ✅ Setup inicial do projeto Django 5.1.6
- ✅ Configuração PostgreSQL 17 local (usuário: tsdb_django_d4j7g9)
- ✅ Configuração TimescaleDB (porta 5442)
- ✅ Estrutura de ambientes (.env.dev, .env.prod)
- ✅ Requirements.txt completo (25+ dependências)
- ✅ Gitignore configurado (secrets protegidos)
- ✅ README.md completo (580 linhas)
- ✅ Scripts de automação (setup_database.py, criar_superuser.py)

#### Tecnologias Configuradas
```
- Django 5.1.6, Python 3.12.10
- PostgreSQL 17 + TimescaleDB 2.17 (porta 5442)
- Redis 7.2 (preparado, USE_REDIS=False)
- Paho-MQTT 2.1.0
- Bootstrap 5.3.2 + Bootstrap Icons 1.11.3
- Django-axes, django-environ, django-extensions
```

#### Arquivos Criados
- `prj_tds_new/settings.py` (configuração completa)
- `environments/.env.dev` e `environments/.env.prod`
- `setup_database.py` (automação de setup)
- `criar_superuser.py` (criação de superusuário)
- `requirements.txt` (25+ dependências)
- `README.md` (580 linhas de documentação)

---

### 🔐 WEEK 2: MODELOS BASE E AUTENTICAÇÃO
**Status:** ✅ **CONCLUÍDO**  
**Data:** 14/02/2026  
**Commit:** `b874b7d`

#### Entregas
- ✅ **CustomUser** (AbstractUser) com autenticação por email
- ✅ **Conta** (Tenant) para isolamento multi-tenant
- ✅ **ContaMembership** (User ↔ Conta com roles: ADMIN, EDITOR, VIEWER)
- ✅ **SaaSBaseModel** (abstract base para isolamento)
- ✅ **Mixins de auditoria** (timestamps, created_by)
- ✅ **CustomUserManager** (criação de usuários por email)
- ✅ **Migration 0001_initial** aplicada
- ✅ **Superusuário criado** (admin@tds.com / admin123)

#### Modelos Implementados
```python
tds_new/models/base.py (377 linhas):
- CustomUser: email-based authentication, invite_token
- Conta: tenant com is_active, planos, CNPJ
- ContaMembership: roles com permissions (is_admin, can_edit, can_view)
- SaaSBaseModel: base abstrata com conta FK obrigatória
- Mixins: BaseTimestampMixin, BaseCreatedByMixin, BaseAuditMixin
```

#### Base de Dados
- **3 tabelas criadas:**
  - `tds_new_customuser` (usuários)
  - `tds_new_conta` (organizações/tenants)
  - `tds_new_contamembership` (relacionamento user ↔ conta)
- **29 migrations aplicadas** (incluindo Django built-in)

#### Decisões Arquiteturais
1. ✅ `AUTH_USER_MODEL = 'tds_new.CustomUser'` definido desde o início
2. ✅ Autenticação por email (não por username)
3. ✅ Mixins de auditoria em todos os modelos
4. ✅ SaaSBaseModel garante isolamento multi-tenant

---

### ⚙️ WEEK 3: MIDDLEWARE E CONTEXT PROCESSORS
**Status:** ✅ **CONCLUÍDO**  
**Data:** 14/02/2026  
**Commit:** `76798b9`

#### Entregas
- ✅ **TenantMiddleware** (isolamento automático por conta)
- ✅ **LicenseValidationMiddleware** (validação de conta ativa)
- ✅ **SessionDebugMiddleware** (debug em desenvolvimento)
- ✅ **4 Context Processors** (conta, usuario, session, app_version)
- ✅ **Thread-local storage** (get_current_account)
- ✅ **Configuração em settings.py** (MIDDLEWARE + TEMPLATES)

#### Arquitetura Multi-Tenant
```
┌─────────────────────────────────────────────────────────────┐
│ Request → TenantMiddleware                                   │
│   ↓ Verifica autenticação                                   │
│   ↓ Busca conta ativa na sessão (conta_ativa_id)           │
│   ↓ Valida acesso via ContaMembership                       │
│   ↓ Define request.conta_ativa e request.usuario_conta     │
│   ↓ Armazena em thread-local (get_current_account())       │
│ LicenseValidationMiddleware                                 │
│   ↓ Verifica conta.is_active                                │
│   ↓ TODO: Integrar com shared.assinaturas (Week 8)         │
│ View Execution                                              │
│   ↓ Acessa request.conta_ativa                              │
│   ↓ Queries filtradas automaticamente por conta            │
│ Template Rendering                                          │
│   ↓ Context processors injetam variáveis globais:          │
│     - {{ conta }}, {{ conta_id }}                           │
│     - {{ usuario_admin }}, {{ usuario_pode_editar }}        │
│     - {{ titulo_pagina }}, {{ cenario_nome }}               │
└─────────────────────────────────────────────────────────────┘
```

#### Context Processors Implementados
```python
core/context_processors.py:
1. conta_context: Injeta 'conta' e 'conta_id' nos templates
2. usuario_context: Injeta 'usuario_admin', 'usuario_pode_editar', 'usuario_pode_visualizar'
3. session_context: Injeta 'titulo_pagina', 'cenario_nome', 'menu_nome'
4. app_version: Injeta 'APP_VERSION'
```

#### URLs Isentas
- `/admin/` - Django Admin (sem tenant)
- `/auth/` - Autenticação (login, logout)
- `/static/` - Arquivos estáticos
- `/media/` - Arquivos de mídia

---

### 🎨 WEEK 4-5: SISTEMA DE CENÁRIOS E UI BASE
**Status:** ✅ **CONCLUÍDO**  
**Data:** 14/02/2026  
**Commit:** `9bd1799` (HEAD)

#### Entregas
- ✅ **Sistema de cenários** (8 cenários configurados)
- ✅ **Views de autenticação** (login, logout, select_account, license_expired)
- ✅ **Dashboard inicial** com mocked data
- ✅ **Templates Bootstrap 5.3** (base.html 267 linhas)
- ✅ **Navbar + Sidebar completos** (design moderno)
- ✅ **14 URLs configuradas** (auth + dashboard + cenários)
- ✅ **Constants.py** (Cenarios, StatusDispositivo, TipoAlerta, Permissoes)

#### Arquivos Criados (13 arquivos, 1.699 linhas)
```
tds_new/
├── constants.py (107 linhas)
│   ├── Cenarios (8 cenários)
│   ├── StatusDispositivo (ATIVO, INATIVO, MANUTENCAO, ERRO)
│   ├── TipoAlerta (INFO, WARNING, CRITICAL)
│   └── Permissoes (ADMIN, EDITOR, VIEWER)
│
├── urls.py (58 linhas)
│   ├── Autenticação (4 URLs)
│   ├── Dashboard (2 URLs)
│   └── Cenários (8 URLs)
│
├── views/
│   ├── __init__.py (38 linhas)
│   ├── cenario.py (133 linhas)
│   │   ├── _configurar_cenario() [helper]
│   │   └── 8 funções de cenário
│   ├── auth.py (235 linhas)
│   │   ├── login_view() [multi-tenant]
│   │   ├── select_account_view()
│   │   ├── logout_view()
│   │   ├── license_expired_view()
│   │   └── _get_client_ip() [helper]
│   └── dashboard.py (41 linhas)
│       └── dashboard_view() [com mocked data]
│
└── templates/
    ├── base.html (267 linhas)
    │   ├── Navbar fixa (60px)
    │   ├── Sidebar fixa (250px)
    │   ├── Sistema de mensagens
    │   └── Design responsivo
    ├── auth/
    │   ├── login.html (105 linhas)
    │   ├── select_account.html (92 linhas)
    │   └── license_expired.html (53 linhas)
    └── tds_new/
        └── dashboard.html (145 linhas)
```

#### Cenários Implementados
1. **HOME** → Dashboard principal ✅ Funcional
2. **DISPOSITIVOS** → Gestão de gateways/dispositivos ⏳ Placeholder (Week 6-7)
3. **TELEMETRIA** → Monitor em tempo real ⏳ Placeholder (Week 8-9)
4. **ALERTAS** → Central de alertas ⏳ Placeholder (Week 8-9)
5. **RELATORIOS** → Análises e relatórios ⏳ Placeholder (Week 10)
6. **CONFIGURACOES** → Config do sistema ⏳ Placeholder (Week 11)
7. **CONTA** → Gestão da conta ⏳ Placeholder (Week 11)
8. **USUARIOS** → Gestão de usuários ⏳ Placeholder (Week 11)

#### Design System
- **Bootstrap 5.3.2** + Bootstrap Icons 1.11.3
- **Gradient Navbar:** `#0d6efd → #0a58ca` (azul)
- **Gradient Login:** `#667eea → #764ba2` (roxo)
- **Cards:** Shadow + hover effects
- **Sidebar:** Fixa 250px, dark theme
- **Navbar:** Fixa 60px, gradient
- **Font:** Segoe UI, Tahoma, Geneva, Verdana

---

### 📄 DOCUMENTAÇÃO COMPLETA
**Status:** ✅ **CONCLUÍDO**

#### Arquivos Documentados

**1. README.md (580 linhas)**
- Stack tecnológico completo
- Instruções de instalação (9 steps)
- Comandos úteis de desenvolvimento
- Guia de variáveis de ambiente
- Padrões de Conventional Commits
- Links para docs externas

**2. CHANGELOG.md (1.393 linhas)**
- Log detalhado de todas as 5 semanas
- Tarefas executadas (com código de exemplo)
- Métricas de código criado
- Decisões arquiteturais
- Próximos passos por fase

**3. docs/DIAGRAMA_ER.md (550 linhas)**
- Diagrama Mermaid completo (8 entidades)
- Descrições detalhadas de campos
- Constraints e indexes (unique_together, CRL)
- Arquitetura MQTT completa
- Estratégias de provisionamento
- Gestão de certificados (10 anos + CRL + OTA)
- Comparação TDS Original vs TDS New
- Validações Django (clean methods)

---

---

## 🏗️ DECISÕES ARQUITETURAIS CRÍTICAS

> **📖 Documentação Detalhada:** [architecture/DECISOES.md](architecture/DECISOES.md)

As decisões arquiteturais críticas do projeto estão documentadas no formato ADR (Architectural Decision Records) em `docs/architecture/DECISOES.md`. Abaixo um **resumo executivo** das 4 decisões principais:

### ADR-001: Estratégia de MQTT Consumer
**Decisão:** Implementar Django Consumer com Celery + Paho-MQTT (REJEITADO: Telegraf)  
**Motivo:** Acesso completo ao ORM Django para isolamento multi-tenant, validações de modelo e integração nativa com Celery  
**Impacto:** Weeks 8-9 (implementação completa do consumer)

📄 **[Ver detalhes completos →](architecture/DECISOES.md#adr-001-mqtt-consumer-strategy)**

---

### ADR-002: Gerenciamento de Certificados
**Decisão:** Certificado único permanente com 10 anos de validade (REJEITADO: Hybrid Bootstrap + Operational)  
**Motivo:** Dispositivos offline por anos podem reconectar sem renovação manual  
**Protocolo:** 
- Algoritmo: RSA 2048 bits
- Common Name: MAC address (identificação única)
- Revogação: CRL (Certificate Revocation List)
- Renovação: OTA automática 2 anos antes da expiração

**Impacto:** Weeks 6-7 (modelo CertificadoDevice) + Week 12 (OTA renewal)

📄 **[Ver detalhes completos →](architecture/DECISOES.md#adr-002-certificate-management-strategy)**

---

### ADR-003: Estrutura de Tópicos MQTT
**Decisão:** Dispositivo publica sem conhecimento de `conta_id`  
**Estrutura:** `tds_new/devices/{mac}/telemetry`  
**Motivo:** Segurança (dispositivo não armazena informações sensíveis do tenant) + Simplicidade (backend resolve `conta_id` via lookup de `Gateway.mac`)  
**MQTT ACL:** `write tds_new/devices/%u/telemetry` (onde `%u` = Common Name do certificado = MAC address)

**Impacto:** Weeks 8-9 (implementação do Django Consumer com lookup de conta)

📄 **[Ver detalhes completos →](architecture/DECISOES.md#adr-003-mqtt-topic-structure)**

---

### ADR-004: Protocolo de Renovação OTA de Certificados
**Decisão:** Renovação automática via MQTT com 2 anos de antecedência, distribuição gradual (10 devices/day)  
**Motivo:** Evitar expiração em massa de certificados fabricados juntos  
**Protocolo:**
- Celery Beat (daily 02:00 AM) seleciona 10 devices com expiração ≤ 730 dias
- Publica novo certificado em `tds_new/devices/{mac}/cert_update` com `retain=True`
- Firmware valida, faz backup, testa novo certificado, rollback automático se falhar

**Impacto:** Week 12 (implementação do serviço OTA)

📄 **[Ver detalhes completos →](architecture/DECISOES.md#adr-004-ota-certificate-renewal-protocol)**

---

## 🔵 PRÓXIMA FASE: WEEK 6-7

### 📱 MÓDULO DE DISPOSITIVOS IoT
**Status:** 🔵 **PLANEJAMENTO 100% COMPLETO** | ⏳ **AGUARDANDO EXECUÇÃO**  
**Prazo Estimado:** 3-5 dias  
**Complexidade:** Média

#### Objetivos
1. Implementar modelos Gateway, Dispositivo, LeituraDispositivo, CertificadoDevice
2. Configurar TimescaleDB hypertable
3. Criar CRUD completo para Gateway e Dispositivo
4. Implementar validações de negócio

---

### 📋 Checklist de Implementação (5 dias)

**Dia 1 - Modelagem:**
- [ ] Criar modelos (dispositivos.py, telemetria.py, certificados.py)
- [ ] Atualizar `__init__.py` com exports
- [ ] Gerar e aplicar migrations (`makemigrations`, `migrate`)
- [ ] Executar SQL de TimescaleDB (hypertable + continuous aggregate)

**Dia 2 - Backend Gateway:**
- [ ] Criar forms (GatewayForm, DispositivoForm)
- [ ] Criar views CRUD completas para Gateway

**Dia 3 - Frontend Gateway:**
- [ ] Criar templates Bootstrap 5 (list, form, detail para Gateway)
- [ ] Testar CRUD Gateway (criar, editar, deletar)
- [ ] Validar filtros e paginação

**Dia 4 - Backend + Frontend Dispositivo:**
- [ ] Criar views CRUD para Dispositivo
- [ ] Criar templates (list, form, detail para Dispositivo)
- [ ] Implementar validações condicionais (Modbus)

**Dia 5 - Testes e Finalização:**
- [ ] Testar CRUD Dispositivo completo
- [ ] Atualizar cenário de dispositivos no menu
- [ ] Validar isolamento multi-tenant (Conta A vs Conta B)
- [ ] Commit e push para GitHub (branch `feature/iot-models`)

📄 **Código de implementação detalhado:** [PROVISIONAMENTO_IOT.md - Seção 6](PROVISIONAMENTO_IOT.md#6-modelos-django-iot)

---

## ⏳ ROADMAP FUTURO (Weeks 8+)

> **📖 Detalhes de Implementação:** [PROVISIONAMENTO_IOT.md](PROVISIONAMENTO_IOT.md) e [architecture/DECISOES.md](architecture/DECISOES.md)

### **WEEK 8-9: INTEGRAÇÃO MQTT E TELEMETRIA**
**Prazo Estimado:** 5-7 dias  
**Complexidade:** Alta

#### Entregas
- [ ] Implementar Celery worker MQTT consumer (ver ADR-001)
- [ ] Paho-MQTT client com mTLS authentication
- [ ] Processar payloads JSON e salvar em LeituraDispositivo
- [ ] Atualizar Gateway.last_seen e is_online
- [ ] Dashboard com dados reais (telemetria ao vivo)
- [ ] Testes de integração MQTT → Django → TimescaleDB

📄 **Fluxo de integração completo:** [architecture/INTEGRACAO.md](architecture/INTEGRACAO.md) - Diagrama de sequência end-to-end, código de exemplo Django Consumer, formato de dados, retry strategies  
📄 **Especificação técnica:** [PROVISIONAMENTO_IOT.md - Seção 7 (Consumer MQTT)](PROVISIONAMENTO_IOT.md#7-mqtt-consumer-django)  
📄 **Decisão arquitetural:** [ADR-001 - Django Consumer](architecture/DECISOES.md#adr-001-mqtt-consumer-strategy)

---

### **WEEK 10: SISTEMA DE ALERTAS**
**Prazo Estimado:** 3-4 dias  
**Complexidade:** Média

#### Entregas
- [ ] Modelo Alerta (tipos: INFO, WARNING, CRITICAL)
- [ ] Regras de disparo (valores acima de limites)
- [ ] Notificações (email, dashboard)
- [ ] Histórico de alertas
- [ ] Filtros e busca

---

### **WEEK 11: RELATÓRIOS E GRÁFICOS**
**Prazo Estimado:** 4-5 dias  
**Complexidade:** Média-Alta

#### Entregas
- [ ] Chart.js integration (linha, barra, pizza)
- [ ] Relatórios de consumo (diário, semanal, mensal)
- [ ] Exportação PDF (reportlab)
- [ ] Exportação Excel (openpyxl)
- [ ] Comparativos entre dispositivos
- [ ] Dashboard analítico

---

### **WEEK 12: GESTÃO DE CERTIFICADOS E OTA**
**Prazo Estimado:** 5-6 dias  
**Complexidade:** Alta

#### Entregas
- [ ] Factory scripts (gerar_certificados_lote.py)
- [ ] CRL management (atualizar_crl_broker.py)
- [ ] Integração com Mosquitto (config CRL)
- [ ] Celery Beat task (verificar_certificados_expirando)
- [ ] MQTT publisher para OTA renewal
- [ ] Dashboard de certificados (expiração, revogação)
- [ ] Logs de renovação

📄 **Especificação técnica:** [PROVISIONAMENTO_IOT.md - Seção 5 (Certificados)](PROVISIONAMENTO_IOT.md#5-certificados-x509-e-seguranca)  
📄 **Decisões arquiteturais:**  
- [ADR-002 - Certificados 10 anos](architecture/DECISOES.md#adr-002-certificate-management-strategy)  
- [ADR-004 - Protocolo OTA](architecture/DECISOES.md#adr-004-ota-certificate-renewal-protocol)

---

### **WEEK 13-14: FIRMWARE E PROVISIONAMENTO**
**Prazo Estimado:** 7-10 dias  
**Complexidade:** Muito Alta

#### Entregas - ESP32 Firmware (C/Arduino)
- [ ] BLE provisioning (WiFi credentials)
- [ ] MQTT client com mTLS
- [ ] Certificate validation
- [ ] OTA certificate update
- [ ] Rollback automático
- [ ] Modbus RTU master

#### Entregas - Raspberry Pi Firmware (Python)
- [ ] HTTP provisioning (WiFi credentials)
- [ ] MQTT client com mTLS (Paho)
- [ ] Certificate validation
- [ ] OTA certificate update
- [ ] Rollback automático
- [ ] Modbus RTU master (minimalmodbus)

📄 **Especificação técnica:** [PROVISIONAMENTO_IOT.md - Seção 8 (Firmware)](PROVISIONAMENTO_IOT.md#8-firmware-gateways)

---

### **WEEK 15-16: REFINAMENTOS E POLISH**
**Prazo Estimado:** 5-7 dias  
**Complexidade:** Média

#### Entregas
- [ ] Testes E2E completos (pytest + Selenium)
- [ ] Performance tuning (TimescaleDB queries)
- [ ] Caching com Redis (ativar USE_REDIS=True)
- [ ] Documentação técnica (API, firmware)
- [ ] Documentação de usuário (manual)
- [ ] Deploy em produção (Docker Compose)
- [ ] Monitoramento (Sentry, Prometheus)

---

### **WEEK 17+: FEATURES AVANÇADAS**
**Prazo Estimado:** Contínuo  
**Complexidade:** Variável

#### Backlog
- [ ] Machine Learning (previsão de consumo)
- [ ] Integração com terceiros (WhatsApp API, Telegram Bot)
- [ ] App mobile (React Native)
- [ ] API REST (Django REST Framework)
- [ ] GraphQL (Graphene-Django)
- [ ] WebSockets (Django Channels) para real-time
- [ ] Mapas interativos (Leaflet.js)
- [ ] Billing/Faturamento (integração com assinaturas)

---

## 📈 MÉTRICAS DO PROJETO

### Código Produzido (Weeks 1-5)
```
Total de Arquivos: 30+
Total de Linhas: ~4.000
Commits: 9
Branches: 1 (master)
Pull Requests: 0
```

### Cobertura de Testes
```
Week 1-5: 0% (sem testes ainda)
Week 6-7: Objetivo 30% (testes de modelo)
Week 8+: Objetivo 60% (testes de integração)
```

### Performance (Baseline)
```
Django check: 0 errors, 2 warnings (não-críticos)
Startup time: ~2s
Database queries (dashboard): N/A (mocked data)
```

---

## 🎯 PRÓXIMOS PASSOS IMEDIATOS

### 1️⃣ **IMPLEMENTAR WEEK 6-7**
- Criar modelos Django (dispositivos.py, telemetria.py, certificados.py)
- Gerar e aplicar migrations
- Configurar TimescaleDB (hypertable + continuous aggregate)
- Implementar CRUD completo (forms, views, templates)
- Validar isolamento multi-tenant

📄 **Checklist completo:** Ver seção "WEEK 6-7" acima  
📄 **Código de implementação:** [PROVISIONAMENTO_IOT.md - Seção 6](PROVISIONAMENTO_IOT.md#6-modelos-django-iot)

### 2️⃣ **TESTAR ISOLAMENTO MULTI-TENANT**
- Criar 2 contas diferentes
- Criar gateways em cada conta
- Validar que cada conta vê apenas seus gateways

### 3️⃣ **COMMIT E PUSH**
```bash
git checkout -b feature/iot-models
git add .
git commit -m "feat: implementar Week 6-7 - Módulo de Dispositivos IoT"
git push origin feature/iot-models
```

---

## 📚 RECURSOS E REFERÊNCIAS

### Documentação do Projeto
- [README.md](../README.md) - Guia completo de instalação
- [CHANGELOG.md](../CHANGELOG.md) - Histórico detalhado de mudanças
- [DIAGRAMA_ER.md](DIAGRAMA_ER.md) - Arquitetura e modelos

### Documentação Externa
- [Django 5.1 Docs](https://docs.djangoproject.com/en/5.1/)
- [TimescaleDB Docs](https://docs.timescale.com/)
- [MQTT Protocol](https://mqtt.org/mqtt-specification/)
- [Paho MQTT Python](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php)
- [Bootstrap 5.3 Docs](https://getbootstrap.com/docs/5.3/)

### Repositórios de Referência
- [server-app-construtora](https://github.com/Miltoneo/server-app-construtora) - Arquitetura base
- [server-app-tds](https://github.com/Miltoneo/server-app-tds) - TDS legado (análise)

---

## 📝 NOTAS DE DOCUMENTAÇÃO

Este arquivo segue o princípio de **Separation of Concerns (SoC)** implementado em 18/02/2026:

- **ROADMAP.md** (este arquivo): Planejamento, cronograma e decisões de alto nível
- **[PROVISIONAMENTO_IOT.md](PROVISIONAMENTO_IOT.md)**: Especificações técnicas operacionais e código de implementação
- **[architecture/DECISOES.md](architecture/DECISOES.md)**: ADRs (Architectural Decision Records) detalhados
- **[README.md](README.md)**: Índice central de navegação de toda documentação

> ⚠️ **Importante:** As seções de código técnico detalhado neste documento (modelos Python, SQL, templates Django) estão mantidas para conveniência durante desenvolvimento, mas a **fonte oficial** (Single Source of Truth) está sempre nos documentos especializados listados acima.

---

**Última atualização:** 18/02/2026  
**Versão do Documento:** 2.0  
**Autor:** Sistema TDS New - Roadmap Completo com SoC
