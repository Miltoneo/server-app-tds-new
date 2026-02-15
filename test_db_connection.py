"""
Script para validar conexão ao PostgreSQL e criar banco/usuário se necessário.

Uso:
    python test_db_connection.py
"""
import psycopg2
from psycopg2 import sql

# Configurações do .env.dev
ADMIN_USER = "postgres"
ADMIN_PASSWORD = "postgres"
DATABASE_HOST = "localhost"
DATABASE_PORT = 5442

APP_USER = "tsdb_django_d4j7g9"
APP_PASSWORD = "DjangoTS2025TimeSeries"
APP_DATABASE = "db_tds_new"

print("=" * 80)
print("VALIDANDO CONEXÃO AO POSTGRESQL + TIMESCALEDB")
print("=" * 80)

# Passo 1: Conectar como admin ao banco postgres padrão
print("\n[1/5] Conectando como admin ao banco 'postgres'...")
try:
    admin_conn = psycopg2.connect(
        dbname="postgres",
        user=ADMIN_USER,
        password=ADMIN_PASSWORD,
        host=DATABASE_HOST,
        port=DATABASE_PORT
    )
    admin_conn.autocommit = True
    admin_cursor = admin_conn.cursor()
    print("✅ Conexão como admin bem-sucedida!")
except Exception as e:
    print(f"❌ ERRO ao conectar como admin: {e}")
    print("\nVERIFIQUE:")
    print("1. PostgreSQL está rodando na porta 5442?")
    print("2. Senha do usuário 'postgres' está correta?")
    print("3. Docker container está ativo?")
    exit(1)

# Passo 2: Verificar se o usuário da aplicação existe
print(f"\n[2/5] Verificando se usuário '{APP_USER}' existe...")
admin_cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (APP_USER,))
user_exists = admin_cursor.fetchone()

if not user_exists:
    print(f"⚠️  Usuário '{APP_USER}' não existe. Criando...")
    try:
        admin_cursor.execute(
            sql.SQL("CREATE USER {} WITH PASSWORD %s").format(sql.Identifier(APP_USER)),
            (APP_PASSWORD,)
        )
        print(f"✅ Usuário '{APP_USER}' criado com sucesso!")
    except Exception as e:
        print(f"❌ ERRO ao criar usuário: {e}")
        exit(1)
else:
    print(f"✅ Usuário '{APP_USER}' já existe!")

# Passo 3: Verificar se o banco de dados existe
print(f"\n[3/5] Verificando se banco '{APP_DATABASE}' existe...")
admin_cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (APP_DATABASE,))
db_exists = admin_cursor.fetchone()

if not db_exists:
    print(f"⚠️  Banco '{APP_DATABASE}' não existe. Criando...")
    try:
        admin_cursor.execute(
            sql.SQL("CREATE DATABASE {} OWNER {}").format(
                sql.Identifier(APP_DATABASE),
                sql.Identifier(APP_USER)
            )
        )
        print(f"✅ Banco '{APP_DATABASE}' criado com sucesso!")
    except Exception as e:
        print(f"❌ ERRO ao criar banco: {e}")
        exit(1)
else:
    print(f"✅ Banco '{APP_DATABASE}' já existe!")

# Passo 4: Garantir permissões do usuário no banco
print(f"\n[4/5] Garantindo permissões de '{APP_USER}' no banco '{APP_DATABASE}'...")
try:
    admin_cursor.execute(
        sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
            sql.Identifier(APP_DATABASE),
            sql.Identifier(APP_USER)
        )
    )
    print(f"✅ Permissões concedidas!")
except Exception as e:
    print(f"❌ ERRO ao conceder permissões: {e}")

admin_conn.close()

# Passo 5: Testar conexão como usuário da aplicação
print(f"\n[5/5] Testando conexão como '{APP_USER}' ao banco '{APP_DATABASE}'...")
try:
    app_conn = psycopg2.connect(
        dbname=APP_DATABASE,
        user=APP_USER,
        password=APP_PASSWORD,
        host=DATABASE_HOST,
        port=DATABASE_PORT
    )
    app_cursor = app_conn.cursor()
    app_cursor.execute("SELECT version();")
    version = app_cursor.fetchone()
    print("✅ Conexão como usuário da aplicação bem-sucedida!")
    print(f"   PostgreSQL Version: {version[0][:50]}...")
    
    # Verificar se TimescaleDB está disponível
    app_cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'timescaledb';")
    timescale = app_cursor.fetchone()
    if timescale:
        print("✅ Extensão TimescaleDB disponível!")
    else:
        print("⚠️  TimescaleDB não está habilitado neste banco. Execute:")
        print(f"   psql -U {ADMIN_USER} -d {APP_DATABASE} -c 'CREATE EXTENSION IF NOT EXISTS timescaledb;'")
    
    app_conn.close()
except Exception as e:
    print(f"❌ ERRO ao conectar como usuário da aplicação: {e}")
    print("\nVERIFIQUE:")
    print(f"1. Senha do usuário '{APP_USER}' está correta no .env.dev")
    print(f"2. Usuário tem permissões no banco '{APP_DATABASE}'")
    exit(1)

print("\n" + "=" * 80)
print("✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO!")
print("=" * 80)
print("\nPróximo passo:")
print("  python manage.py migrate")
