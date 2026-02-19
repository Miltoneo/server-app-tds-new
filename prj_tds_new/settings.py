"""
Django settings for prj_tds_new project.

Sistema de Telemetria e Monitoramento IoT - Multi-tenant SaaS
"""

import os
import sys
import environ
from pathlib import Path
from core.version import get_version

# =============================================================================
# CONFIGURAÇÕES BÁSICAS DO PROJETO
# =============================================================================

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Adiciona diretório www ao sys.path para permitir importação de shared
WWW_DIR = BASE_DIR.parent
if str(WWW_DIR) not in sys.path:
    sys.path.insert(0, str(WWW_DIR))

# Nome do projeto (para identificação no ambiente multi-projeto)
PROJECT_NAME = 'tds_new'

# Versão da aplicação
APP_VERSION = get_version(force_file=True)

# =============================================================================
# CONFIGURAÇÃO DE AMBIENTE E MODO DE OPERAÇÃO
# =============================================================================
# Inicializa leitor de variáveis de ambiente
env = environ.Env()

# ⚠️ MELHORES PRÁTICAS: Configurações Centralizadas no settings.py
#
# ENVIRONMENT: Define qual arquivo .env será carregado ('DEV' ou 'PROD')
# DEBUG: Flag Python/Django para exibir erros detalhados (True/False)
#
# Altere manualmente conforme o ambiente:
# - Desenvolvimento: ENVIRONMENT='DEV', DEBUG=True
# - Produção: ENVIRONMENT='PROD', DEBUG=False

ENVIRONMENT = 'DEV'  # Valores: 'DEV' ou 'PROD'
DEBUG = True        # True=exibe erros detalhados | False=oculta erros

# Carrega arquivo .env baseado no ENVIRONMENT
env_dir = os.path.join(BASE_DIR, 'environments')
env_mode = 'dev' if ENVIRONMENT == 'DEV' else 'prod'
env_file = os.path.join(env_dir, f'.env.{env_mode}')

if os.path.exists(env_file):
    # Carregar variáveis de ambiente do arquivo específico
    environ.Env.read_env(env_file)
    print(f"[CONFIG] {PROJECT_NAME} | Ambiente: {ENVIRONMENT} | DEBUG: {DEBUG} | Arquivo: .env.{env_mode}")
    print(f"[DEBUG] Arquivo .env encontrado: {env_file}")
else:
    raise FileNotFoundError(
        f"Arquivo não encontrado: {env_file}\n"
        f"Certifique-se de que existe: environments/.env.{env_mode}"
    )

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-ngjj!z$$f^h-0-d(05*hw(r6^jx_7a0hp_nbk^xl_x&b7!8cy+')

# Hosts permitidos
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost', 'www.onkoto.com.br', 'onkoto.com.br', '[::1]', '*'])

# Silenciar system checks para desenvolvimento/runtime
SILENCED_SYSTEM_CHECKS = [
    'django_recaptcha.recaptcha_test_key_error',  # Chaves de teste do reCAPTCHA
    'axes.W002',  # AxesMiddleware não obrigatório (usando apenas signals)
    'axes.W003',  # AxesStandaloneBackend não obrigatório
    # Removidos após refatoração do shared package para abstract models:
    # 'fields.E300',  # Cross-app references (shared.assinaturas → medicos)
    # 'fields.E307',  # Lazy references para apps não instalados
]

# =============================================================================
# APLICAÇÕES DJANGO
# =============================================================================

INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Apps do projeto
    'tds_new.apps.TdsNewConfig',
    
    # Apps de terceiros essenciais
    'axes',  # Django-axes para proteção de login
    'django_recaptcha',  # reCAPTCHA do Google
    'django_bootstrap5',
    'mathfilters',
    'django_extensions', 
    'django_select2',
    'crispy_forms',
    'crispy_bootstrap5',
]

# =============================================================================
# MIDDLEWARE
# =============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    
    # Django-axes: REMOVIDO - usando apenas signals para controle manual
    # 'axes.middleware.AxesMiddleware',  # ← DESABILITADO para tela customizada
    
    # SaaS Multi-tenant Middleware (Week 3)
    'tds_new.middleware.TenantMiddleware',
    'tds_new.middleware.LicenseValidationMiddleware',
    
    # 🆕 Week 8: Proteção administrativa
    'tds_new.middleware.SuperAdminMiddleware',
    
    # Debug Middleware (apenas em desenvolvimento)
    'tds_new.middleware.SessionDebugMiddleware',
]

# =============================================================================
# CONFIGURAÇÕES DE URL E TEMPLATES
# =============================================================================

ROOT_URLCONF = 'prj_tds_new.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # Busca apenas nas pastas dos apps
        'APP_DIRS': True,  # Busca automática em templates/ de cada app
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                
                # Custom Context Processors (Week 3)
                'core.context_processors.app_version',
                'core.context_processors.conta_context',
                'core.context_processors.session_context',
                'core.context_processors.usuario_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'prj_tds_new.wsgi.application'

# =============================================================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# =============================================================================

# Forçar encoding UTF-8 para evitar problemas no Windows
os.environ['PGCLIENTENCODING'] = 'UTF8'
# Desabilitar busca por arquivos de configuração do PostgreSQL
os.environ.pop('PGSYSCONFDIR', None)
os.environ.pop('PGSERVICEFILE', None)

DATABASES = {
    'default': {
        'ENGINE': env('DATABASE_ENGINE'),
        'NAME': env('DATABASE_NAME'),
        'USER': env('DATABASE_USER'),
        'PASSWORD': env('DATABASE_PASSWORD'),
        'HOST': env('DATABASE_HOST'),
        'PORT': env('DATABASE_PORT'),
        'OPTIONS': {
            'connect_timeout': 10,
            'client_encoding': 'UTF8',
            'options': '-c client_encoding=UTF8',
        },
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }
}

# =============================================================================
# CONFIGURAÇÃO DE CACHE (REDIS)
# =============================================================================

REDIS_HOST = env('REDIS_HOST', default='localhost')
REDIS_PORT = env('REDIS_PORT', default='6379')
REDIS_PASSWORD = env('REDIS_PASSWORD', default='StrongRedisPass2024!')
USE_REDIS = env.bool('USE_REDIS', default=False)  # Desabilitado por padrão para desenvolvimento

# Configuração de cache com fallback para banco de dados se Redis não estiver disponível
if USE_REDIS:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "CONNECTION_POOL_KWARGS": {
                    "retry_on_timeout": True,
                    "socket_keepalive": True,
                    "socket_keepalive_options": {},
                }
            },
        },
        "select2": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/2",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "CONNECTION_POOL_KWARGS": {
                    "retry_on_timeout": True,
                    "socket_keepalive": True,
                    "socket_keepalive_options": {},
                }
            },
        }
    }
else:
    # Fallback: usa cache de banco de dados para desenvolvimento
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "cache_table",
        },
        "select2": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "select2_cache_table",
        }
    }

# =============================================================================
# CONFIGURAÇÕES DE AUTENTICAÇÃO
# =============================================================================

# Modelo de usuário customizado (usa email como USERNAME_FIELD)
AUTH_USER_MODEL = 'tds_new.CustomUser'

AUTHENTICATION_BACKENDS = [
    # REMOVIDO: 'axes.backends.AxesStandaloneBackend' - causa conflito com authenticate()
    # django-axes funciona via MIDDLEWARE e SIGNALS, não precisa de backend
    'django.contrib.auth.backends.ModelBackend',
]

# ⭐ URLs de Autenticação - Redirecionam para o Login Seguro (Fase 1)
LOGIN_URL = '/construtora/auth/login-secure/'
LOGIN_REDIRECT_URL = 'construtora:index'
LOGOUT_REDIRECT_URL = '/construtora/auth/login-secure/'

# Validação de senhas
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =============================================================================
# CONFIGURAÇÕES DE SEGURANÇA
# =============================================================================

# Configurações de segurança (valores definidos no .env)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=False)
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=False)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=False)

# =============================================================================
# CONFIGURAÇÕES DE INTERNACIONALIZAÇÃO
# =============================================================================

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True

# Formatos customizados - NOTA: No Django 5.x, USE_L10N está deprecado
# A formatação de números deve ser feita via:
# 1. Template tag {% load l10n %} + {{ valor|localize }}
# 2. Filtros customizados (br_decimal, br_currency, br_percent)
# 3. Arquivo construtora/formats/pt_BR/formats.py
DATE_INPUT_FORMATS = ('%d-%m-%Y', '%d-%m-%y',)
FORMAT_MODULE_PATH = ['construtora.formats']

# =============================================================================
# CONFIGURAÇÕES DE ARQUIVOS ESTÁTICOS
# =============================================================================

STATIC_URL = '/static/construtora/'
# Multi-repo: cada app tem seu próprio diretório de static
STATIC_ROOT = '/var/server-app/www/construtora/static'

STATICFILES_DIRS = [
    BASE_DIR / 'staticfiles',  # Arquivos estáticos do projeto construtora
]

# =============================================================================
# CONFIGURAÇÕES DE EMAIL
# =============================================================================

# Backend de e-mail: SMTP direto
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)

DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)
SERVER_EMAIL = env('SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)

# URL Base do Sistema (usada para links em e-mails e notificações)
BASE_URL = env('BASE_URL')
SITE_URL = BASE_URL  # Manter compatibilidade com código existente

# =============================================================================
# CONFIGURAÇÕES DE BIBLIOTECAS TERCEIRAS
# =============================================================================

# Django Select2
SELECT2_CACHE_BACKEND = "select2"
SELECT2_JS = ''  # Desabilita injeção automática (controle manual no template)
SELECT2_CSS = ''

# Django Crispy Forms
CRISPY_TEMPLATE_PACK = "bootstrap5"
CRISPY_ALLOWED_TEMPLATE_PACKS = ["bootstrap5"]

# =============================================================================
# CONFIGURAÇÕES GERAIS
# =============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# CONFIGURAÇÃO DE LOGGING
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'django_logs' / 'django.log',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'loggers': {
        'despesas.debug': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'auth.debug': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'construtora.signals_financeiro': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'construtora.views_faturamento': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# =============================================================================
# CONFIGURAÇÕES DE SEGURANÇA - DJANGO-AXES
# =============================================================================
# Django-Axes funciona em MODO HÍBRIDO:
# - SIGNALS: Rastreia tentativas automaticamente (via user_login_failed)
# - SEM MIDDLEWARE: View tem controle total do bloqueio e tela customizada
# - Benefício: Tela de bloqueio bonita ao invés de HTTP 403/429
# =============================================================================

from datetime import timedelta

# Limite de tentativas de login antes de bloquear
AXES_FAILURE_LIMIT = 5

# Tempo de bloqueio (5 minutos) - Ajustado para melhor UX
AXES_COOLOFF_TIME = timedelta(minutes=5)

# ⭐ Bloquear APENAS por USERNAME (não por IP)
# Permite tentar outro usuário do mesmo computador/IP
AXES_LOCKOUT_PARAMETERS = ['username']  # ← Removido 'ip_address'

# ⭐ Nome do campo de username no formulário de login
AXES_USERNAME_FORM_FIELD = 'username'  # Campo do AuthenticationForm

# ⭐ Função callable para extrair username do request
# Busca em request.POST['username'] primeiro, depois em credentials
def axes_username_callable(request, credentials):
    """Extrai username do request ou credentials"""
    # Tenta pegar do POST data primeiro
    username = request.POST.get('username', None)
    if username:
        return username
    # Se não, tenta pegar dos credentials do authenticate() (se existir)
    if credentials:
        return credentials.get('username', None)
    return None

AXES_USERNAME_CALLABLE = 'prj_tds_new.settings.axes_username_callable'

# Resetar contador de tentativas após login bem-sucedido
AXES_RESET_ON_SUCCESS = True

# Habilitar interface admin do axes
AXES_ENABLE_ADMIN = True

# Sistema está atrás de proxy reverso (Nginx, etc)
AXES_BEHIND_REVERSE_PROXY = True

# Cache dedicado para axes (usa Redis)
AXES_CACHE = 'axes'

# ⭐ CONFIGURAÇÃO CRÍTICA: Usar APENAS SIGNALS, não backends
# Isso garante que authenticate() sem request= ainda dispare o axes
AXES_ONLY_ALLOW_WHITELIST = False
AXES_NEVER_LOCKOUT_WHITELIST = False
AXES_NEVER_LOCKOUT_GET = True

# ⭐ DESABILITA resposta automática do middleware (403/429)
# A view verifica manualmente e renderiza tela customizada
AXES_ONLY_WHITELIST = False
AXES_LOCK_OUT_AT_FAILURE = True  # ← Marca como bloqueado no banco
AXES_LOCKOUT_TEMPLATE = None  # ← Sem template automático
AXES_LOCKOUT_URL = None  # ← Sem redirecionamento automático

# IP header para usar quando atrás de proxy
AXES_IPWARE_PROXY_COUNT = 1
AXES_IPWARE_META_PRECEDENCE_ORDER = [
    'HTTP_X_FORWARDED_FOR',
    'X_FORWARDED_FOR',
    'HTTP_CLIENT_IP',
    'HTTP_X_REAL_IP',
    'HTTP_X_FORWARDED',
    'HTTP_X_CLUSTER_CLIENT_IP',
    'HTTP_FORWARDED_FOR',
    'HTTP_FORWARDED',
    'HTTP_VIA',
    'REMOTE_ADDR',
]

# =============================================================================
# CONFIGURAÇÕES DE SEGURANÇA - RECAPTCHA
# =============================================================================

# ⭐ DESENVOLVIMENTO: Chaves de teste oficiais do Google
# Estas chaves SEMPRE passam a validação (apenas para desenvolvimento/testes)
# Fonte: https://developers.google.com/recaptcha/docs/faq#id-like-to-run-automated-tests-with-recaptcha.-what-should-i-do

# 🔧 PARA PRODUÇÃO: Obter chaves reais em https://www.google.com/recaptcha/admin/create
# Escolha "reCAPTCHA v2" > "Checkbox" (não Invisible)
# Adicione seus domínios: localhost, 127.0.0.1, seu-dominio.com.br
# Configure as chaves no arquivo .env (nunca commite chaves reais no código!)

# Temporarily load from env like medicos does
RECAPTCHA_PUBLIC_KEY = env('RECAPTCHA_PUBLIC_KEY', default='6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI')
RECAPTCHA_PRIVATE_KEY = env('RECAPTCHA_PRIVATE_KEY', default='6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe')
# =============================================================================
# CONFIGURAÇÕES DE SEGURANÇA GERAIS
# =============================================================================

# Proteção XSS
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Configurações de Cookies (valores definidos no .env)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Timeout de sessão (30 minutos de inatividade)
SESSION_COOKIE_AGE = 1800
SESSION_SAVE_EVERY_REQUEST = True  # Renovar a cada request

# =============================================================================
# CONFIGURAÇÕES DE EMAIL
# =============================================================================

EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=25)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=False)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')

# Autenticação condicional: não autenticar APENAS para localhost
if EMAIL_HOST.lower() in ['localhost', '127.0.0.1', '::1']:
    EMAIL_HOST_USER = ''
    EMAIL_HOST_PASSWORD = ''

# Remetente padrão
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@onkoto.com.br')
SERVER_EMAIL = env('SERVER_EMAIL', default='noreply@onkoto.com.br')

# BASE_URL para emails (links de ativação, redefinição de senha, etc)
BASE_URL = env('BASE_URL', default=None) or env('SITE_URL', default=None) or (
    'https://www.onkoto.com.br' if ENVIRONMENT == 'PROD' else 'http://localhost:8000'
)

# =============================================================================
# MERCADO PAGO - CONFIGURAÇÕES DE PAGAMENTO
# =============================================================================
# Credenciais do Mercado Pago (definidas no .env)
MERCADOPAGO_ACCESS_TOKEN = env('MERCADOPAGO_ACCESS_TOKEN', default='')
MERCADOPAGO_PUBLIC_KEY = env('MERCADOPAGO_PUBLIC_KEY', default='')
MERCADOPAGO_WEBHOOK_SECRET = env('MERCADOPAGO_WEBHOOK_SECRET', default='')

# Credenciais específicas para SANDBOX (desenvolvimento)
MERCADOPAGO_ACCESS_TOKEN_SANDBOX = env('MERCADOPAGO_ACCESS_TOKEN_SANDBOX', default='')
MERCADOPAGO_PUBLIC_KEY_SANDBOX = env('MERCADOPAGO_PUBLIC_KEY_SANDBOX', default='')
MERCADOPAGO_WEBHOOK_SECRET_SANDBOX = env('MERCADOPAGO_WEBHOOK_SECRET_SANDBOX', default='')

# URLs de retorno após pagamento
SUCCESS_URL = env('SUCCESS_URL', default='')
FAILURE_URL = env('FAILURE_URL', default='')
PENDING_URL = env('PENDING_URL', default='')
WEBHOOK_URL = env('WEBHOOK_URL', default='')

# Configurações de assinatura
ASSINATURA_VALIDATION_ENABLED = env.bool('ASSINATURA_VALIDATION_ENABLED', default=True)
ASSINATURA_GRACE_PERIOD_DAYS = env.int('ASSINATURA_GRACE_PERIOD_DAYS', default=7)
ASSINATURA_ALLOW_GRACE_PERIOD = env.bool('ASSINATURA_ALLOW_GRACE_PERIOD', default=True)

# =============================================================================
# MQTT BROKER - CONFIGURAÇÕES DE TELEMETRIA IOT
# =============================================================================
# Configurações do broker MQTT (Mosquitto)
MQTT_BROKER_HOST = env('MQTT_BROKER_HOST', default='localhost')
MQTT_BROKER_PORT = env.int('MQTT_BROKER_PORT', default=1883)
MQTT_BROKER_PORT_TLS = env.int('MQTT_BROKER_PORT_TLS', default=8883)

# Autenticação do Consumer Django (ambiente sem mTLS)
MQTT_BROKER_USER = env('MQTT_BROKER_USER', default=None)
MQTT_BROKER_PASSWORD = env('MQTT_BROKER_PASSWORD', default=None)

# Topics e prefixos
MQTT_TOPIC_PREFIX = env('MQTT_TOPIC_PREFIX', default='tds_new/devices')

# TLS/mTLS (certificados X.509) - apenas produção
MQTT_USE_TLS = env.bool('MQTT_USE_TLS', default=False)
MQTT_CA_CERTS = env('MQTT_CA_CERTS', default='/app/certs/ca.crt')
MQTT_CERTFILE = env('MQTT_CERTFILE', default='/app/certs/django-consumer-cert.pem')
MQTT_KEYFILE = env('MQTT_KEYFILE', default='/app/certs/django-consumer-key.pem')

# Keepalive (em segundos)
MQTT_KEEPALIVE = env.int('MQTT_KEEPALIVE', default=60)

# =============================================================================
# PKI — CERTIFICATE AUTHORITY (assinatura de certificados de dispositivos IoT)
# =============================================================================
# Caminhos locais: certs/ca/ (fora do diretório estático, nunca servido via web)
# Produção: configure via variáveis de ambiente apontando para armazenamento seguro.
#
# IMPORTANTE:
#   ca.key  → Chave privada da CA. NUNCA commitar. Em produção: use Vault/KMS.
#   ca.crt  → Certificado público da CA. Distribuído para dispositivos e brokers.

MQTT_CA_CERT_PATH = env(
    'MQTT_CA_CERT_PATH',
    default=str(BASE_DIR / 'certs' / 'ca' / 'ca.crt')
)

MQTT_CA_KEY_PATH = env(
    'MQTT_CA_KEY_PATH',
    default=str(BASE_DIR / 'certs' / 'ca' / 'ca.key')
)

# Senha da chave privada da CA (deixar vazio se não usar senha)
MQTT_CA_KEY_PASSWORD = env('MQTT_CA_KEY_PASSWORD', default='')

# Validade padrão dos certificados de dispositivos (em dias)
DEVICE_CERT_VALIDITY_DAYS = env.int('DEVICE_CERT_VALIDITY_DAYS', default=3650)  # 10 anos
