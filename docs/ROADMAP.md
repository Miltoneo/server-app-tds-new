# 🗺️ ROADMAP - Sistema TDS New

**Projeto:** TDS New - Sistema de Telemetria e Monitoramento IoT  
**Repositório:** [Miltoneo/server-app-tds-new](https://github.com/Miltoneo/server-app-tds-new)  
**Última Atualização:** 15/02/2026  
**Status Geral:** 🟢 **Weeks 1-5 CONCLUÍDAS** | 🔵 **Pronto para Week 6-7**

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

## 🏗️ DECISÕES ARQUITETURAIS CRÍTICAS

### 1. MQTT Consumer Strategy

#### ❌ Telegraf REJEITADO
**Motivos:**
- Sem acesso ao ORM Django
- Impossível fazer isolamento multi-tenant (conta_id)
- Queries SQL raw sem validações Django
- Separação entre coleta e processamento

#### ✅ Django Consumer ADOTADO
**Vantagens:**
- Acesso completo ao ORM Django
- Isolamento multi-tenant nativo
- Validações de modelo automáticas
- Celery task integrado ao ecossistema

**Arquitetura:**
```
┌─────────────────────────────────────────────────────────────┐
│ MQTT Broker (Mosquitto)                                     │
│   ↓ mTLS authentication (CN = MAC address)                 │
│   ↓ Topic: tds_new/gateway/{MAC}/telemetria                │
│   ↓                                                         │
│ Django Celery Task (processar_telemetria_mqtt)             │
│   ↓ 1. Extrair MAC do client certificate CN                │
│   ↓ 2. Lookup: Gateway.objects.get(mac_address=MAC)        │
│   ↓ 3. Conta descoberta via Gateway.conta FK               │
│   ↓ 4. Parse JSON: [gateway_mac, timestamp, leituras[]]    │
│   ↓ 5. Validar dispositivos (código no gateway)            │
│   ↓ 6. Criar LeituraDispositivo (bulk_create)              │
│   ↓ 7. Atualizar Gateway.last_seen, is_online              │
│   ↓                                                         │
│ TimescaleDB Hypertable                                      │
│   ↓ Particionamento automático por timestamp               │
│   ↓ Continuous aggregates mensais (ConsumoMensal)          │
└─────────────────────────────────────────────────────────────┘
```

**Payload MQTT (JSON):**
```json
{
  "gateway_mac": "aa:bb:cc:dd:ee:ff",
  "timestamp": "2026-02-15T14:30:00Z",
  "leituras": [
    {
      "dispositivo_codigo": "D01",
      "valor": 123.45,
      "unidade": "kWh"
    },
    {
      "dispositivo_codigo": "D02",
      "valor": 67.89,
      "unidade": "m³"
    }
  ]
}
```

---

### 2. Certificate Management Strategy

#### ❌ Hybrid Bootstrap + Operational REJEITADO
**Problema:**
- Bootstrap certificate (10 anos) para registrar device
- Operational certificate (90 dias) após registro
- **CONFLITO:** Dispositivo offline por 2 anos não consegue renovar operational certificate

#### ✅ Single Permanent Certificate ADOTADO
**Estratégia:**
- **Validade:** 10 anos (fabricação → expiração)
- **Geração:** Factory scripts (lote via CSV)
- **Identificação:** Common Name = MAC address (unique)
- **Algorithm:** RSA 2048 bits
- **Revogação:** CRL (Certificate Revocation List)
- **Renovação:** OTA (Over-The-Air) 2 anos antes

**Vantagens:**
- ✅ Dispositivo offline por anos pode reconectar
- ✅ Zero intervenção manual
- ✅ CRL para revogação imediata (dispositivo roubado/defeituoso)
- ✅ OTA renewal 2 anos antes (janela de 730 dias)

**Modelo Django:**
```python
class CertificadoDevice(SaaSBaseModel):
    mac_address = CharField(17, unique per conta)
    certificate_pem = TextField(conteúdo do certificado)
    serial_number = CharField(50, unique globally)
    expires_at = DateTimeField(data de expiração)
    
    is_revoked = BooleanField(default=False)
    revoked_at = DateTimeField(null, blank)
    revoke_reason = TextField(optional)
    
    class Meta:
        unique_together = [('conta', 'mac_address')]
        indexes = [
            Index(fields=['mac_address', 'is_revoked']),
            Index(fields=['expires_at'])  # Query de renovação
        ]
```

---

### 3. OTA Certificate Renewal Protocol

#### Cenário do Problema
```
Ano 0 (Fabricação): 1000 dispositivos fabricados juntos
  → Todos recebem certificado com validade de 10 anos
  
Ano 10 (Expiração): Todos os 1000 certificados expiram SIMULTANEAMENTE
  → 1000 dispositivos offline ao mesmo tempo
  → Catástrofe operacional
```

#### Solução: OTA Renewal com Antecedência
**Características:**
- ✅ **Janela de 2 anos** (renovação começa 730 dias antes)
- ✅ **Distribuição gradual** (10 devices/day)
- ✅ **MQTT Retained Messages** (`retain=True`)
- ✅ **Validação no firmware** (antes de salvar novo cert)
- ✅ **Rollback automático** (se novo cert falhar)

**Fluxo Completo:**
```
┌─────────────────────────────────────────────────────────────┐
│ Backend (Celery Beat - Daily 02:00 AM)                      │
│   ↓ Query: WHERE expires_at <= NOW() + 730 days LIMIT 10   │
│   ↓ Generate new certificate (10-year validity)             │
│   ↓ Publish to MQTT:                                        │
│     - Topic: tds_new/gateway/{MAC}/cert_update              │
│     - Payload: {new_cert, new_key, expires_at}              │
│     - QoS: 1 (at least once)                                │
│     - Retain: true (offline devices receive later)          │
│   ↓                                                          │
│ Device Firmware (ESP32/RPi)                                 │
│   ↓ Subscribe: tds_new/gateway/{MAC}/cert_update            │
│   ↓ Receive payload                                         │
│   ↓ Validate certificate:                                   │
│     - CN = MAC address                                      │
│     - Not expired                                           │
│     - Valid signature                                       │
│   ↓ Backup old: device-cert-old.pem                         │
│   ↓ Save new: device-cert-new.pem                           │
│   ↓ Restart device (load new certificate)                   │
│   ↓ Test connection to MQTT broker                          │
│   ↓ If FAIL:                                                │
│     - Rollback to device-cert-old.pem                       │
│     - Restart again                                         │
│     - Log error                                             │
└─────────────────────────────────────────────────────────────┘
```

**Proteção contra Riscos:**
1. **Device offline durante renewal**  
   → MQTT `retain=true` garante entrega ao reconectar

2. **Certificado corrompido**  
   → Validação antes de salvar + rollback automático

3. **Expiração em massa**  
   → 2 anos de antecedência + 10 devices/day  
   → 3650 devices = 365 dias para renovar todos

---

### 4. Provisioning Strategy

#### ❌ Staging Table (Bootstrap) REJEITADO
- Table temporária para devices não registrados
- Adiciona complexidade desnecessária

#### ✅ Pre-Registration ADOTADO
**Fluxo:**
```
1. Factory (Fabricação):
   - Gerar certificado (10 anos, CN = MAC)
   - Flash firmware + certificado
   - Registrar em CSV: MAC, serial, expires_at
   
2. Admin (Pré-Cadastro no Django):
   - Importar CSV via Django Admin
   - Criar Gateway record (mac, codigo, conta)
   - Status: PRÉ-CADASTRADO
   
3. Field (Instalação):
   - Scan QR Code (WiFi SSID + password)
   - Device conecta via BLE, recebe WiFi credentials
   - Device conecta WiFi → MQTT broker (mTLS)
   - Primeira telemetria → Status: ATIVO
   
4. Operation (Anos):
   - Device offline 2 anos? → Reconecta com mesmo cert ✅
   - Cert expira em 8 anos? → OTA renewal automático ✅
```

**Provisioning Methods:**
1. **Fase 1 (Manual):** QR Code com WiFi credentials via BLE
2. **Fase 2 (Semi-Auto):** OTA certificate updates via MQTT
3. **Fase 3 (Futuro):** AWS IoT JITR, Azure DPS

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

### 📋 TAREFAS DETALHADAS

#### 1. Criar Modelos Django

**A. tds_new/models/dispositivos.py**
```python
class Gateway(SaaSBaseModel):
    """Gateway de telemetria (coleta dados via Modbus RTU e publica via MQTT)"""
    
    # Identificação
    codigo = CharField(30, unique per conta)
    mac = CharField(17, unique per conta, regex aa:bb:cc:dd:ee:ff)
    nome = CharField(100)
    descricao = TextField(optional)
    
    # Localização
    latitude = DecimalField(9,6, optional)
    longitude = DecimalField(9,6, optional)
    
    # Capacidade
    qte_max_dispositivos = IntegerField(default=8)
    
    # Status
    is_online = BooleanField(default=False)
    last_seen = DateTimeField(null, blank)
    firmware_version = CharField(20, optional)
    
    # Meta
    class Meta:
        unique_together = [('conta', 'codigo'), ('conta', 'mac')]
        indexes = [
            Index(fields=['conta', 'is_online']),
            Index(fields=['conta', 'mac']),
        ]
    
    # Métodos
    @property
    def status_conexao(self):
        """ONLINE | OFFLINE | NUNCA_CONECTADO"""
        
    @property
    def dispositivos_count(self):
        """Contagem de dispositivos ativos"""
        
    @property
    def capacidade_disponivel(self):
        """Slots disponíveis para novos dispositivos"""
        
    def clean(self):
        """Validar formato MAC: aa:bb:cc:dd:ee:ff"""


class Dispositivo(SaaSBaseModel):
    """Dispositivo IoT conectado ao gateway"""
    
    # Relacionamento
    gateway = ForeignKey(Gateway, on_delete=CASCADE)
    
    # Identificação
    codigo = CharField(20)  # Unique dentro do gateway
    mac = CharField(17, optional, unique per conta)
    nome = CharField(100)
    descricao = TextField(optional)
    tipo = CharField(choices=[MEDIDOR, SENSOR, ATUADOR])
    
    # Modbus RTU (obrigatório se tipo==MEDIDOR)
    register_modbus = IntegerField(1-65535, optional)
    slave_id = IntegerField(1-247, optional)
    
    # Operação
    modo = CharField(choices=[AUTO, MANUAL], default=AUTO)
    status = CharField(choices=[ATIVO, INATIVO, MANUTENCAO])
    val_alarme_dia = DecimalField(optional)
    val_alarme_mes = DecimalField(optional)
    
    # Status
    is_online = BooleanField(default=False)
    last_seen = DateTimeField(null, blank)
    firmware_version = CharField(20, optional)
    
    # Meta
    class Meta:
        unique_together = [('gateway', 'codigo')]
        indexes = [
            Index(fields=['conta', 'gateway', 'status']),
            Index(fields=['conta', 'mac']),
        ]
    
    # Métodos
    def clean(self):
        """
        Validações:
        - Se tipo==MEDIDOR: slave_id obrigatório (1-247)
        - Se tipo==MEDIDOR: register_modbus obrigatório (1-65535)
        - Se mac preenchido: validar formato aa:bb:cc:dd:ee:ff
        - Validar capacidade do gateway (max_dispositivos)
        """
```

**B. tds_new/models/telemetria.py**
```python
class LeituraDispositivo(SaaSBaseModel):
    """TimescaleDB Hypertable - Leituras de telemetria"""
    
    # Partition key
    time = DateTimeField(db_index=True)
    
    # Relacionamentos
    gateway = ForeignKey(Gateway, on_delete=CASCADE)
    dispositivo = ForeignKey(Dispositivo, on_delete=CASCADE)
    
    # Dados
    valor = DecimalField(15,4)
    unidade = CharField(10)  # kWh, m³, L, etc
    payload_raw = JSONField(optional)
    
    # Meta
    class Meta:
        managed = False  # Gerenciado pelo TimescaleDB
        db_table = 'tds_new_leitura_dispositivo'
        indexes = [
            Index(fields=['conta', 'time']),
            Index(fields=['dispositivo', 'time']),
        ]


class ConsumoMensal(models.Model):
    """Continuous Aggregate - Consumo mensal agregado"""
    
    mes_referencia = DateField
    conta = ForeignKey(Conta)
    dispositivo = ForeignKey(Dispositivo)
    total_consumo = DecimalField
    media_diaria = DecimalField
    leituras_count = IntegerField
    
    class Meta:
        managed = False  # Gerenciado pelo TimescaleDB
        db_table = 'tds_new_consumo_mensal'
```

**C. tds_new/models/certificados.py**
```python
class CertificadoDevice(SaaSBaseModel):
    """Certificados X.509 dos dispositivos (10 anos de validade)"""
    
    # Identificação
    mac_address = CharField(17)  # Unique per conta
    certificate_pem = TextField
    serial_number = CharField(50)  # Unique globally
    expires_at = DateTimeField
    
    # Revogação (CRL)
    is_revoked = BooleanField(default=False)
    revoked_at = DateTimeField(null, blank)
    revoke_reason = TextField(optional)
    
    # Meta
    class Meta:
        unique_together = [('conta', 'mac_address')]
        indexes = [
            Index(fields=['mac_address', 'is_revoked']),
            Index(fields=['serial_number']),  # Global unique
            Index(fields=['expires_at']),  # Query de renovação
        ]
    
    # Métodos
    @property
    def dias_para_expiracao(self):
        """Dias restantes até expiração"""
        
    @property
    def precisa_renovacao(self):
        """True se faltam <= 730 dias (2 anos)"""
```

**D. Atualizar tds_new/models/__init__.py**
```python
from .base import *
from .dispositivos import Gateway, Dispositivo
from .telemetria import LeituraDispositivo, ConsumoMensal
from .certificados import CertificadoDevice

__all__ = [
    # Base
    'CustomUser',
    'Conta',
    'ContaMembership',
    'SaaSBaseModel',
    # IoT
    'Gateway',
    'Dispositivo',
    'LeituraDispositivo',
    'ConsumoMensal',
    'CertificadoDevice',
]
```

---

#### 2. Criar Migrations

```bash
# Step 1: Gerar migrations Django
cd f:\projects\server-app\server-app-tds-new
python manage.py makemigrations tds_new

# Esperado:
# Migrations for 'tds_new':
#   tds_new\migrations\0002_gateway_dispositivo_certificadodevice.py
#     - Create model Gateway
#     - Create model Dispositivo
#     - Create model CertificadoDevice
#     - Create model LeituraDispositivo (managed=False)
#     - Create model ConsumoMensal (managed=False)

# Step 2: Aplicar migrations
python manage.py migrate

# Step 3: SQL manual para TimescaleDB hypertable
psql -U tsdb_django_d4j7g9 -d db_tds_new
```

**SQL para TimescaleDB:**
```sql
-- Criar hypertable para LeituraDispositivo
SELECT create_hypertable(
    'tds_new_leitura_dispositivo',
    'time',
    chunk_time_interval => INTERVAL '1 day'
);

-- Criar continuous aggregate para ConsumoMensal
CREATE MATERIALIZED VIEW tds_new_consumo_mensal
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 month', time) AS mes_referencia,
    conta_id,
    dispositivo_id,
    SUM(valor) AS total_consumo,
    AVG(valor) AS media_diaria,
    COUNT(*) AS leituras_count
FROM tds_new_leitura_dispositivo
GROUP BY mes_referencia, conta_id, dispositivo_id
WITH NO DATA;

-- Policy de refresh (atualizar a cada 1 hora)
SELECT add_continuous_aggregate_policy('tds_new_consumo_mensal',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- Índices adicionais
CREATE INDEX idx_leitura_conta_time ON tds_new_leitura_dispositivo (conta_id, time DESC);
CREATE INDEX idx_leitura_dispositivo_time ON tds_new_leitura_dispositivo (dispositivo_id, time DESC);
```

**Criar script: scripts/setup_timescaledb.sql**
```sql
-- Arquivo completo com todos os comandos SQL acima
```

---

#### 3. Implementar CRUD - Gateway

**A. tds_new/forms/gateway.py**
```python
from django import forms
from tds_new.models import Gateway
import re

class GatewayForm(forms.ModelForm):
    class Meta:
        model = Gateway
        fields = [
            'codigo', 'mac', 'nome', 'descricao',
            'latitude', 'longitude', 'qte_max_dispositivos'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'mac': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'aa:bb:cc:dd:ee:ff'
            }),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'qte_max_dispositivos': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def clean_mac(self):
        mac = self.cleaned_data.get('mac')
        if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', mac):
            raise forms.ValidationError('Formato inválido. Use aa:bb:cc:dd:ee:ff')
        return mac.lower()  # Padronizar lowercase
```

**B. tds_new/views/gateway.py**
```python
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from tds_new.models import Gateway
from tds_new.forms.gateway import GatewayForm

class GatewayListView(LoginRequiredMixin, ListView):
    model = Gateway
    template_name = 'tds_new/gateway/list.html'
    context_object_name = 'gateways'
    paginate_by = 20
    
    def get_queryset(self):
        qs = Gateway.objects.filter(conta=self.request.conta_ativa)
        # Filtros
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(is_online=(status=='online'))
        return qs.order_by('-created_at')

class GatewayCreateView(LoginRequiredMixin, CreateView):
    model = Gateway
    form_class = GatewayForm
    template_name = 'tds_new/gateway/form.html'
    success_url = reverse_lazy('tds_new:gateway_list')
    
    def form_valid(self, form):
        form.instance.conta = self.request.conta_ativa
        form.instance.created_by = self.request.user
        return super().form_valid(form)

# UpdateView, DeleteView, DetailView similar...
```

**C. URLs**
```python
# tds_new/urls.py
from tds_new.views import gateway

urlpatterns = [
    # ...
    path('gateways/', gateway.GatewayListView.as_view(), name='gateway_list'),
    path('gateways/create/', gateway.GatewayCreateView.as_view(), name='gateway_create'),
    path('gateways/<int:pk>/', gateway.GatewayDetailView.as_view(), name='gateway_detail'),
    path('gateways/<int:pk>/edit/', gateway.GatewayUpdateView.as_view(), name='gateway_edit'),
    path('gateways/<int:pk>/delete/', gateway.GatewayDeleteView.as_view(), name='gateway_delete'),
]
```

---

#### 4. Implementar CRUD - Dispositivo

**Similar ao Gateway**, com validações adicionais:
- `tds_new/forms/dispositivo.py`: Validação condicional (Modbus vs WiFi)
- `tds_new/views/dispositivo.py`: CRUD completo
- Templates responsivos com Bootstrap 5

---

#### 5. Templates Bootstrap 5

**A. tds_new/templates/tds_new/gateway/list.html**
```django
{% extends 'base.html' %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>Gateways</h2>
    <a href="{% url 'tds_new:gateway_create' %}" class="btn btn-primary">
        <i class="bi bi-plus-circle"></i> Novo Gateway
    </a>
</div>

<!-- Filtros -->
<div class="card mb-3">
    <div class="card-body">
        <form method="get" class="row g-3">
            <div class="col-md-4">
                <label>Status</label>
                <select name="status" class="form-select">
                    <option value="">Todos</option>
                    <option value="online">Online</option>
                    <option value="offline">Offline</option>
                </select>
            </div>
            <div class="col-md-4 d-flex align-items-end">
                <button type="submit" class="btn btn-secondary">Filtrar</button>
            </div>
        </form>
    </div>
</div>

<!-- Lista -->
<div class="row">
    {% for gateway in gateways %}
    <div class="col-md-6 col-lg-4 mb-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">{{ gateway.nome }}</h5>
                <p class="card-text text-muted">{{ gateway.codigo }} | {{ gateway.mac }}</p>
                <span class="badge {% if gateway.is_online %}bg-success{% else %}bg-secondary{% endif %}">
                    {{ gateway.status_conexao }}
                </span>
                <hr>
                <div class="d-flex justify-content-between">
                    <small>Dispositivos: {{ gateway.dispositivos_count }}/{{ gateway.qte_max_dispositivos }}</small>
                    <a href="{% url 'tds_new:gateway_detail' gateway.pk %}" class="btn btn-sm btn-primary">Ver</a>
                </div>
            </div>
        </div>
    </div>
    {% empty %}
    <div class="col-12">
        <div class="alert alert-info">Nenhum gateway cadastrado.</div>
    </div>
    {% endfor %}
</div>

<!-- Paginação -->
{% if is_paginated %}
<nav>
    <ul class="pagination">
        {% if page_obj.has_previous %}
        <li class="page-item"><a class="page-link" href="?page={{ page_obj.previous_page_number }}">Anterior</a></li>
        {% endif %}
        <li class="page-item active"><span class="page-link">{{ page_obj.number }}</span></li>
        {% if page_obj.has_next %}
        <li class="page-item"><a class="page-link" href="?page={{ page_obj.next_page_number }}">Próximo</a></li>
        {% endif %}
    </ul>
</nav>
{% endif %}
{% endblock %}
```

**Outros templates:**
- `gateway/form.html`: Form de criação/edição
- `gateway/detail.html`: Detalhes + lista de dispositivos
- `dispositivo/list.html`: Lista de dispositivos
- `dispositivo/form.html`: Form com validação condicional
- `dispositivo/detail.html`: Detalhes + histórico de leituras

---

#### 6. Atualizar Cenário de Dispositivos

**tds_new/views/cenario.py**
```python
@login_required
def cenario_dispositivos(request):
    """Cenário de dispositivos IoT - redireciona para lista de gateways"""
    _configurar_cenario(request, Cenarios.DISPOSITIVOS)
    return redirect('tds_new:gateway_list')  # ← Atualizar redirecionamento
```

---

### ✅ Checklist de Execução - Week 6-7

- [ ] **Dia 1**: Criar modelos (dispositivos.py, telemetria.py, certificados.py)
- [ ] **Dia 1**: Atualizar `__init__.py` com exports
- [ ] **Dia 1**: Gerar e aplicar migrations (`makemigrations`, `migrate`)
- [ ] **Dia 1**: Executar SQL de TimescaleDB (hypertable + continuous aggregate)
- [ ] **Dia 2**: Criar forms (GatewayForm, DispositivoForm)
- [ ] **Dia 2**: Criar views (CRUD Gateway)
- [ ] **Dia 3**: Criar templates (list, form, detail para Gateway)
- [ ] **Dia 3**: Testar CRUD Gateway (criar, editar, deletar)
- [ ] **Dia 4**: Criar views (CRUD Dispositivo)
- [ ] **Dia 4**: Criar templates (list, form, detail para Dispositivo)
- [ ] **Dia 5**: Testar CRUD Dispositivo
- [ ] **Dia 5**: Atualizar cenário de dispositivos
- [ ] **Dia 5**: Validar isolamento multi-tenant
- [ ] **Dia 5**: Commit e push para GitHub

---

## ⏳ ROADMAP FUTURO (Weeks 8+)

### **WEEK 8-9: INTEGRAÇÃO MQTT E TELEMETRIA**
**Prazo Estimado:** 5-7 dias  
**Complexidade:** Alta

#### Entregas
- [ ] Implementar Celery worker MQTT consumer
- [ ] Paho-MQTT client com mTLS authentication
- [ ] Processar payloads JSON e salvar em LeituraDispositivo
- [ ] Atualizar Gateway.last_seen e is_online
- [ ] Dashboard com dados reais (telemetria ao vivo)
- [ ] Testes de integração MQTT → Django → TimescaleDB

#### Arquivos a Criar
```
tds_new/
├── mqtt/
│   ├── __init__.py
│   ├── consumer.py (Celery task)
│   └── client.py (Paho-MQTT wrapper)
├── tasks/
│   ├── __init__.py
│   └── telemetria.py (processar_telemetria_mqtt)
└── management/commands/
    └── start_mqtt_consumer.py
```

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

### 1️⃣ **IMPLEMENTAR WEEK 6-7 (AGORA)**
```bash
cd f:\projects\server-app\server-app-tds-new

# Criar modelos
# - tds_new/models/dispositivos.py
# - tds_new/models/telemetria.py
# - tds_new/models/certificados.py

# Gerar migrations
python manage.py makemigrations tds_new

# Aplicar migrations
python manage.py migrate

# Configurar TimescaleDB
psql -U tsdb_django_d4j7g9 -d db_tds_new -f scripts/setup_timescaledb.sql
```

### 2️⃣ **TESTAR ISOLAMENTO MULTI-TENANT**
```python
# Criar 2 contas diferentes
# Criar gateways em cada conta
# Validar que cada conta vê apenas seus gateways
```

### 3️⃣ **COMMIT E PUSH**
```bash
git add .
git commit -m "feat: implementar Week 6-7 - Módulo de Dispositivos IoT

- Criar modelos Gateway, Dispositivo, LeituraDispositivo, CertificadoDevice
- Configurar TimescaleDB hypertable e continuous aggregate
- Implementar CRUD completo para Gateway e Dispositivo
- Templates Bootstrap 5 responsivos
- Validações de negócio (MAC address, Modbus, capacidade)
- Isolamento multi-tenant em todas as queries"

git push origin master
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

**Última atualização:** 15/02/2026  
**Versão do Documento:** 1.0  
**Autor:** Sistema TDS New - Roadmap Completo
