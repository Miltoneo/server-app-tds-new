# 🚀 TDS NEW - Sistema de Telemetria e Monitoramento IoT

**Projeto Greenfield** baseado na arquitetura do **CONSTRUTORA**  
**Status:** 🟢 Em Desenvolvimento - Dia 2 Concluído  
**Criado em:** 14/02/2026  
**Repositório:** https://github.com/Miltoneo/server-app-tds-new  
**Commit:** `6dc8273` - 2070 insertions, 20 files

---

## 📋 SOBRE O PROJETO

TDS New é a versão moderna e refatorada do sistema TDS, desenvolvida do zero (greenfield) seguindo os padrões arquiteturais maduros do projeto CONSTRUTORA.

### Características Principais

- ✅ **Multi-tenant**: Isolamento completo de dados por conta
- ✅ **Arquitetura Limpa**: Baseado em padrões testados e validados
- ✅ **IoT Ready**: Integração MQTT para telemetria em tempo real
- ✅ **Time-Series**: PostgreSQL + TimescaleDB para dados temporais otimizados
- ✅ **Sistema de Cenários**: Navegação centralizada e consistente

---

## 🏗️ ESTRUTURA DO PROJETO

```
server-app-tds-new/
├── prj_tds_new/              # Configurações Django
│   ├── settings.py           # ENVIRONMENT='DEV'/'PROD'
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── tds_new/                  # App principal
│   ├── __init__.py
│   └── apps.py
├── core/                     # Utilitários compartilhados
│   ├── context_processors.py
│   └── version.py
├── environments/             # Arquivos .env
│   ├── .env.dev             # Desenvolvimento (db_tds_new, MQTT)
│   ├── .env.prod            # Produção
│   └── .env.example
├── venv/                     # Virtualenv Python 3.12.10
├── django_logs/              # Logs da aplicação
├── manage.py
├── requirements.txt
└── .gitignore
```

---

## 📚 DOCUMENTAÇÃO

A documentação completa está no repositório **server-app-tds**:

- **[ANALISE_GREENFIELD.md](../server-app-tds/docs/ANALISE_GREENFIELD.md)** - Decisão estratégica greenfield vs refatoração
- **[ROADMAP_DESENVOLVIMENTO.md](../server-app-tds/docs/ROADMAP_DESENVOLVIMENTO.md)** - Plano de 12 semanas
- **[MIGRACAO_DADOS.md](../server-app-tds/docs/MIGRACAO_DADOS.md)** - Estratégia de migração TDS → TDS New

---

## ✅ STATUS DE IMPLEMENTAÇÃO

### Semana 1 - Setup e Foundation

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

#### 🔄 Dias 4-5: Documentação e Testes Iniciais (PRÓXIMO)
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
