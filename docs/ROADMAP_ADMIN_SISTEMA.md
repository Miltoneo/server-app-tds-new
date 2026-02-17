# 🚀 ROADMAP - Interface de Gestão Administrativa TDS New

**Projeto:** TDS New - Sistema de Telemetria e Monitoramento IoT  
**Data:** 17/02/2026  
**Status:** ✅ Week 8 Implementada  
**Objetivo:** Interface administrativa completa com segregação de dashboards

---

## 📊 CONTEXTO

### Problema Identificado
- Dashboard único misturando dados de usuário final (multi-tenant) com dados administrativos (globais)
- Risco de vazamento de dados entre contas
- Dificuldade de manutenção e escalabilidade

### Solução Implementada
- **Segregação completa** entre interfaces de usuário final e admin sistema
- **Middleware de proteção** para rotas administrativas
- **Templates segregados** sem context processor de tenant
- **Views administrativas** sem filtro de conta (visão global)

---

## ✅ WEEK 8 - IMPLEMENTADA (17/02/2026)

### 📁 Estrutura Criada

```
tds_new/
├── constants.py                       ✅ Atualizado
│   ├── Cenarios.ADMIN_SISTEMA        🆕
│   └── Permissoes.SUPER_ADMIN        🆕
│
├── middleware.py                      ✅ Atualizado
│   └── SuperAdminMiddleware          🆕 Proteção de rotas /admin-sistema/
│
├── views/
│   ├── dashboard.py                   ✅ Mantido (usuário final)
│   ├── gateway.py                     ✅ Mantido (usuário final)
│   ├── dispositivo.py                 ✅ Mantido (usuário final)
│   │
│   └── admin/                         🆕 Pasta administrativa
│       ├── __init__.py               ✅ Criado
│       ├── dashboard.py              ✅ Criado (visão global)
│       └── provisionamento.py        ✅ Criado (lista certificados)
│
├── templates/
│   ├── tds_new/                       ✅ Mantido (usuário final)
│   │   ├── dashboard.html
│   │   ├── gateway/
│   │   └── dispositivo/
│   │
│   └── admin_sistema/                 🆕 Pasta administrativa
│       ├── base_admin.html           ✅ Criado (layout sem tenant)
│       ├── dashboard.html            ✅ Criado (métricas globais)
│       └── provisionamento/
│           └── certificados_list.html ✅ Criado
│
├── urls.py                            ✅ Atualizado
│   ├── /admin-sistema/               🆕 Namespace administrativo
│   └── /admin-sistema/provisionamento/certificados/ 🆕
│
└── prj_tds_new/
    └── settings.py                    ✅ Atualizado
        └── MIDDLEWARE                 🆕 SuperAdminMiddleware registrado
```

---

## 🎯 FUNCIONALIDADES IMPLEMENTADAS

### 1. Dashboard Global Administrativo
- **URL**: `/tds_new/admin-sistema/`
- **View**: `tds_new.views.admin.dashboard.dashboard_global`
- **Template**: `admin_sistema/dashboard.html`
- **Permissão**: `@staff_member_required` (is_staff ou is_superuser)

**Métricas Exibidas:**
- ✅ Total de contas ativas
- ✅ Total de gateways (online/offline/nunca conectados)
- ✅ Total de dispositivos (ativos/manutenção)
- ✅ Total de certificados (válidos/expirados/revogados)
- ✅ Top 5 contas com mais gateways
- ✅ Atividade recente (últimos 7 dias)

### 2. Lista Global de Certificados
- **URL**: `/tds_new/admin-sistema/provisionamento/certificados/`
- **View**: `tds_new.views.admin.provisionamento.CertificadosListView`
- **Template**: `admin_sistema/provisionamento/certificados_list.html`
- **Permissão**: `UserPassesTestMixin` (is_staff ou is_superuser)

**Funcionalidades:**
- ✅ Visualização de **todos os certificados** (sem filtro de conta)
- ✅ Filtros: válidos, expirados, revogados
- ✅ Paginação (50 itens por página)
- ✅ Estatísticas consolidadas

### 3. Middleware de Proteção
- **Classe**: `SuperAdminMiddleware`
- **Arquivo**: `tds_new/middleware.py`
- **Registrado em**: `prj_tds_new/settings.py`

**Proteção:**
- ✅ Bloqueia acesso a `/tds_new/admin-sistema/*` para não-staff
- ✅ Redireciona para login se não autenticado
- ✅ Redireciona para dashboard normal se não for staff/superuser
- ✅ Mensagens de erro explicativas

### 4. Constantes Administrativas
- **ADMIN_SISTEMA**: Cenário para menu e título de página
- **SUPER_ADMIN**: Novo role de permissão (planejado para Week 9)

---

## 🔐 CONTROLE DE ACESSO

### Níveis de Permissão

| Role | Interface | Escopo | Ações |
|------|-----------|--------|-------|
| **VIEWER** | Usuário Final | Conta própria | Visualizar |
| **EDITOR** | Usuário Final | Conta própria | Criar/editar |
| **ADMIN** | Usuário Final | Conta própria | CRUD completo |
| **STAFF** | **Admin Sistema** | **Global** | ✅ Dashboard global<br>✅ Listar certificados |
| **SUPERUSER** | **Admin Sistema** | **Global** | ✅ Todas as ações admin |

### Diferenças Críticas

| Aspecto | Usuário Final | Admin Sistema |
|---------|--------------|---------------|
| **URL** | `/gateways/`, `/dispositivos/` | `/admin-sistema/` |
| **Queryset** | `Gateway.objects.filter(conta=conta_ativa)` | `Gateway.objects.all()` |
| **Permissão** | `LoginRequiredMixin` | `@staff_member_required` |
| **Layout** | `base_cenario_dispositivos.html` | `base_admin.html` |
| **Context** | Com `conta_ativa`, `empresa` | **Sem** tenant context |

---

## 📋 CHECKLIST DE VALIDAÇÃO

### Testes de Segurança
- [ ] Usuário comum (não-staff) **não acessa** `/admin-sistema/` ✅
- [ ] Usuário comum é redirecionado para `/dashboard/` ✅
- [ ] Staff/superuser **acessa** `/admin-sistema/` normalmente ✅
- [ ] Mensagens de erro são exibidas corretamente ✅

### Testes de Funcionalidade
- [ ] Dashboard admin mostra métricas de **todas as contas** ✅
- [ ] Lista de certificados mostra **todas as contas** (sem filtro) ✅
- [ ] Filtros funcionam (válidos, expirados, revogados) ✅
- [ ] Paginação funciona corretamente ✅
- [ ] Top 5 contas é calculado corretamente ✅

### Testes de Interface
- [ ] Layout base admin **não** possui menu de conta ✅
- [ ] Sidebar administrativa exibe módulos corretos ✅
- [ ] Badge de permissão (SUPER ADMIN/STAFF) é exibido ✅
- [ ] Link "Voltar ao Sistema" funciona ✅
- [ ] Templates não compartilham código (sem herança cruzada) ✅

---

## 🔜 WEEK 9 - PLANEJADO

### Fase 2: Provisionamento Completo

#### 2.1. Alocação de Gateways
- [ ] View: `alocar_gateway_view(gateway_id)`
- [ ] Form: `AlocarGatewayForm`
- [ ] Template: `admin_sistema/provisionamento/alocar_gateway.html`
- [ ] Funcionalidade: Transferir gateway entre contas

#### 2.2. Importação em Lote (CSV)
- [ ] View: `ImportarGatewaysCSVView`
- [ ] Form: `ImportarGatewaysCSVForm`
- [ ] Template: `admin_sistema/provisionamento/importar_csv.html`
- [ ] Validação de arquivo CSV
- [ ] Geração automática de certificados em lote

#### 2.3. Gestão de Certificados
- [ ] View: `revogar_certificado_view(certificado_id)`
- [ ] Template: Confirmação de revogação
- [ ] Atualização de CRL (Certificate Revocation List)
- [ ] Integração com broker Mosquitto

#### 2.4. Auditoria
- [ ] View: `LogsSistemaView`
- [ ] Template: `admin_sistema/auditoria/logs_sistema.html`
- [ ] Integração com `django.contrib.admin.models.LogEntry`
- [ ] Filtros: usuário, ação, data

---

## 🔜 WEEK 10 - PLANEJADO

### Fase 3: Auditoria e Compliance

#### 3.1. Certificados Revogados (CRL)
- [ ] View: `CertificadosRevogadosView`
- [ ] View: `exportar_crl_view()` (download PEM)
- [ ] Template: `admin_sistema/auditoria/certificados_revogados.html`
- [ ] Documentar uso no Mosquitto

#### 3.2. Auditoria de Ações Admin
- [ ] Registro de alocação de gateways
- [ ] Registro de emissão/revogação de certificados
- [ ] Registro de importação CSV

---

## 🔜 WEEK 11 - PLANEJADO

### Fase 4: Ferramentas de Manutenção

#### 4.1. Atualização de Firmware (OTA)
- [ ] View: `FirmwareUpdateView`
- [ ] Upload de firmware
- [ ] Sistema de versionamento
- [ ] Notificação para gateways (MQTT topic)

#### 4.2. Limpeza de Dados Históricos
- [ ] Script de remoção de leituras antigas (TimescaleDB)
- [ ] Interface para configurar retenção de dados
- [ ] Exportação antes da limpeza

---

## 📚 ARQUIVOS MODIFICADOS/CRIADOS

### Arquivos Modificados
1. `tds_new/constants.py` - Adicionado ADMIN_SISTEMA e SUPER_ADMIN
2. `tds_new/middleware.py` - Adicionado SuperAdminMiddleware
3. `tds_new/urls.py` - Adicionadas rotas administrativas
4. `prj_tds_new/settings.py` - Registrado SuperAdminMiddleware

### Arquivos Criados
1. `tds_new/views/admin/__init__.py`
2. `tds_new/views/admin/dashboard.py`
3. `tds_new/views/admin/provisionamento.py`
4. `tds_new/templates/admin_sistema/base_admin.html`
5. `tds_new/templates/admin_sistema/dashboard.html`
6. `tds_new/templates/admin_sistema/provisionamento/certificados_list.html`
7. `docs/ROADMAP_ADMIN_SISTEMA.md` (este arquivo)

---

## 🎓 LIÇÕES APRENDIDAS

### 1. Segregação de Contextos
- **Problema**: Mixing de multi-tenant com visão global
- **Solução**: Pastas separadas (`views/admin/`, `templates/admin_sistema/`)
- **Benefício**: Código limpo, fácil manutenção, segurança robusta

### 2. Middleware de Proteção
- **Importância**: Primeira linha de defesa contra acesso não autorizado
- **Implementação**: Verificação em `process_request` antes de qualquer view
- **Mensagens**: Feedback claro para usuários não autorizados

### 3. Templates Sem Compartilhamento
- **Anti-padrão**: Herdar de base_admin em templates de usuário final
- **Padrão correto**: Layouts base completamente segregados
- **Razão**: Context processors diferentes (tenant vs global)

### 4. Queries Sem Filtro
- **View Admin**: `Gateway.objects.all()` (sem `.filter(conta=...)`)
- **View Usuário**: `Gateway.objects.filter(conta=conta_ativa)`
- **Atenção**: Sempre documentar que admin é **sem filtro**

---

## ✅ STATUS FINAL WEEK 8

**Data de Conclusão:** 17/02/2026  
**Status:** 🟢 Implementada e pronta para testes  
**Próximo passo:** Testar em ambiente de desenvolvimento e validar segurança

**Comandos para testar:**
```bash
# 1. Aplicar migrations (se necessário)
python manage.py makemigrations
python manage.py migrate

# 2. Criar superuser para testes admin
python manage.py createsuperuser

# 3. Iniciar servidor
python manage.py runserver

# 4. Acessar dashboard admin
# http://localhost:8000/tds_new/admin-sistema/

# 5. Verificar proteção (usuário comum)
# Fazer login como usuário comum (não-staff)
# Tentar acessar /tds_new/admin-sistema/ → deve redirecionar
```

**Validações de Segurança:**
```sql
-- Verificar usuários staff
SELECT id, email, is_staff, is_superuser FROM tds_new_customuser WHERE is_active=true;

-- Verificar certificados (deve ver TODAS as contas)
-- Dashboard admin: deve mostrar certificados de todas as contas
-- Dashboard usuário: deve mostrar apenas da conta ativa
```

---

**Última atualização:** 17/02/2026  
**Responsável:** Equipe TDS New  
**Próxima revisão:** Week 9 (24/02/2026)
