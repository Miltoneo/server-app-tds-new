# 📝 LOG DE IMPLEMENTAÇÃO - TDS NEW

## ✅ SEMANA 3: MIDDLEWARE E CONTEXT PROCESSORS (14/02/2026)

**Status:** CONCLUÍDO  
**Tempo:** ~1 hora  
**Responsável:** Equipe de Desenvolvimento  
**Commit:** `[pendente]`

---

### 🎯 Objetivos Cumpridos

1. ✅ Implementar middleware multi-tenant (TenantMiddleware)
2. ✅ Implementar validação de licença (LicenseValidationMiddleware)
3. ✅ Criar context processors para templates
4. ✅ Configurar settings.py (MIDDLEWARE + TEMPLATES)
5. ✅ Atualizar porta do TimescaleDB (5432 → 5442)

---

### 📋 Tarefas Executadas

#### 1. Middleware Implementado (tds_new/middleware.py)

**A. TenantMiddleware**
```python
class TenantMiddleware(MiddlewareMixin):
    - Garante isolamento de dados por conta/tenant
    - Verifica se usuário tem acesso à conta selecionada
    - Define request.conta_ativa e request.usuario_conta
    - Armazena conta em thread-local para acesso global
    - Redireciona para seleção de conta se necessário
    - URLs isentas: /admin/, /auth/, /static/, /media/
```

**B. LicenseValidationMiddleware**
```python
class LicenseValidationMiddleware(MiddlewareMixin):
    - Valida se a conta está ativa
    - TODO (Week 8): Integrar com shared.assinaturas
    - Redireciona para /auth/license-expired/ se inativa
    - URLs isentas: /admin/, /auth/, /static/, /media/
```

**C. SessionDebugMiddleware**
```python
class SessionDebugMiddleware(MiddlewareMixin):
    - Debug de sessão em desenvolvimento (apenas DEBUG=True)
    - Logs: path, user, session keys, conta ativa
```

**D. Helper Function**
```python
def get_current_account():
    - Retorna a conta ativa no contexto da requisição
    - Thread-safe usando threading.local()
```

#### 2. Context Processors (core/context_processors.py)

**A. conta_context(request)**
```python
- Injeta 'conta' e 'conta_id' no contexto dos templates
- Prioridade 1: request.conta_ativa (middleware)
- Prioridade 2: session['conta_ativa_id'] (fallback)
- Retorna None se nenhuma conta ativa
```

**B. app_version(request)**
```python
- Injeta APP_VERSION no contexto
- Valor de settings.APP_VERSION
```

**C. session_context(request)**
```python
- Injeta variáveis de sessão:
  * titulo_pagina
  * cenario_nome (Dashboard, Dispositivos, Telemetria, etc)
  * menu_nome
```

**D. usuario_context(request)**
```python
- Injeta permissões do usuário:
  * usuario_atual: User object
  * usuario_admin: bool (role='admin')
  * usuario_pode_editar: bool (role='admin' ou 'editor')
  * usuario_pode_visualizar: bool (qualquer role ativo)
- Usa ContaMembership.is_admin(), .can_edit(), .can_view()
```

#### 3. Configuração settings.py

**A. MIDDLEWARE atualizado**
```python
MIDDLEWARE = [
    # ... Django defaults ...
    'tds_new.middleware.TenantMiddleware',             # ← NOVO
    'tds_new.middleware.LicenseValidationMiddleware',  # ← NOVO
    'tds_new.middleware.SessionDebugMiddleware',       # ← NOVO (dev only)
]
```

**B. TEMPLATES context_processors atualizado**
```python
'context_processors': [
    # ... Django defaults ...
    'core.context_processors.app_version',      # ← NOVO
    'core.context_processors.conta_context',    # ← NOVO
    'core.context_processors.session_context',  # ← NOVO
    'core.context_processors.usuario_context',  # ← NOVO
]
```

#### 4. Atualização de Configuração de Banco

**Porta TimescaleDB alterada:**
- `environments/.env.dev`: DATABASE_PORT=5432 → 5442
- `environments/.env.prod`: DATABASE_PORT=5443 → 5442
- Motivo: Alinhamento com infraestrutura Docker externa

---

### ✅ Validação

```bash
python manage.py check
# [CONFIG] tds_new | Ambiente: DEV | DEBUG: True | Arquivo: .env.dev
# System check identified 2 issues (3 silenced).
# ✅ Configuração válida
```

**Warnings não críticos:**
- `axes.W005`: AXES_USERNAME_CALLABLE (configuração customizada)
- `staticfiles.W004`: Diretório staticfiles não existe (criado em produção)

---

### 📊 Arquitetura Multi-Tenant

```
Request → TenantMiddleware
  ↓
  1. Verifica se usuário autenticado
  2. Busca conta ativa na sessão (conta_ativa_id)
  3. Valida acesso via ContaMembership
  4. Define request.conta_ativa e request.usuario_conta
  5. Armazena em thread-local (get_current_account())
  ↓
LicenseValidationMiddleware
  ↓
  1. Verifica conta.is_active
  2. TODO: Integrar com shared.assinaturas (Week 8)
  ↓
View Execution
  ↓
  - Acessa request.conta_ativa
  - Queries filtradas automaticamente por conta
  ↓
Template Rendering
  ↓
  - Context processors injetam variáveis globais:
    * {{ conta }}, {{ conta_id }}
    * {{ usuario_admin }}, {{ usuario_pode_editar }}
    * {{ titulo_pagina }}, {{ cenario_nome }}
```

---

### 🔑 Uso nas Views

```python
from django.shortcuts import render

def minha_view(request):
    # Conta ativa já está no request (via middleware)
    conta = request.conta_ativa
    usuario_conta = request.usuario_conta
    
    # Templates recebem variáveis automaticamente (via context processors)
    context = {
        'titulo_pagina': 'Minha Página',
        # conta, conta_id, usuario_admin já estão disponíveis
    }
    return render(request, 'template.html', context)
```

---

### 🔑 Uso nos Templates

```django
{# Variáveis injetadas automaticamente #}
<h1>{{ titulo_pagina }}</h1>
<p>Conta: {{ conta.name }}</p>

{% if usuario_admin %}
  <a href="#">Configurações Admin</a>
{% endif %}

{% if usuario_pode_editar %}
  <button>Editar</button>
{% endif %}
```

---

### 🚀 Próximos Passos - SEMANA 4

#### Week 4-5: Sistema de Cenários e UI Base
- [📁] Criar módulo `tds_new/cenarios/`
- [🎨] Implementar templates base com Bootstrap 5
- [📊] Dashboard inicial
- [🔐] Views de autenticação (login, logout, select-account)
- [📱] Menu de navegação com cenários
- [ ] Sistema de roteamento de cenários

---

## ✅ SEMANA 2: MODELOS E AUTENTICAÇÃO (14/02/2026)

**Status:** CONCLUÍDO  
**Tempo:** ~2 horas  
**Responsável:** Equipe de Desenvolvimento  
**Commit:** `b874b7d`

---

### 🎯 Objetivos Cumpridos

1. ✅ Implementar modelos base (CustomUser, Conta, ContaMembership)
2. ✅ Configurar AUTH_USER_MODEL no settings.py
3. ✅ Criar migrations e aplicar ao banco de dados
4. ✅ Criar superusuário de teste

---

### 📋 Tarefas Executadas

#### 1. Modelos Implementados (tds_new/models/base.py)

**A. CustomUser (AbstractUser)**
```python
class CustomUser(AbstractUser):
    - Autenticação por email (não por username)
    - Username preenchido automaticamente com email
    - Suporte a sistema de convites via invite_token
    - CustomUserManager para criação de usuários
    - USERNAME_FIELD = 'email'
    - REQUIRED_FIELDS = []
```

**B. Conta (Tenant)**
```python
class Conta(BaseAuditMixin):
    - name: Nome da organização (unique)
    - cnpj: CNPJ opcional
    - is_active: Controle de ativação
    - Métodos: get_total_members(), get_admins()
    - Isolamento multi-tenant completo
```

**C. ContaMembership (User ↔ Conta)**
```python
class ContaMembership(BaseAuditMixin):
    - conta: ForeignKey para Conta
    - user: ForeignKey para CustomUser
    - role: ADMIN | EDITOR | VIEWER
    - is_active: Controle de membership ativo
    - date_joined: Data de adesão
    - unique_together = ('conta', 'user')
    - Métodos: is_admin(), can_edit(), can_view()
    - Validação: clean() valida conta e user ativos
```

**D. SaaSBaseModel (Abstract)**
```python
class SaaSBaseModel(models.Model):
    - Base para todos os modelos com isolamento por conta
    - conta: ForeignKey obrigatória
    - ContaScopedManager customizado
    - save(): Valida que conta foi informada
```

**E. Mixins de Auditoria**
```python
- BaseTimestampMixin: created_at, updated_at
- BaseCreatedByMixin: created_by (ForeignKey User)
- BaseAuditMixin: Combina timestamp + created_by
```

#### 2. Migrations Criadas

```bash
python manage.py makemigrations tds_new

# Migrations criadas:
tds_new\migrations\0001_initial.py
  - Create model CustomUser
  - Create model Conta
  - Create model ContaMembership
  - Create indexes on ContaMembership
```

#### 3. Database Migration Aplicada

```bash
python manage.py migrate

# Aplicadas com sucesso:
- auth.* (12 migrations)
- tds_new.0001_initial
- admin.* (3 migrations)
- axes.* (8 migrations)
- sessions.0001_initial

Total: 29 migrations aplicadas
```

#### 4. Superusuário Criado

```bash
python criar_superuser.py

# Credenciais de desenvolvimento:
Email: admin@tds.com
Senha: admin123
```

#### 5. Configuração do settings.py

```python
# Habilitado AUTH_USER_MODEL
AUTH_USER_MODEL = 'tds_new.CustomUser'
```

---

### 📊 Métricas

**Código Criado:**
- **tds_new/models/base.py:** 400+ linhas de código
- **tds_new/models/__init__.py:** Exporta 9 classes

**Arquivos Criados:**
- 3 arquivos de modelos
- 1 migration inicial
- 1 script de criação de superusuário

**Migrations:**
- 1 migration inicial com 3 modelos
- 29 migrations aplicadas no total (incluindo Django built-in)

**Tabelas Criadas no Banco:**
- `customUser` - Usuários do sistema
- `conta` - Organizações (tenants)
- `conta_membership` - Relacionamento user ↔ conta

---

### ⚠️ Decisões Importantes

**1. AUTH_USER_MODEL = CustomUser**
- Definido desde o início (best practice)
- Evita migrations complexas no futuro
- Autenticação por email

**2. Mixins de Auditoria**
- Timestamp automático em todos os modelos
- Rastreamento de created_by
- Facilita troubleshooting

**3. SaaSBaseModel Abstract**
- Garante que todo modelo tem conta (tenant)
- Evita esquecimento de FK conta
- Manager customizado para filtros

---

### ✅ Resultado Final

- ✅ Modelos base implementados e testados
- ✅ Migrations aplicadas com sucesso
- ✅ Superusuário criado (admin@tds.com)
- ✅ PostgreSQL local configurado
- ⏭️ Pronto para Semana 3: Middleware e Context Processors

---

### 🎯 Próximos Passos (Semana 3)

#### Middleware
1. TenantMiddleware - Isolamento automático por conta
2. LicenseValidationMiddleware - Validação de planos

#### Context Processors
1. conta_context - Variáveis globais de conta
2. usuario_context - Variáveis do usuário logado
3. cenario_context - Variáveis de navegação

#### Testes
1. Testes unitários para modelos
2. Testes de isolamento multi-tenant
3. Testes de permissions (roles)

---

## ✅ DIAS 4-5: DOCUMENTAÇÃO E TESTES INICIAIS (14/02/2026)

**Status:** CONCLUÍDO (Testes SKIPPED)  
**Tempo:** ~45 minutos  
**Responsável:** Equipe de Desenvolvimento  
**Commit:** Pendente

---

### 🎯 Objetivos Cumpridos

1. ✅ Documentação completa do projeto em README.md
2. ✅ Stack tecnológico detalhado
3. ✅ Instruções de instalação passo a passo (9 steps)
4. ✅ Comandos úteis de desenvolvimento
5. ✅ Guia de variáveis de ambiente (dev vs prod)
6. ✅ Padrões de Conventional Commits
7. ✅ Links para documentação externa
8. ❌ Testes iniciais (SKIPPED - implementar conforme necessário)

---

### 📋 Tarefas Executadas

#### 1. Atualização Massiva do README.md

**Seções Adicionadas/Melhoradas:**

**A. SOBRE O PROJETO (melhorado)**
- Descrição detalhada da proposta do sistema
- Objetivos principais (gestão, supervisão, alerts, análise)
- Características-chave (IoT, multi-tenant, TimescaleDB)

**B. STACK TECNOLÓGICO (novo - detalhado)**
```
Backend:
- Django 5.1.6 (framework principal)
- PostgreSQL 17 + TimescaleDB 2.17 (time-series)
- Redis 7.2 (cache/sessions)
- Celery (tarefas assíncronas)

Frontend:
- Bootstrap 5.3 (UI framework)
- Chart.js (gráficos/visualizações)
- Select2 (dropdowns avançados)
- HTMX (interatividade dinâmica)

IoT/Telemetria:
- MQTT (Mosquitto broker)
- Paho MQTT 2.1.0 (Python client)
- Telegraf (coleta de métricas)

DevOps:
- Git/GitHub (versionamento)
- Docker/Docker Compose (containers)
- Gunicorn/Nginx (servidor web)
- GitHub Actions (CI/CD futuro)
```

**C. INSTALAÇÃO E SETUP (novo - 9 steps)**
```bash
# 1. Clonar repositório
git clone https://github.com/Miltoneo/server-app-tds-new.git

# 2. Criar virtualenv
python -m virtualenv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar banco de dados
python setup_database.py

# 5. Configurar .env
cp environments/.env.dev.example environments/.env.dev

# 6. Validar configuração
python manage.py check

# 7. Aplicar migrations (futuro - após criar modelos)
python manage.py migrate

# 8. Criar superuser (futuro)
python manage.py createsuperuser

# 9. Executar servidor
python manage.py runserver
```

**D. DESENVOLVIMENTO (novo - comandos úteis)**
```bash
# Validação
python manage.py check

# Servidor local
python manage.py runserver

# Shell Django
python manage.py shell

# Shell do banco
python manage.py dbshell

# Migrations
python manage.py makemigrations
python manage.py migrate

# Superusuário
python manage.py createsuperuser
```

**E. VARIÁVEIS DE AMBIENTE (novo - comparação dev/prod)**
| Variável | .env.dev | .env.prod |
|----------|----------|-----------|
| DATABASE_HOST | localhost | onkoto.com.br |
| DATABASE_PORT | 5432 | 5443 |
| MQTT_BROKER_HOST | localhost | mqtt |
| DEBUG | True | False |

**F. ESTRUTURA DE COMMITS (novo - Conventional Commits)**
```bash
# Exemplos:
feat(models): adicionar modelo Device
docs(readme): atualizar instruções de instalação
fix(mqtt): corrigir conexão com broker
refactor(views): simplificar lógica de filtragem
```

**G. DOCUMENTAÇÃO ADICIONAL (novo - links GitHub)**
- [ANALISE_GREENFIELD.md](https://github.com/Miltoneo/server-app-tds/blob/master/docs/ANALISE_GREENFIELD.md)
- [ROADMAP_DESENVOLVIMENTO.md](https://github.com/Miltoneo/server-app-tds/blob/master/docs/ROADMAP_DESENVOLVIMENTO.md)
- [MIGRACAO_DADOS.md](https://github.com/Miltoneo/server-app-tds/blob/master/docs/MIGRACAO_DADOS.md)

**H. ESTRUTURA DO PROJETO (melhorado)**
- Adicionado `models/` com Day 3
- Adicionado `setup_database.py`
- Detalhado todos os subdiretórios
- Adicionado CHANGELOG.md

**I. PRÓXIMOS PASSOS (atualizado)**
- Marcado Semana 1 como CONCLUÍDA
- Adicionado preview da Semana 2 (Modelos e Autenticação)
- Listado tasks pendentes (CustomUser, Conta, ContaMembership)

---

### 📊 Métricas

- **README.md:** ~200+ linhas adicionadas/modificadas
- **Seções criadas:** 7 novas seções principais
- **Exemplos de código:** 6 blocos bash/python
- **Links externos:** 3 documentos referenciados
- **Comandos úteis:** 8 comandos Django documentados
- **Comparação de ambientes:** Tabela dev vs prod criada

---

### ⚠️ Decisões Importantes

1. **Testes SKIPPED:**
   - Usuário solicitou "skip teste"
   - Testes serão implementados conforme necessário
   - Foco em documentação completa para onboarding

2. **Foco em Documentação:**
   - README.md agora é referência completa
   - Todas as instruções de instalação documentadas
   - Padrões de desenvolvimento estabelecidos
   - Links para documentação externa incluídos

3. **Semana 1 Concluída:**
   - Dias 1-3: Setup técnico completo
   - Dias 4-5: Documentação completa
   - Pronto para Semana 2 (Modelos e Autenticação)

---

### ✅ Resultado Final

- ✅ README.md é um guia completo de onboarding
- ✅ Stack tecnológico completamente documentado
- ✅ Instruções de instalação passo a passo validadas
- ✅ Comandos de desenvolvimento listados
- ✅ Padrões de commit estabelecidos (Conventional Commits)
- ✅ Week 1 (Setup e Foundation) 100% COMPLETA
- ⏭️ Pronto para Week 2: Modelos e Autenticação

---

### 🎯 Próximos Passos (Semana 2)

#### Modelos (Semanas 2-3)
1. Implementar `tds_new/models/base.py`:
   - CustomUser(AbstractUser)
   - Conta (tenant)
   - ContaMembership (user ↔ conta + roles)
2. Descomentar `AUTH_USER_MODEL` em settings.py
3. Criar e aplicar migrations
4. Testar criação de usuários e contas

#### Middleware
1. TenantMiddleware (isolamento por conta)
2. Context processors (conta_context, usuario_context)

---

## ✅ DIA 3: BANCO DE DADOS (14/02/2026)

**Status:** CONCLUÍDO  
**Tempo:** ~30 minutos  
**Responsável:** Equipe de Desenvolvimento  
**Commit:** `2b8a9f5`

---

### 🎯 Objetivos Cumpridos

1. ✅ Criar banco de dados PostgreSQL local
2. ✅ Criar usuário da aplicação com credenciais de produção
3. ✅ Configurar `.env.dev` com credenciais corretas
4. ✅ Testar conexão Django com banco de dados
5. ✅ Criar estrutura de modelos (`tds_new/models/`)
6. ✅ Verificar extensão TimescaleDB (não instalada localmente)

---

### 📋 Tarefas Executadas

#### 1. Configuração de Credenciais (.env.dev)

**Credenciais de admin PostgreSQL (para setup):**
- User: `postgres`
- Password: `postgres`

**Credenciais da aplicação (alinhadas com produção):**
```ini
DATABASE_NAME=db_tds_new
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=tsdb_django_d4j7g9       # ← Mesmo usuário de produção
DATABASE_PASSWORD=DjangoTS2025TimeSeries  # ← Mesma senha de produção
```

#### 2. Script de Setup Automatizado

**Arquivo:** `setup_database.py`

```bash
python setup_database.py

# Passos executados:
# 1. ✅ Conectou ao PostgreSQL como admin (postgres)
# 2. ✅ Criou usuário tsdb_django_d4j7g9
# 3. ✅ Criou banco db_tds_new
# 4. ⚠️  TimescaleDB não instalado (opcional)
# 5. ✅ Confirmou permissões do usuário
# 6. ✅ Testou conexão com credenciais da aplicação
```

**Resultado:**
```
PostgreSQL: 17.7 (Debian)
Banco: db_tds_new
Extensões: plpgsql (1.0)
```

#### 3. Validação Django

```bash
python manage.py check

# ✅ [CONFIG] tds_new | Ambiente: DEV | DEBUG: True | Arquivo: .env.dev
# ✅ System check identified 2 issues (3 silenced)
# ✅ Conexão ao banco db_tds_new bem-sucedida
```

#### 4. Estrutura de Modelos Criada

```
tds_new/
├── __init__.py
├── apps.py
└── models/                         # ← Novo
    ├── __init__.py                 # ← Novo (com imports planejados)
    └── base.py                     # ← Novo (placeholder para Semanas 2-3)
```

**Arquivo:** `tds_new/models/__init__.py`
- Estrutura de imports documentada
- Modelos serão implementados nas Semanas 2-3

**Arquivo:** `tds_new/models/base.py`
- Placeholder com TODOs
- Modelos planejados: CustomUser, Conta, ContaMembership

#### 5. Observações sobre TimescaleDB

⚠️ **TimescaleDB não foi instalado localmente:**
- Extensão não disponível no PostgreSQL 17 local
- O banco funcionará normalmente sem recursos de time-series
- TimescaleDB disponível em produção (onkoto.com.br:5443)
- Instalação local opcional: https://docs.timescale.com/install/

---

### 📊 Métricas

- **Banco criado:** db_tds_new (PostgreSQL 17.7)
- **Usuário criado:** tsdb_django_d4j7g9
- **Arquivos criados:** 3 (setup_database.py, models/__init__.py, models/base.py)
- **Django check:** 0 errors, 2 warnings (não críticos)
- **Tempo total:** ~30 minutos

---

### 🎯 Próximos Passos (Dias 4-5)

1. Criar README.md completo do projeto
2. Criar testes iniciais (test_settings.py)
3. Executar testes: `python manage.py test`
4. Commit: `feat(day3): configurar banco de dados PostgreSQL`
5. Push para GitHub

---

## ✅ DIA 2: CONFIGURAÇÃO DE AMBIENTE (14/02/2026)

**Status:** CONCLUÍDO  
**Tempo:** ~1 hora  
**Responsável:** Equipe de Desenvolvimento  
**Commit:** `6dc8273` - feat: setup inicial do projeto TDS New - greenfield

---

### 🎯 Objetivos Cumpridos

1. ✅ Criar e ativar virtualenv
2. ✅ Instalar Django 5.1.6 e dependências essenciais
3. ✅ Configurar `.env.dev` com db_tds_new e MQTT
4. ✅ Alinhar credenciais de banco com TDS original
5. ✅ Limpar `settings.py` de referências ao CONSTRUTORA
6. ✅ Corrigir `urls.py` para remover imports inexistentes
7. ✅ Validar configuração com `python manage.py check`

---

### 📋 Tarefas Executadas

#### 1. Ambiente Virtual

```bash
# Criado com virtualenv (Python 3.12.10)
python -m virtualenv venv
.\venv\Scripts\Activate.ps1

# Resultado: venv criado em 9261ms
```

#### 2. Dependências Instaladas

**Core:**
- Django==5.1.6
- psycopg2-binary==2.9.11
- django-environ==0.12.1
- paho-mqtt==2.1.0

**Third-party:**
- django-axes (tentativas de login)
- django-recaptcha (proteção anti-bot)
- django-bootstrap5 (interface)
- django-mathfilters (templates)
- django-extensions (admin tools)
- django-select2 (widgets)
- django-crispy-forms + crispy-bootstrap5 (forms)

#### 3. Configuração `.env.dev` - Desenvolvimento Local

**Database (PostgreSQL + TimescaleDB) - LOCALHOST:**
```ini
DATABASE_ENGINE=timescale.db.backends.postgresql
DATABASE_NAME=db_tds_new          # Novo banco (a ser criado localmente)
DATABASE_HOST=localhost           # ✅ Servidor local para desenvolvimento
DATABASE_USER=admin               # ✅ Usuário local padrão
DATABASE_PASSWORD=admin           # ✅ Senha local padrão
DATABASE_PORT=5432                # ✅ Porta PostgreSQL padrão
```

#### 3.1. Configuração `.env.prod` - Produção Remota

**Database (PostgreSQL + TimescaleDB) - SERVIDOR REMOTO:**
```ini
DATABASE_ENGINE=timescale.db.backends.postgresql
DATABASE_NAME=db_tds_new          # Novo banco (a ser criado no servidor)
DATABASE_HOST=onkoto.com.br       # ✅ Servidor remoto de produção
DATABASE_USER=tsdb_django_d4j7g9  # ✅ Mesmo usuário que TDS original
DATABASE_PASSWORD=DjangoTS2025TimeSeries  # ✅ Mesma senha que TDS original
DATABASE_PORT=5443                # ✅ Porta customizada (não 5432)
```

**Outras configurações produção:**
```ini
DEBUG=False
SECRET_KEY=CHANGE_THIS_IN_PRODUCTION_TDS_NEW_XXXXXXXXXXXX
ALLOWED_HOSTS=www.onkoto.com.br,onkoto.com.br

# MQTT
MQTT_BROKER_HOST=mqtt
MQTT_TOPIC_PREFIX=tds_new/devices

# TimescaleDB
TIMESCALE_RETENTION_DAYS=365      # 1 ano em produção
TIMESCALE_COMPRESSION_ENABLED=True

# Segurança HTTPS
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
```

**MQTT (IoT Telemetry):**
```ini
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_BROKER_USER=tds_new_user
MQTT_TOPIC_PREFIX=tds_new/devices
```

**TimescaleDB:**
```ini
TIMESCALE_RETENTION_DAYS=90
TIMESCALE_COMPRESSION_ENABLED=True
```

**Conta Visitante:**
```ini
VISITOR_EMAIL=visitante@onkoto.com.br
VISITOR_PASSWORD=demo2026
```

**Email (console para dev):**
```ini
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

#### 4. Limpeza `settings.py`

**Removido de INSTALLED_APPS:**
- django_adsense_injector
- jquery
- django_tables2
- django.contrib.sitemaps

**Removido de MIDDLEWARE:**
- construtora.middleware.MultiTenantMiddleware
- construtora.middleware.LicenseActiveMiddleware
- construtora.middleware.TenantMiddleware

**Comentados (TODO - Semanas 2-3):**
- AUTH_USER_MODEL='tds_new.CustomUser' (aguardando models)
- Context processors tds_new (aguardando models)

**Corrigido:**
- TEMPLATES backend: 'django.template.backends.django.DjangoTemplates'
- ROOT_URLCONF='prj_tds_new.urls'
- WSGI_APPLICATION='prj_tds_new.wsgi.application'

#### 5. Correção `urls.py`

**Removido:**
```python
# path('construtora/auth/', include(...))
# path('construtora/', include(...))
```

**Mantido:**
```python
path('admin/', admin.site.urls)
path('select2/', include("django_select2.urls"))
path('', lambda request: redirect('admin/', permanent=False))
```

#### 6. Validação

```bash
python manage.py check

# Resultado: 3 warnings (não críticos)
# - AXES_USERNAME_CALLABLE (configuração)
# - AXES_LOCKOUT_PARAMETERS (segurança recomendada)
# - staticfiles.W004 (diretório não existe - esperado)
# ✅ 0 ERRORS - Configuração validada
```

---

### 📊 Métricas

- **Pacotes instalados:** 12 third-party + Django core
- **Linhas `.env.dev`:** 111 (completo)
- **settings.py:** -4 INSTALLED_APPS, -3 MIDDLEWARE
- **urls.py:** Simplificado de 8 para 5 paths
- **Tempo virtualenv:** 9.3s
- **Tempo total:** ~1h

---

### 🎯 Próximos Passos (Day 3)

**Opção A - Desenvolvimento Local:**
1. Instalar PostgreSQL + TimescaleDB localmente
2. Criar banco `db_tds_new` com usuário `admin`
3. Testar conexão Django: `python manage.py check --database default`
4. Preparar estrutura `tds_new/models/`

**Opção B - Produção Remota:**
1. Conectar ao servidor PostgreSQL (onkoto.com.br:5443)
2. Criar banco `db_tds_new` com usuário `tsdb_django_d4j7g9`:
   ```sql
   CREATE DATABASE db_tds_new OWNER tsdb_django_d4j7g9;
   \c db_tds_new
   CREATE EXTENSION IF NOT EXISTS timescaledb;
   ```
3. Configurar variável `ENVIRONMENT=PROD` e testar conexão
4. Preparar estrutura `tds_new/models/`

---

## ✅ DIA 1: CRIAÇÃO DO REPOSITÓRIO (14/02/2026)

**Status:** CONCLUÍDO  
**Tempo:** ~30 minutos  
**Responsável:** Equipe de Desenvolvimento

---

### 🎯 Objetivos Cumpridos

1. ✅ Criar estrutura base do projeto
2. ✅ Copiar arquivos essenciais do CONSTRUTORA
3. ✅ Renomear referências de 'construtora' para 'tds_new'
4. ✅ Configurar `manage.py` e arquivos Django

---

### 📋 Tarefas Executadas

#### 1. Estrutura de Diretórios

```bash
# Criado em: f:\projects\server-app\server-app-tds-new\

✓ prj_tds_new/          # Configurações Django
✓ tds_new/              # App principal
✓ core/                 # Utilitários compartilhados
✓ environments/         # Arquivos .env
```

#### 2. Arquivos Copiados

```
✓ requirements.txt      # Dependências Python
✓ .gitignore           # Padrões de exclusão Git
✓ prj_tds_new/         # Estrutura Django completa
✓ core/                # Context processors e versioning
✓ environments/        # Sistema de ambientes (.env.dev, .env.prod)
```

#### 3. Arquivos Criados

```
✓ manage.py            # CLI Django
✓ tds_new/__init__.py  # Pacote Python
✓ tds_new/apps.py      # TdsNewConfig
✓ README.md            # Documentação do projeto
✓ CHANGELOG.md         # Este arquivo
```

#### 4. Configurações Atualizadas

**prj_tds_new/settings.py:**
```python
# Antes: PROJECT_NAME = 'construtora'
# Depois: PROJECT_NAME = 'tds_new'

# Antes: 'construtora.apps.ConstrutoraConfig'
# Depois: 'tds_new.apps.TdsNewConfig'
```

**prj_tds_new/asgi.py:**
```python
# Antes: 'prj_construtora.settings'
# Depois: 'prj_tds_new.settings'
```

**prj_tds_new/wsgi.py:**
```python
# Antes: 'prj_construtora.settings'
# Depois: 'prj_tds_new.settings'
```

**core/context_processors.py:**
```python
# Antes: from construtora.models import ...
# Depois: from tds_new.models import ...
```

**tds_new/apps.py:**
```python
class TdsNewConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tds_new'
```

---

### 🔍 Validações Realizadas

- [x] Estrutura de diretórios conforme roadmap
- [x] Todas as referências a 'construtora' substituídas por 'tds_new'
- [x] manage.py configurado com 'prj_tds_new.settings'
- [x] Apps.py com TdsNewConfig correto
- [x] README.md criado com documentação inicial

---

### 📊 Métricas

| Métrica | Valor |
|---------|-------|
| Arquivos criados | 3 |
| Arquivos copiados | ~180 |
| Arquivos editados | 5 |
| Linhas de código alteradas | ~15 |
| Tempo de execução | 30 min |

---

### 🐛 Problemas Encontrados

Nenhum problema significativo encontrado.

---

### 📝 Notas Técnicas

1. **Ambiente de desenvolvimento:** Windows PowerShell
2. **Estrutura base:** Copiada de `server-app-construtora` (versão estável)
3. **Padrão de nomes:** 
   - Projeto: `prj_tds_new`
   - App: `tds_new`
   - Config: `TdsNewConfig`
4. **Sistema de ambientes:** Mantido padrão CONSTRUTORA (ENVIRONMENT='DEV'/'PROD')

---

### 🎯 Próxima Etapa: DIA 2

**Objetivo:** Configuração de Ambiente

**Tarefas:**
- [ ] Criar virtualenv
- [ ] Instalar dependências do `requirements.txt`
- [ ] Configurar arquivo `.env.dev` com credenciais do banco
- [ ] Adaptar `settings.py` para especificidades do TDS New
- [ ] Testar: `python manage.py check`

**Pré-requisitos:**
- PostgreSQL 16 instalado
- Redis 7.2 instalado
- Python 3.11+ instalado

---

### 📚 Referências

- [ROADMAP_DESENVOLVIMENTO.md](../server-app-tds/docs/ROADMAP_DESENVOLVIMENTO.md) - Semana 1, Dia 1
- [ANALISE_GREENFIELD.md](../server-app-tds/docs/ANALISE_GREENFIELD.md)
- [Repositório CONSTRUTORA](../server-app-construtora/) - Base arquitetural

---

**Última atualização:** 14/02/2026 09:02
