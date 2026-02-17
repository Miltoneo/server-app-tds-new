# 📊 ROADMAP - Status Atualizado do Admin Sistema

**Projeto:** TDS New - Sistema de Telemetria e Monitoramento IoT  
**Data de Atualização:** 17/02/2026  
**Objetivo:** Interface administrativa completa com segregação multi-tenant

---

## 🎯 VISÃO GERAL DO PROGRESSO

```
WEEK 8  ████████████████████ 100% ✅ CONCLUÍDA
WEEK 9  ████████░░░░░░░░░░░░  40% 🔄 EM ANDAMENTO
WEEK 10 ░░░░░░░░░░░░░░░░░░░░   0% 📋 PLANEJADA
WEEK 11 ░░░░░░░░░░░░░░░░░░░░   0% 📋 PLANEJADA
```

**Progresso Geral:** 3 de 12 fases implementadas (25%)

---

## ✅ WEEK 8 - CONCLUÍDA (17/02/2026)

### 📊 Resumo
Implementação completa da infraestrutura administrativa com segregação de contexto multi-tenant.

### 🎯 Entregas
| # | Funcionalidade | Status | Arquivo Principal |
|---|----------------|--------|-------------------|
| 1 | **Dashboard Global Administrativo** | ✅ Concluído | `views/admin/dashboard.py` |
| 2 | **Lista Global de Certificados** | ✅ Concluído | `views/admin/provisionamento.py` |
| 3 | **SuperAdminMiddleware** | ✅ Concluído | `middleware.py` |
| 4 | **Template Base Admin** | ✅ Concluído | `templates/admin_sistema/base_admin.html` |

### 📈 Métricas Implementadas
- ✅ Total de contas ativas e com gateways
- ✅ Gateways (online/offline/nunca conectados)
- ✅ Dispositivos (ativos/manutenção)
- ✅ Certificados (válidos/expirados/revogados)
- ✅ Top 5 contas com mais gateways
- ✅ Atividade recente (últimos 7 dias)
- ✅ Total de usuários e usuários admin

### 🔐 Controle de Acesso
- ✅ Proteção via `@staff_member_required` e `UserPassesTestMixin`
- ✅ Middleware bloqueando não-staff de acessar `/admin-sistema/*`
- ✅ Redirecionamento inteligente (login ou dashboard normal)

**Commit:** `3d0a84b`  
**Documentação:** [WEEK8_CONCLUIDA.md](./WEEK8_CONCLUIDA.md)

---

## 🔄 WEEK 9 - EM ANDAMENTO (40% Concluído)

### ✅ Fase 1: Alocação de Gateways - CONCLUÍDA (17/02/2026)

**Status:** ✅ Implementada e Validada  
**Prioridade:** 🔴 ALTA (Concluída)

#### 📋 Entregas Realizadas
| # | Item | Status | Observações |
|---|------|--------|-------------|
| 1 | **AlocarGatewayForm** | ✅ Concluído | Seleção de conta + checkbox transferência |
| 2 | **alocar_gateway_view** | ✅ Concluído | Transação atômica (gateway + cert + devices) |
| 3 | **alocar_gateway_por_certificado_view** | ✅ Concluído | Ponto de entrada unificado |
| 4 | **Template alocar_gateway.html** | ✅ Concluído | Interface completa com 6 seções |
| 5 | **Botão "Alocar" em certificados_list.html** | ✅ Concluído | Sempre visível, sem lógica condicional |
| 6 | **TenantMiddleware isenção** | ✅ Concluído | `/admin-sistema/` isento de validação de conta |
| 7 | **Documentação e testes** | ✅ Concluído | WEEK9_FASE1_CONCLUIDA.md + guia de testes |

#### 🎯 Funcionalidades Implementadas
- ✅ Alocação de gateway órfão para conta
- ✅ Realocação de gateway entre contas
- ✅ Transferência automática de dispositivos vinculados
- ✅ Atualização sincronizada de certificado X.509
- ✅ Interface sempre visível (sem lógica condicional)
- ✅ Tratamento de estado vazio (gateway não encontrado)

**Commit:** `cb92b27`  
**Documentação:** [WEEK9_FASE1_CONCLUIDA.md](./WEEK9_FASE1_CONCLUIDA.md)  
**Guia de Testes:** [GUIA_TESTE_ALOCACAO.md](../GUIA_TESTE_ALOCACAO.md)

---

### ⏸️ Fase 2: Importação em Lote (CSV) - A IMPLEMENTAR

**Status:** ⏸️ Não Implementada  
**Prioridade:** 🟡 **BAIXA** (Marcada para implementação futura)

#### 📋 Escopo Planejado (NÃO IMPLEMENTADO)
| # | Item | Status | Observações |
|---|------|--------|-------------|
| 1 | **ImportarGatewaysCSVForm** | ⏸️ A implementar | Upload + validação de CSV |
| 2 | **ImportarGatewaysCSVView** | ⏸️ A implementar | Processamento linha a linha |
| 3 | **Template importar_csv.html** | ⏸️ A implementar | Interface de upload + resultados |
| 4 | **Validação de CSV** | ⏸️ A implementar | Estrutura, MAC único, encoding |
| 5 | **Geração de certificados em lote** | ⏸️ A implementar | Criar cert para cada gateway |
| 6 | **URL admin-sistema/provisionamento/importar-csv/** | ⏸️ A implementar | Rota de acesso |
| 7 | **Menu "Importar CSV"** | ⏸️ A implementar | Link em sidebar admin |

#### 🎯 Funcionalidades Planejadas (NÃO IMPLEMENTADAS)
- ⏸️ Upload de arquivo CSV via formulário
- ⏸️ Validação de formato (colunas obrigatórias)
- ⏸️ Validação de dados (MAC único, conta válida)
- ⏸️ Criação de gateways em lote (transação atômica)
- ⏸️ Geração automática de certificados X.509
- ⏸️ Relatório de importação (sucesso/erros)
- ⏸️ Download de template CSV de exemplo

**Justificativa de Baixa Prioridade:**
- Alocação manual (Fase 1) já atende necessidades operacionais
- CSV bulk import é otimização para escala futura
- Foco deve estar em funcionalidades de segurança (revogação)

**Estimativa de Esforço:** 1-2 dias de desenvolvimento  
**Dependências:** Nenhuma (independente das outras fases)

---

### 📋 Fase 3: Revogação de Certificados - PENDENTE

**Status:** 📋 Planejada  
**Prioridade:** 🔴 **ALTA** (Segurança crítica)

#### 📋 Escopo Planejado
| # | Item | Status | Prioridade |
|---|------|--------|-----------|
| 1 | **RevogarCertificadoForm** | 📋 Pendente | 🔴 Alta |
| 2 | **revogar_certificado_view** | 📋 Pendente | 🔴 Alta |
| 3 | **Template confirmação de revogação** | 📋 Pendente | 🔴 Alta |
| 4 | **Atualização de CertificadoDevice** | 📋 Pendente | 🔴 Alta |
| 5 | **Geração de CRL (Certificate Revocation List)** | 📋 Pendente | 🔴 Alta |
| 6 | **Integração com Mosquitto** | 📋 Pendente | 🔴 Alta |
| 7 | **Teste de bloqueio MQTT** | 📋 Pendente | 🔴 Alta |

#### 🎯 Funcionalidades Planejadas
- 🔴 Revogar certificado X.509 existente
- 🔴 Marcar como revogado (is_revoked=True, revoked_at, revoke_reason)
- 🔴 Bloquear conexão MQTT do gateway revogado
- 🔴 Exportar CRL em formato PEM
- 🔴 Configurar Mosquitto para verificar CRL
- 🔴 Auditoria de revogações

**Justificativa de Alta Prioridade:**
- Requisito de segurança crítico
- Necessário para compliance e governança
- Permite desativar gateways comprometidos
- Evita acesso não autorizado ao broker MQTT

**Estimativa de Esforço:** 2-3 dias de desenvolvimento + 1 dia de integração Mosquitto  
**Dependências:** Fase 1 (Alocação) concluída ✅

---

### 📋 Fase 4: Auditoria de Operações - PENDENTE

**Status:** 📋 Planejada  
**Prioridade:** 🟠 **MÉDIA** (Compliance e governança)

#### 📋 Escopo Planejado
| # | Item | Status | Prioridade |
|---|------|--------|-----------|
| 1 | **LogsSistemaView** | 📋 Pendente | 🟠 Média |
| 2 | **Template logs_sistema.html** | 📋 Pendente | 🟠 Média |
| 3 | **Integração com LogEntry** | 📋 Pendente | 🟠 Média |
| 4 | **Filtros de busca** | 📋 Pendente | 🟠 Média |
| 5 | **Exportação de logs** | 📋 Pendente | 🟠 Média |
| 6 | **Auditoria de alocações** | 📋 Pendente | 🟠 Média |
| 7 | **Auditoria de revogações** | 📋 Pendente | 🟠 Média |

#### 🎯 Funcionalidades Planejadas
- 📋 Visualização de logs administrativos
- 📋 Filtros: usuário, ação, data, tipo de objeto
- 📋 Registro de alocação de gateways
- 📋 Registro de emissão/revogação de certificados
- 📋 Registro de importações CSV
- 📋 Exportação de logs (CSV/PDF)
- 📋 Paginação e busca avançada

**Estimativa de Esforço:** 1-2 dias de desenvolvimento  
**Dependências:** Fases 1, 2 e 3 (registrar eventos de cada fase)

---

## 📋 WEEK 10 - PLANEJADA

### Fase 5: Auditoria e Compliance

**Status:** 📋 Planejada  
**Prioridade:** 🟡 **BAIXA** (Após Week 9 completa)

#### 📋 Escopo Planejado
| # | Item | Status | Prioridade |
|---|------|--------|-----------|
| 1 | **CertificadosRevogadosView** | 📋 Pendente | 🟡 Baixa |
| 2 | **exportar_crl_view** | 📋 Pendente | 🟡 Baixa |
| 3 | **Template certificados_revogados.html** | 📋 Pendente | 🟡 Baixa |
| 4 | **Documentação de CRL para Mosquitto** | 📋 Pendente | 🟡 Baixa |

#### 🎯 Funcionalidades Planejadas
- 📋 Lista dedicada de certificados revogados
- 📋 Download de CRL em formato PEM
- 📋 Estatísticas de revogações
- 📋 Documentação de integração com broker

**Estimativa de Esforço:** 1 dia  
**Dependências:** Week 9 Fase 3 (Revogação) concluída

---

## 📋 WEEK 11 - PLANEJADA

### Fase 6: Ferramentas de Manutenção

**Status:** 📋 Planejada  
**Prioridade:** 🟡 **BAIXA** (Otimização futura)

#### 📋 Escopo Planejado
| # | Item | Status | Prioridade |
|---|------|--------|-----------|
| 1 | **FirmwareUpdateView** | 📋 Pendente | 🟡 Baixa |
| 2 | **Upload de firmware** | 📋 Pendente | 🟡 Baixa |
| 3 | **Sistema de versionamento** | 📋 Pendente | 🟡 Baixa |
| 4 | **Notificação para gateways (MQTT)** | 📋 Pendente | 🟡 Baixa |
| 5 | **Limpeza de dados históricos** | 📋 Pendente | 🟡 Baixa |
| 6 | **Configuração de retenção** | 📋 Pendente | 🟡 Baixa |

#### 🎯 Funcionalidades Planejadas
- 📋 Upload de firmware para gateways (OTA)
- 📋 Versionamento de firmware
- 📋 Rollback de versões
- 📋 Notificação via MQTT para atualização
- 📋 Limpeza de leituras antigas (TimescaleDB)
- 📋 Exportação antes da exclusão

**Estimativa de Esforço:** 3-5 dias  
**Dependências:** Infraestrutura MQTT estável

---

## 📊 RESUMO DE PRIORIDADES

### 🔴 Alta Prioridade (Próximos Passos)
| Fase | Descrição | Estimativa | Status |
|------|-----------|------------|--------|
| **Week 9 - Fase 3** | Revogação de Certificados | 2-3 dias | 📋 Próxima a implementar |
| **Week 9 - Fase 4** | Auditoria de Operações | 1-2 dias | 📋 Após Fase 3 |

### 🟠 Média Prioridade
| Fase | Descrição | Estimativa | Status |
|------|-----------|------------|--------|
| **Week 10** | Auditoria e Compliance | 1 dia | 📋 Planejada |

### 🟡 Baixa Prioridade (Backlog)
| Fase | Descrição | Estimativa | Status |
|------|-----------|------------|--------|
| **Week 9 - Fase 2** | Importação CSV | 1-2 dias | ⏸️ A implementar |
| **Week 11** | Ferramentas de Manutenção (OTA) | 3-5 dias | 📋 Planejada |

---

## 🎯 PLANO DE AÇÃO SUGERIDO

### Próximos 7 Dias
1. ✅ **Week 9 - Fase 1:** Alocação de Gateways (CONCLUÍDA)
2. 🔴 **Week 9 - Fase 3:** Implementar revogação de certificados
3. 🔴 **Week 9 - Fase 4:** Implementar auditoria de operações

### Próximos 14-30 Dias
4. 🟠 **Week 10:** Implementar exportação de CRL
5. 🟡 **Week 9 - Fase 2:** Implementar importação CSV (se necessário)

### Médio Prazo (1-3 meses)
6. 🟡 **Week 11:** Implementar OTA firmware updates
7. 🟡 **Week 11:** Implementar limpeza de dados históricos

---

## 📈 MÉTRICAS DE PROGRESSO

### Por Funcionalidade
```
Dashboard Admin              ████████████████████ 100% ✅
Lista de Certificados        ████████████████████ 100% ✅
SuperAdminMiddleware         ████████████████████ 100% ✅
Template Base Admin          ████████████████████ 100% ✅
Alocação de Gateways         ████████████████████ 100% ✅
CSV Import                   ░░░░░░░░░░░░░░░░░░░░   0% ⏸️
Revogação de Certificados    ░░░░░░░░░░░░░░░░░░░░   0% 📋
Auditoria                    ░░░░░░░░░░░░░░░░░░░░   0% 📋
CRL Export                   ░░░░░░░░░░░░░░░░░░░░   0% 📋
OTA Updates                  ░░░░░░░░░░░░░░░░░░░░   0% 📋
```

### Por Week
- **Week 8:** 100% ✅ (4/4 entregas concluídas)
- **Week 9:** 40% 🔄 (1/4 fases concluídas)
  - Fase 1: ✅ Concluído
  - Fase 2: ⏸️ Baixa prioridade
  - Fase 3: 📋 Alta prioridade
  - Fase 4: 📋 Média prioridade
- **Week 10:** 0% 📋 (0/1 fase iniciada)
- **Week 11:** 0% 📋 (0/1 fase iniciada)

---

## 🔗 REFERÊNCIAS

### Documentação Implementada
- [ROADMAP_ADMIN_SISTEMA.md](./ROADMAP_ADMIN_SISTEMA.md) - Roadmap completo
- [WEEK8_CONCLUIDA.md](./WEEK8_CONCLUIDA.md) - Detalhes Week 8
- [WEEK9_FASE1_CONCLUIDA.md](./WEEK9_FASE1_CONCLUIDA.md) - Detalhes Week 9 Fase 1
- [GUIA_TESTE_ALOCACAO.md](../GUIA_TESTE_ALOCACAO.md) - Guia de testes de alocação

### Arquivos Principais
```
tds_new/
├── middleware.py                           # SuperAdminMiddleware + TenantMiddleware
├── constants.py                            # ADMIN_SISTEMA + SUPER_ADMIN
├── views/admin/
│   ├── dashboard.py                       # Dashboard global ✅
│   └── provisionamento.py                 # Certificados + Alocação ✅
├── forms/
│   └── provisionamento.py                 # AlocarGatewayForm ✅
├── templates/admin_sistema/
│   ├── base_admin.html                    # Layout base admin ✅
│   ├── dashboard.html                     # Dashboard template ✅
│   └── provisionamento/
│       ├── certificados_list.html         # Lista de certificados ✅
│       └── alocar_gateway.html            # Interface de alocação ✅
└── urls.py                                # Rotas administrativas ✅
```

---

## 📅 HISTÓRICO DE ATUALIZAÇÕES

| Data | Versão | Mudanças |
|------|--------|----------|
| 17/02/2026 | 1.2 | Fase 2 marcada como baixa prioridade |
| 17/02/2026 | 1.1 | Week 9 Fase 1 concluída e documentada |
| 17/02/2026 | 1.0 | Week 8 concluída e documentada |

---

**Última atualização:** 17/02/2026  
**Responsável:** Equipe TDS New  
**Próxima revisão:** Após conclusão de Week 9 Fase 3 (Revogação)

---

## 🎯 CONCLUSÃO

### O Que Temos Hoje ✅
- ✅ Infraestrutura administrativa segregada e segura
- ✅ Dashboard global com métricas consolidadas
- ✅ Gerenciamento de certificados (visualização e alocação)
- ✅ Sistema de alocação de gateways entre contas
- ✅ Middleware de proteção robusto

### O Que Falta (Alta Prioridade) 🔴
- 🔴 Revogação de certificados X.509 (segurança crítica)
- 🔴 Auditoria de operações administrativas (compliance)

### O Que Falta (Baixa Prioridade) 🟡
- 🟡 Importação em lote via CSV (otimização operacional)
- 🟡 Exportação de CRL (melhorias de auditoria)
- 🟡 OTA firmware updates (roadmap futuro)

**Recomendação:** Focar em Week 9 Fases 3 e 4 (revogação + auditoria) antes de implementar otimizações de baixa prioridade.
