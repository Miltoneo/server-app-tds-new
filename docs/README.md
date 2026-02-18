# 📚 Documentação - Sistema TDS New

**Projeto:** TDS New - Sistema de Telemetria e Monitoramento IoT  
**Repositório:** [Miltoneo/server-app-tds-new](https://github.com/Miltoneo/server-app-tds-new)  
**Última Atualização:** 18/02/2026  
**Versão:** 1.0

Bem-vindo à documentação do sistema TDS New. Esta página serve como índice central para toda a documentação técnica do projeto.

---

## 🗺️ GUIA DE LEITURA

### Para Desenvolvedores Backend
1. **Início:** [../README.md](../README.md) - Instalação e setup local
2. **Planejamento:** [ROADMAP.md](ROADMAP.md) - Cronograma de 16 semanas
3. **⭐ IMPLEMENTAÇÃO IMEDIATA:** [PLANO_IMPLEMENTACAO_TELEMETRIA.md](PLANO_IMPLEMENTACAO_TELEMETRIA.md) - Plano executável telemetria (3-17 dias)
4. **Diagramas:** [DIAGRAMA_ER.md](DIAGRAMA_ER.md) - Entidades e relacionamentos
5. **Integração:** [architecture/INTEGRACAO.md](architecture/INTEGRACAO.md) - Fluxo end-to-end entre camadas
6. **Decisões:** [architecture/DECISOES.md](architecture/DECISOES.md) - Architectural Decision Records (ADRs)

### Para DevOps/Operações
1. **Provisionamento:** [PROVISIONAMENTO_IOT.md](PROVISIONAMENTO_IOT.md) - Estratégias multi-plataforma
2. **Infraestrutura:** Consultar repositório [project-iot](https://github.com/Miltoneo/project-iot)
3. **Deploy:** [../README_deploy.md](../README_deploy.md) (quando disponível)

### Para Engenheiros de Firmware
1. **ESP32/Arduino:** Consultar repositório [placas](https://github.com/Miltoneo/placas)
2. **Provisionamento:** [PROVISIONAMENTO_IOT.md](PROVISIONAMENTO_IOT.md) - Implementações ESP32/RPi

---

## 📄 DOCUMENTOS PRINCIPAIS

### 📅 Planejamento e Roadmap

#### [ROADMAP.md](ROADMAP.md) 
**Público:** Equipe de Desenvolvimento  
**Conteúdo:** Cronograma completo de 16 semanas, entregas, checklists, métricas  
**Tamanho:** 1.200+ linhas  
**Status:** 🟢 Weeks 1-5 concluídas | 🔵 Week 6-7 em andamento

**Seções principais:**
- Weeks 1-16: Cronograma detalhado
- Decisões arquiteturais críticas
- Checklists de implementação
- Métricas de código produzido

#### [PLANO_IMPLEMENTACAO_TELEMETRIA.md](PLANO_IMPLEMENTACAO_TELEMETRIA.md) ⭐
**Público:** Equipe de Desenvolvimento, Product Owner  
**Conteúdo:** Plano executável simplificado para implementação de telemetria  
**Tamanho:** 1.100+ linhas  
**Status:** 🟢 Pronto para executar (18/02/2026)

**Seções principais:**
- Resumo Executivo: Decisão arquitetural (ADR-005 - MQTT Consumer no backend)
- Visão Geral: Estado atual (85% pronto, 15% pendente)
- 6 Fases Detalhadas: Fase 1-6 com duração estimada
- 3 Opções de Implementação:
  - **MVP Mínimo:** 3 dias (18-21/02) - Fases 1+2+4 - RECOMENDADO ✅
  - **MVP Completo:** 7 dias - Adiciona Celery (Fase 3)
  - **Produção:** 17 dias - Adiciona mTLS (Fase 5) + Testes (Fase 6)
- Cronograma Hora-a-Hora: Day 1-3 detalhado (09:00-18:00)
- Critérios de Sucesso: Técnicos (<500ms latency) + Negócio (demo stakeholder)
- Próximos Passos IMEDIATOS: Comandos copy-paste para HOJE (1h)
- Referências: VIABILIDADE, ESTRUTURA, ARQUITETURA, ADR-005, INTEGRACAO

**Quando usar este documento:**
- 🎯 **Antes de iniciar:** Para entender escopo e timeline (3/7/17 dias)
- 🎯 **Durante execução:** Para seguir cronograma hora-a-hora do MVP Mínimo
- 🎯 **Tomada de decisão:** Para escolher entre 3 opções de implementação
- 🎯 **Validação:** Para verificar critérios de sucesso (latency, persistência, demo)

---

### 🏛️ Arquitetura e Design

#### [DIAGRAMA_ER.md](DIAGRAMA_ER.md)
**Público:** Desenvolvedores Backend  
**Conteúdo:** Diagrama Mermaid completo, 8 entidades, constraints  
**Tamanho:** 550 linhas  
**Status:** ✅ Completo

**Entidades principais:**
- Conta, Empresa, Membership
- Gateway, Dispositivo, CertificadoDevice
- LeituraDispositivo (TimescaleDB hypertable)
- ConsumoMensal (continuous aggregate)

#### [architecture/DECISOES.md](architecture/DECISOES.md)
**Público:** Arquitetos, Tech Leads  
**Conteúdo:** Architectural Decision Records (ADRs)  
**Status:** 🆕 Novo (18/02/2026)

**ADRs documentados:**
- ADR-001: MQTT Consumer Strategy (Django vs Telegraf)
- ADR-002: Certificate Management Strategy (10 anos vs bootstrap)
- ADR-003: Topic MQTT sem conta_id (segurança multi-tenant)
- ADR-004: OTA Certificate Renewal Protocol (distribuição gradual)
- ADR-005: MQTT Consumer Location (Backend vs Infraestrutura vs Híbrido) ⭐ NEW

#### [architecture/INTEGRACAO.md](architecture/INTEGRACAO.md)
**Público:** Desenvolvedores Full-Stack, Arquitetos  
**Conteúdo:** Fluxo end-to-end de integração entre camadas  
**Tamanho:** 1.000+ linhas  
**Status:** 🆕 Novo (18/02/2026)

**Seções principais:**
- Diagrama de sequência completo (20 etapas)
- Camada 1: Firmware (Dispositivo → MQTT)
- Camada 2: Broker MQTT (mTLS Authentication)
- Camada 3: Django Consumer (MQTT → Backend)
- Camada 4: TimescaleDB (Hypertable + Continuous Aggregate)
- Camada 5: Dashboard (Query + Visualização Chart.js)
- Formato de dados por camada (transformações)
- Tratamento de erros e retry strategies
- Métricas de performance e latência (~300ms end-to-end)
- Monitoramento e observabilidade

---

### ⚙️ Operações e Provisionamento

#### [PROVISIONAMENTO_IOT.md](PROVISIONAMENTO_IOT.md)
**Público:** DevOps, Engenharia de Campo, Firmware  
**Conteúdo:** Estratégias de provisionamento multi-plataforma  
**Tamanho:** 580+ linhas  
**Status:** ✅ v1.1 (atualizado 18/02/2026)

**Seções principais:**
- 3 estratégias de provisionamento (Manual, API REST, Zero-Touch)
- Fluxo de certificação mTLS (CA, CRL, X.509)
- Implementações completas (ESP32 C++, Raspberry Pi Python)
- Configuração Mosquitto (broker MQTT)
- Segurança (Secure Boot, Flash Encryption)
- Troubleshooting (3 problemas comuns)

---

## 🔄 FLUXO DE NAVEGAÇÃO ENTRE DOCUMENTOS

```
┌─────────────────────────────────────────────────────────────┐
│                     INÍCIO DO PROJETO                        │
│                    ├─ README.md (raiz)                       │
│                    └─ docs/README.md (este arquivo)          │
└────────────────────────┬────────────────────────────────────┘
                         ↓
         ┌───────────────┴────────────────┐
         ↓                                ↓
┌────────────────────┐          ┌─────────────────────────┐
│  PLANEJAMENTO      │          │  ARQUITETURA            │
│  ├─ ROADMAP.md     │←────────→│  ├─ DIAGRAMA_ER.md      │
│  └─ PLANO_IMPL ⭐  │          │  ├─ INTEGRACAO.md       │
│  (O QUE + QUANDO)  │          │  └─ DECISOES.md (ADR-5) │
└────────┬───────────┘          └─────────┬───────────────┘
         │                                 │
         └────────────┬────────────────────┘
                      ↓
         ┌────────────────────────┐
         │  IMPLEMENTAÇÃO         │
         │  PROVISIONAMENTO_IOT   │
         │  (COMO + OPERAÇÕES)    │
         └────────────────────────┘
```

### Exemplo de Fluxo de Leitura:

**Cenário 1: Novo Desenvolvedor Backend**
```
README.md (raiz) → docs/README.md → ROADMAP.md → DIAGRAMA_ER.md → INTEGRACAO.md
```

**Cenário 1b: Implementação Imediata de Telemetria ⭐**
```
docs/README.md → PLANO_IMPLEMENTACAO_TELEMETRIA.md → Executar Fase 1 (HOJE)
                      ↓
               VIABILIDADE_TELEMETRIA.md (análise detalhada)
                      ↓
               ADR-005 (decisão arquitetural)
                      ↓
               INTEGRACAO.md (código pronto)
```

**Cenário 2: DevOps configurando Provisionamento**
```
README.md (raiz) → docs/README.md → PROVISIONAMENTO_IOT.md
```

**Cenário 3: Implementando MQTT Consumer (Week 8-9)**
```
ROADMAP.md (Week 8) → INTEGRACAO.md (Camada 3) → DECISOES.md (ADR-001) → PROVISIONAMENTO_IOT.md (Broker config)
```

**Cenário 3: Entender Decisão Arquitetural**
```
ROADMAP.md (decisão citada) → architecture/DECISOES.md (ADR completo) → PROVISIONAMENTO_IOT.md (implementação)
```

---

## 📐 PRINCÍPIOS DE DOCUMENTAÇÃO

Este projeto segue os seguintes princípios para manter a documentação organizada e atualizada:

### 1. Separation of Concerns (SoC)
- **ROADMAP.md** → Planejamento (O QUE e QUANDO)
- **PROVISIONAMENTO_IOT.md** → Operações (COMO)
- **architecture/DECISOES.md** → Decisões (POR QUÊ)

### 2. Single Source of Truth (SSOT)
- Cada informação técnica existe em **UM ÚNICO** local
- Cross-references entre documentos (não duplicação)

### 3. Audience-Specific
- Desenvolvedores → ROADMAP.md
- DevOps/Ops → PROVISIONAMENTO_IOT.md
- Arquitetos → architecture/DECISOES.md

### 4. Living Documentation
- Documentos evoluem com o código
- Commits devem atualizar documentação relevante

---

## ✅ CHECKLIST DE DOCUMENTAÇÃO

Antes de fechar uma tarefa/PR, valide que a documentação está atualizada:

### Para Features/Bugs
- [ ] **ROADMAP.md**: Tarefa marcada como concluída?
- [ ] **CHANGELOG.md**: Commit detalhado adicionado? (quando disponível)
- [ ] **README.md (raiz)**: Seção relevante atualizada?

### Para Decisões Arquiteturais
- [ ] **architecture/DECISOES.md**: ADR criado com contexto, decisão e consequências?
- [ ] **ROADMAP.md**: Cross-reference para ADR adicionado?

### Para Mudanças Operacionais
- [ ] **PROVISIONAMENTO_IOT.md**: Seção relevante atualizada?
- [ ] **README.md (raiz)**: Instruções de setup atualizadas?

### Para Mudanças de Modelo/Schema
- [ ] **DIAGRAMA_ER.md**: Diagrama Mermaid atualizado?
- [ ] **ROADMAP.md**: Decisão de modelagem documentada?

---

## 🆕 NOVOS DOCUMENTOS (Planejados)

Os seguintes documentos serão criados conforme o projeto evolui:

### Week 8-10
- [ ] `architecture/MQTT_INTEGRATION.md` - Integração MQTT completa
- [ ] `architecture/MODELOS_DJANGO.md` - Entidades Django detalhadas

### Week 11-14
- [ ] `operations/TROUBLESHOOTING.md` - Guia completo de problemas
- [ ] `operations/MONITORING.md` - Métricas, alertas, Grafana

### Week 15-16
- [ ] `firmware/ESP32_GUIDE.md` - Desenvolvimento ESP32/Arduino
- [ ] `firmware/RPI_GUIDE.md` - Desenvolvimento Raspberry Pi
- [ ] `api/API_REFERENCE.md` - Documentação Swagger/OpenAPI

---

## 📞 SUPORTE E CONTRIBUIÇÃO

### Reportar Problemas na Documentação
- Abra uma issue no GitHub com label `documentation`
- Descreva qual documento está desatualizado/incorreto
- Sugira a correção (se possível)

### Contribuir com Documentação
1. Siga os princípios SoC, SSOT e Audience-Specific
2. Use cross-references em vez de duplicar conteúdo
3. Mantenha exemplos de código funcionais e testados
4. Adicione seção no checklist de documentação

---

## 📊 MÉTRICAS DE DOCUMENTAÇÃO

| Documento | Linhas | Última Atualização | Status |
|-----------|--------|-------------------|--------|
| README.md (raiz) | ~150 | 15/02/2026 | ✅ Atualizado |
| docs/README.md | ~200 | 18/02/2026 | 🆕 Novo |
| ROADMAP.md | ~1.200 | 18/02/2026 | ✅ Refatorado |
| DIAGRAMA_ER.md | ~550 | 15/02/2026 | ✅ Completo |
| PROVISIONAMENTO_IOT.md | ~580 | 18/02/2026 | ✅ v1.1 |
| architecture/DECISOES.md | ~300 | 18/02/2026 | 🆕 Novo |

**Total:** ~3.000 linhas de documentação técnica

---

## 🔗 LINKS EXTERNOS

### Repositórios Relacionados
- **[project-iot](https://github.com/Miltoneo/project-iot)** - Infraestrutura IoT (MQTT, TimescaleDB, Telegraf)
- **[placas](https://github.com/Miltoneo/placas)** - Firmware ESP32/Arduino

### Documentação de Referência
- **Django 5.1:** https://docs.djangoproject.com/en/5.1/
- **TimescaleDB 2.17:** https://docs.timescale.com/
- **MQTT Spec:** https://mqtt.org/mqtt-specification/
- **Mosquitto mTLS:** https://mosquitto.org/man/mosquitto-tls-7.html
- **ESP32 Arduino:** https://docs.espressif.com/projects/arduino-esp32/

---

**Última atualização:** 18/02/2026  
**Responsável:** Equipe TDS New  
**Versão:** 1.0  
**Status:** 🟢 Ativo
