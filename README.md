# 🚀 TDS NEW - Sistema de Telemetria e Monitoramento IoT

**Projeto Greenfield** baseado na arquitetura do **CONSTRUTORA**  
**Status:** 🟢 Em Desenvolvimento - Semana 1 Concluída (Dias 1-3)  
**Criado em:** 14/02/2026  
**Repositório:** https://github.com/Miltoneo/server-app-tds-new  
**Última atualização:** 14/02/2026

---

## 📋 SOBRE O PROJETO

TDS New é a **versão moderna e refatorada** do sistema TDS, desenvolvida do zero (greenfield) seguindo os padrões arquiteturais maduros e testados do projeto **CONSTRUTORA**.

O sistema permite monitoramento remoto de consumo (água, energia, gás) via dispositivos IoT conectados por MQTT, com visualização em tempo real e processamento de telemetria usando PostgreSQL + TimescaleDB.

### 🎯 Objetivos

- ✅ **Arquitetura limpa** - 100% baseada em padrões do CONSTRUTORA
- ✅ **Multi-tenant robusto** - Isolamento via Conta + ContaMembership  
- ✅ **Sistema de cenários** - Navegação centralizada e consistente
- ✅ **Context processors** - Variáveis globais em templates
- ✅ **Integração MQTT** - Recebimento de telemetria IoT em tempo real
- ✅ **Time-series otimizado** - PostgreSQL + TimescaleDB

### ✨ Características Principais

- 🏢 **Multi-tenant**: Isolamento completo de dados por conta
- 🏗️ **Arquitetura Limpa**: Baseado em padrões testados e validados
- 📡 **IoT Ready**: Integração MQTT para telemetria em tempo real
- ⏱️ **Time-Series**: PostgreSQL + TimescaleDB para dados temporais otimizados
- 🧭 **Sistema de Cenários**: Navegação centralizada e consistente
- 🔐 **Autenticação Multi-tenant**: Roles (ADMIN, EDITOR, VIEWER) por conta

---

## 🛠️ STACK TECNOLÓGICO

### Backend
- **Django 5.1.6** - Framework web Python
- **PostgreSQL 17** - Banco de dados relacional
- **TimescaleDB 2.17** - Extensão para time-series (produção)
- **Redis 7.2** - Cache e sessões
- **Celery** - Tarefas assíncronas (futuro)

### Frontend
- **Bootstrap 5.3** - Framework CSS
- **Chart.js** - Gráficos de consumo
- **Select2** - Dropdowns inteligentes
- **HTMX** - Interatividade (futuro)

### IoT
- **MQTT (Mosquitto)** - Message broker para telemetria
- **Paho MQTT 2.1.0** - Client Python
- **Telegraf** - Ingestão de dados (futuro/opcional)

### DevOps
- **Git + GitHub** - Controle de versão
- **Docker + Docker Compose** - Containerização (futuro)
- **Gunicorn + Nginx** - Servidor de aplicação (produção)
- **GitHub Actions** - CI/CD (futuro)

---

## 📦 INSTALAÇÃO E SETUP

### 🐳 **Opção 1: Docker Compose (RECOMENDADO)**

> ✅ **Vantagem:** Paridade total dev/prod com TimescaleDB 2.17 igual produção

#### Pré-requisitos
- Docker Desktop (Windows/Mac) ou Docker Engine + Docker Compose (Linux)
- Python 3.12.10+ (para executar Django localmente)
- Git

#### Setup Rápido

```bash
# 1. Clone do repositório
git clone https://github.com/Miltoneo/server-app-tds-new.git
cd server-app-tds-new

# 2. Criar e ativar virtualenv
python -m virtualenv venv
.\venv\Scripts\Activate.ps1  # Windows
# source venv/bin/activate    # Linux/Mac

# 3. Instalar dependências Python
pip install -r requirements.txt

# 4. Subir stack Docker (PostgreSQL + Redis + MQTT)
docker compose -f docker-compose.dev.yml up -d

# 5. Aguardar serviços ficarem healthy (~30s)
docker compose -f docker-compose.dev.yml ps

# 6. Aplicar migrations
python manage.py migrate

# 7. Criar superusuário
python criar_superuser.py
# Ou: python manage.py createsuperuser

# 8. Executar servidor Django
python manage.py runserver
```

#### Verificar Setup

```bash
# Testar conexões com serviços Docker
python test_docker_connections.py

# Output esperado:
# ✅ PostgreSQL: PostgreSQL 17.x
# ✅ TimescaleDB: 2.17.2
# ✅ Redis: 7.2.x
# ✅ MQTT: Conectado com sucesso
```

#### Comandos Docker Compose

```bash
# Parar serviços
docker compose -f docker-compose.dev.yml stop

# Parar e remover containers (dados permanecem)
docker compose -f docker-compose.dev.yml down

# Parar e remover TUDO (inclusive volumes)
docker compose -f docker-compose.dev.yml down -v

# Ver logs
docker compose -f docker-compose.dev.yml logs -f

# Acessar PostgreSQL
docker exec -it tds_new_db_dev psql -U tsdb_django_d4j7g9 -d db_tds_new
```

**📖 Documentação completa:** [`docker/README.md`](docker/README.md)

---

### 💻 **Opção 2: Setup Local (PostgreSQL instalado)**

> ⚠️ **Desvantagem:** TimescaleDB não disponível localmente = ambientes dev/prod diferentes

#### Pré-requisitos
- Python 3.12.10+
- PostgreSQL 17+ (instalado localmente)
- Git
- virtualenv

#### Passos de Instalação

```bash
# 1. Clone do repositório
git clone https://github.com/Miltoneo/server-app-tds-new.git
cd server-app-tds-new

# 2. Criar e ativar virtualenv
python -m virtualenv venv
.\venv\Scripts\Activate.ps1  # Windows
# source venv/bin/activate    # Linux/Mac

# 3. Instalar dependências Python
pip install -r requirements.txt
```

**Principais dependências instaladas:**
- Django==5.1.6
- psycopg2-binary (PostgreSQL)
- django-environ (gestão de .env)
- paho-mqtt==2.1.0 (telemetria IoT)
- django-axes (segurança)
- django-bootstrap5 (UI)
- django-extensions (admin tools)
- django-select2 (widgets)
- crispy-forms + crispy-bootstrap5 (forms)

```bash
# 4. Configurar banco de dados (automático)
python setup_database.py
```

**O script irá:**
1. ✅ Conectar ao PostgreSQL como admin (`postgres/postgres`)
2. ✅ Criar usuário `tsdb_django_d4j7g9`
3. ✅ Criar banco `db_tds_new`
4. ✅ Configurar permissões
5. ✅ Testar conexão
6. ⚠️ TimescaleDB não disponível (apenas em prod)

**Configuração manual (alternativa):**

```sql
-- Conectar ao PostgreSQL
psql -U postgres

-- Criar usuário
CREATE USER tsdb_django_d4j7g9 WITH PASSWORD 'DjangoTS2025TimeSeries';

-- Criar banco
CREATE DATABASE db_tds_new OWNER tsdb_django_d4j7g9;

-- Conectar ao banco
\c db_tds_new

-- Dar permissões
GRANT ALL PRIVILEGES ON DATABASE db_tds_new TO tsdb_django_d4j7g9;
```

```bash
# 5. Ajustar .env.dev para PostgreSQL padrão
# Trocar DATABASE_ENGINE para: django.db.backends.postgresql
```

### 5. Configurar Ambiente (.env)

O arquivo `environments/.env.dev` já está configurado. Credenciais padrão:

```ini
DATABASE_NAME=db_tds_new
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=tsdb_django_d4j7g9
DATABASE_PASSWORD=DjangoTS2025TimeSeries

MQTT_BROKER_HOST=localhost
MQTT_TOPIC_PREFIX=tds_new/devices
```

### 6. Validar Configuração

```bash
# Testar configuração Django
python manage.py check

# Resultado esperado: System check identified 0 issues
```

### 7. Aplicar Migrations (Futuro - Semana 2)

```bash
# Quando os modelos forem implementados:
python manage.py makemigrations
python manage.py migrate
```

### 8. Criar Superusuário (Futuro - Semana 2)

```bash
# Quando CustomUser estiver implementado:
python manage.py createsuperuser
```

### 9. Executar Servidor de Desenvolvimento

```bash
python manage.py runserver

# Acesse: http://localhost:8000/admin/
```

---

## 🏗️ ESTRUTURA DO PROJETO (Detalhada)

```
server-app-tds-new/
├── prj_tds_new/              # Configurações Django
│   ├── __init__.py
│   ├── settings.py           # ENVIRONMENT='DEV'/'PROD'
│   ├── urls.py               # URLs principais (admin, select2)
│   ├── wsgi.py               # WSGI para Gunicorn
│   └── asgi.py               # ASGI (futuro)
│
├── tds_new/                  # App principal
│   ├── __init__.py
│   ├── apps.py               # TdsNewConfig
│   └── models/               # ✅ Dia 3
│       ├── __init__.py       # Imports de modelos
│       └── base.py           # Placeholder (CustomUser, Conta - Semanas 2-3)
│
├── core/                     # Utilitários compartilhados
│   ├── context_processors.py # Context processors (não implementados ainda)
│   ├── version.py            # Versão do sistema
│   └── version.txt           # Número da versão
│
├── environments/             # Arquivos .env
│   ├── .env.dev              # Desenvolvimento (localhost)
│   ├── .env.prod             # Produção (onkoto.com.br:5443)
│   ├── .env.example          # Template
│   ├── .env.prod.example     # Template produção
│   └── README.md             # Documentação de ambientes
│
├── django_logs/              # Logs da aplicação
│
├── venv/                     # Virtualenv Python 3.12.10
│
├── setup_database.py         # ✅ Script de setup do banco (Dia 3)
├── manage.py                 # CLI Django
├── requirements.txt          # Dependências Python
├── .gitignore                # Arquivos ignorados pelo Git
├── README.md                 # Este arquivo
└── CHANGELOG.md              # Log de implementação detalhado
```

---

## 🔧 DESENVOLVIMENTO

### Comandos Úteis

```bash
# Ativar virtualenv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate     # Linux/Mac

# Verificar configuração
python manage.py check

# Executar servidor de desenvolvimento
python manage.py runserver

# Acessar shell Django
python manage.py shell

# Acessar shell do banco de dados
python manage.py dbshell

# Ver migrações pendentes (futuro)
python manage.py showmigrations

# Criar migrações (futuro)
python manage.py makemigrations

# Aplicar migrações (futuro)
python manage.py migrate

# Criar superusuário (futuro)
python manage.py createsuperuser
```

### Variáveis de Ambiente

**Desenvolvimento (`.env.dev`):**
```ini
DEBUG=True
DATABASE_HOST=localhost
DATABASE_PORT=5432
MQTT_BROKER_HOST=localhost
```

**Produção (`.env.prod`):**
```ini
DEBUG=False
DATABASE_HOST=onkoto.com.br
DATABASE_PORT=5443
MQTT_BROKER_HOST=mqtt
```

**Alternar ambiente:**
```powershell
# Windows
[System.Environment]::SetEnvironmentVariable('DJANGO_ENV', 'production', 'User')

# Linux/Mac
export DJANGO_ENV=production
```

### Estrutura de Commits

Seguimos **Conventional Commits**:

```bash
# Exemplos
git commit -m "feat(day3): configurar banco de dados PostgreSQL"
git commit -m "docs: atualizar README com instruções de instalação"
git commit -m "fix(models): corrigir validação de CustomUser"
git commit -m "refactor(views): simplificar lógica de cenários"
```

---

## 📚 DOCUMENTAÇÃO ADICIONAL

A documentação completa do projeto está no repositório **server-app-tds**:

- **[ANALISE_GREENFIELD.md](https://github.com/Miltoneo/server-app-tds/blob/master/docs/ANALISE_GREENFIELD.md)** - Decisão estratégica greenfield vs refatoração
- **[ROADMAP_DESENVOLVIMENTO.md](https://github.com/Miltoneo/server-app-tds/blob/master/docs/ROADMAP_DESENVOLVIMENTO.md)** - Plano de 12 semanas detalhado
- **[MIGRACAO_DADOS.md](https://github.com/Miltoneo/server-app-tds/blob/master/docs/MIGRACAO_DADOS.md)** - Estratégia de migração TDS → TDS New

---

## ✅ STATUS DE IMPLEMENTAÇÃO

### ✅ Semana 1 - Setup e Foundation (CONCLUÍDA - 14/02/2026)

#### ✅ Dia 1: Criação do Repositório (CONCLUÍDO - 14/02/2026)

- [x] Estrutura base copiada do CONSTRUTORA
- [x] `manage.py` configurado para `prj_tds_new`
- [x] App `tds_new` criado (`__init__.py`, `apps.py`)
- [x] Referências de 'construtora' renomeadas para 'tds_new'
- [x] Arquivos de configuração atualizados:
  - `prj_tds_new/settings.py` (PROJECT_NAME, INSTALLED_APPS)
  - `prj_tds_new/asgi.py` (DJANGO_SETTINGS_MODULE)
  - `prj_tds_new/wsgi.py` (DJANGO_SETTINGS_MODULE)
  - `core/context_processors.py` (imports de models)

#### ✅ Dia 2: Configuração de Ambiente (CONCLUÍDO - 14/02/2026)

- [x] Criar virtualenv (Python 3.12.10)
- [x] Instalar Django 5.1.6 e dependências essenciais:
  - psycopg2-binary (PostgreSQL)
  - django-environ (gestão de .env)
  - paho-mqtt==2.1.0 (telemetria IoT)
  - django-axes (segurança)
  - django-recaptcha (anti-bot)
  - django-bootstrap5 (UI)
  - django-extensions (admin tools)
  - django-select2 (widgets)
  - crispy-forms + crispy-bootstrap5 (forms)
- [x] Configurar `.env.dev`:
  - DATABASE_NAME=db_tds_new
  - MQTT_BROKER_HOST=localhost
  - MQTT_TOPIC_PREFIX=tds_new/devices
  - VISITOR_EMAIL=visitante@onkoto.com.br
  - TIMESCALE_RETENTION_DAYS=90
- [x] Limpar `settings.py`:
  - Remover django_adsense_injector, jquery, django_tables2
  - Remover middleware do CONSTRUTORA
  - Comentar AUTH_USER_MODEL (aguardando models)
- [x] Corrigir `urls.py`:
  - Remover imports construtora
  - Simplificar para admin + select2 + redirect
- [x] Validar configuração: `python manage.py check` ✅

#### ✅ Dia 3: Banco de Dados (CONCLUÍDO - 14/02/2026)

- [x] Criar banco PostgreSQL local:
  - Banco: `db_tds_new`
  - Usuário: `tsdb_django_d4j7g9` (credenciais de produção)
  - PostgreSQL: 17.7 (Debian)
- [x] Script automatizado: `setup_database.py`
  - Cria usuário e banco
  - Configura permissões
  - Testa conexão
- [x] Testar conexão Django: `python manage.py check` ✅
- [x] Criar estrutura de modelos:
  - `tds_new/models/__init__.py`
  - `tds_new/models/base.py` (placeholder)
- [x] TimescaleDB:
  - ⚠️ Não instalado localmente (opcional)
  - ✅ Disponível em produção (onkoto.com.br:5443)

#### ✅ Dias 4-5: Documentação e Testes Iniciais (CONCLUÍDO - 14/02/2026)

- [x] README.md completo com:
  - Stack tecnológico detalhado
  - Instruções de instalação passo a passo
  - Estrutura do projeto comentada
  - Comandos úteis para desenvolvimento
  - Informações sobre ambientes e configuração
- [x] CHANGELOG.md atualizado com Dia 3
- [x] Documentação de arquitetura (padrões CONSTRUTORA)
- [ ] Testes iniciais (SKIPPED - será implementado conforme necessário)

---

### 🔄 Semana 2: Modelos e Autenticação (PRÓXIMO)

#### Planejado:

**Modelos Base:**
- [ ] `CustomUser` - Modelo de usuário customizado (AbstractUser)
- [ ] `Conta` - Modelo de tenant (isolamento multi-tenant)
- [ ] `ContaMembership` - Relacionamento User ↔ Conta com roles

**Autenticação:**
- [ ] Sistema de login/logout
- [ ] Registro de usuários
- [ ] Seleção de conta ativa
- [ ] Middleware de tenant

**Migrations:**
- [ ] `python manage.py makemigrations`
- [ ] `python manage.py migrate`
- [ ] Criação de superusuário

---

## 🚀 COMO CONTRIBUIR

### 1. Fork do Repositório

```bash
# Fazer fork no GitHub
# Clonar o fork
git clone https://github.com/seu-usuario/server-app-tds-new.git
```

### 2. Criar Branch de Feature

```bash
git checkout -b feature/nome-da-feature
```

### 3. Fazer Alterações e Commit

```bash
git add .
git commit -m "feat: descrição da feature"
```

### 4. Push e Pull Request

```bash
git push origin feature/nome-da-feature
# Abrir Pull Request no GitHub
```

---

## 📝 LICENÇA

Este projeto é privado e proprietário. Todos os direitos reservados.

---

## 👥 EQUIPE

- **Arquitetura:** Baseada em CONSTRUTORA (padrões maduros)
- **Desenvolvimento:** 2 desenvolvedores full-stack
- **DevOps:** Setup automatizado (scripts Python)
- **Documentação:** Roadmap de 12 semanas detalhado

---

## 📞 SUPORTE

Para dúvidas ou suporte:
- **Documentação:** Ver arquivos em `/docs` no repositório server-app-tds
- **GitHub Issues:** https://github.com/Miltoneo/server-app-tds-new/issues
- **Roadmap:** Consultar ROADMAP_DESENVOLVIMENTO.md

---

**Última atualização:** 14/02/2026 - Semana 1 Concluída (Setup e Foundation)  
**Próximo:** Semana 2 - Implementação de Modelos e Autenticação Multi-Tenant
  - crispy-forms + crispy-bootstrap5 (forms)
- [x] Configurar `.env.dev`:
  - DATABASE_NAME=db_tds_new
  - MQTT_BROKER_HOST=localhost
  - MQTT_TOPIC_PREFIX=tds_new/devices
  - VISITOR_EMAIL=visitante@onkoto.com.br
  - TIMESCALE_RETENTION_DAYS=90
- [x] Limpar `settings.py`:
  - Remover django_adsense_injector, jquery, django_tables2
  - Remover middleware do CONSTRUTORA
  - Comentar AUTH_USER_MODEL (aguardando models)
- [x] Corrigir `urls.py`:
  - Remover imports construtora
  - Simplificar para admin + select2 + redirect
- [x] Validar configuração: `python manage.py check` ✅

#### 🔄 Dia 3: Banco de Dados (PRÓXIMO)
- [ ] Testar `python manage.py check`

---

## 🚀 PRÓXIMOS PASSOS

### 1. Criar Repositório no GitHub

```bash
# Criar repo "server-app-tds-new" no GitHub
git init
git add .
git commit -m "feat: setup inicial do projeto TDS New (Dia 1)"
git remote add origin https://github.com/Miltoneo/server-app-tds-new.git
git push -u origin main
```

### 2. Configurar Ambiente de Desenvolvimento (Dia 2)

```powershell
# Criar virtualenv
python -m virtualenv venv

# Ativar virtualenv
.\venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt

# Configurar arquivo .env.dev
# (Editar environments/.env.dev com credenciais do banco db_tds_new)

# Testar configuração
python manage.py check
```

### 3. Criar Banco de Dados (Dia 3)

```sql
-- Conectar ao PostgreSQL
psql -U postgres

-- Criar banco
CREATE DATABASE db_tds_new OWNER admin;

-- Conectar ao banco
\c db_tds_new

-- Ativar extensão TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

---

## 🔧 STACK TECNOLÓGICO

**Backend:**
- Django 5.1.6
- PostgreSQL 16 + TimescaleDB 2.17
- Redis 7.2
- Celery

**Frontend:**
- Bootstrap 5.3
- Chart.js
- Select2
- HTMX

**IoT:**
- MQTT (Mosquitto)
- Paho MQTT Client

---

## 📞 CONTATO E SUPORTE

**Equipe:** Equipe de Desenvolvimento TDS  
**Repositório Original:** [server-app-tds](https://github.com/Miltoneo/server-app-tds)  
**Documentação:** [server-app-tds/docs/](https://github.com/Miltoneo/server-app-tds/tree/master/docs)

---

**⚠️ IMPORTANTE:** Este é um projeto greenfield. O TDS atual permanece operacional durante todo o desenvolvimento.
