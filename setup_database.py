"""
Script para configurar banco de dados PostgreSQL local para TDS New
Dia 3 do roadmap: Criação de banco, usuário e extensão TimescaleDB

Credenciais de admin PostgreSQL: postgres/postgres
Credenciais da aplicação: tsdb_django_d4j7g9/DjangoTS2025TimeSeries
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

# Configurações
ADMIN_USER = 'postgres'
ADMIN_PASSWORD = 'postgres'
HOST = 'localhost'
PORT = 5432

APP_USER = 'tsdb_django_d4j7g9'
APP_PASSWORD = 'DjangoTS2025TimeSeries'
DATABASE_NAME = 'db_tds_new'


def print_step(message):
    """Print formatado para os passos"""
    print(f"\n{'=' * 70}")
    print(f"  {message}")
    print('=' * 70)


def main():
    print_step("🚀 SETUP DATABASE - TDS NEW (Dia 3)")
    
    # ========================================================================
    # PASSO 1: Conectar ao PostgreSQL como admin
    # ========================================================================
    print_step("PASSO 1: Conectando ao PostgreSQL como admin (postgres)")
    
    try:
        conn_admin = psycopg2.connect(
            dbname='postgres',
            user=ADMIN_USER,
            password=ADMIN_PASSWORD,
            host=HOST,
            port=PORT
        )
        conn_admin.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn_admin.cursor()
        print("✅ Conectado com sucesso ao PostgreSQL!")
        
    except psycopg2.OperationalError as e:
        print(f"❌ ERRO: Não foi possível conectar ao PostgreSQL:")
        print(f"   {e}")
        print("\n💡 Verifique se:")
        print("   1. PostgreSQL está instalado")
        print("   2. Serviço PostgreSQL está rodando")
        print("   3. Credenciais postgres/postgres estão corretas")
        sys.exit(1)
    
    # ========================================================================
    # PASSO 2: Criar usuário da aplicação
    # ========================================================================
    print_step(f"PASSO 2: Criando usuário '{APP_USER}'")
    
    try:
        # Verificar se usuário já existe
        cursor.execute(
            "SELECT 1 FROM pg_roles WHERE rolname = %s",
            (APP_USER,)
        )
        user_exists = cursor.fetchone()
        
        if user_exists:
            print(f"⚠️  Usuário '{APP_USER}' já existe. Pulando criação.")
        else:
            cursor.execute(
                f"CREATE USER {APP_USER} WITH PASSWORD %s",
                (APP_PASSWORD,)
            )
            print(f"✅ Usuário '{APP_USER}' criado com sucesso!")
            
    except Exception as e:
        print(f"❌ ERRO ao criar usuário: {e}")
        cursor.close()
        conn_admin.close()
        sys.exit(1)
    
    # ========================================================================
    # PASSO 3: Criar banco de dados
    # ========================================================================
    print_step(f"PASSO 3: Criando banco de dados '{DATABASE_NAME}'")
    
    try:
        # Verificar se banco já existe
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DATABASE_NAME,)
        )
        db_exists = cursor.fetchone()
        
        if db_exists:
            print(f"⚠️  Banco '{DATABASE_NAME}' já existe. Pulando criação.")
        else:
            cursor.execute(
                f"CREATE DATABASE {DATABASE_NAME} OWNER {APP_USER}"
            )
            print(f"✅ Banco '{DATABASE_NAME}' criado com sucesso!")
            
    except Exception as e:
        print(f"❌ ERRO ao criar banco: {e}")
        cursor.close()
        conn_admin.close()
        sys.exit(1)
    
    # Fechar conexão admin
    cursor.close()
    conn_admin.close()
    
    # ========================================================================
    # PASSO 4: Conectar ao banco criado e ativar TimescaleDB
    # ========================================================================
    print_step(f"PASSO 4: Ativando extensão TimescaleDB no banco '{DATABASE_NAME}'")
    
    try:
        conn_db = psycopg2.connect(
            dbname=DATABASE_NAME,
            user=ADMIN_USER,
            password=ADMIN_PASSWORD,
            host=HOST,
            port=PORT
        )
        conn_db.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor_db = conn_db.cursor()
        
        # Tentar ativar TimescaleDB
        try:
            cursor_db.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
            print("✅ Extensão TimescaleDB ativada com sucesso!")
            
            # Verificar versão
            cursor_db.execute("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb';")
            version = cursor_db.fetchone()
            if version:
                print(f"   Versão: {version[0]}")
                
        except Exception as e:
            print(f"⚠️  TimescaleDB não foi ativado: {e}")
            print("   O banco funcionará normalmente, mas sem recursos de time-series.")
            print("   Para instalar TimescaleDB: https://docs.timescale.com/install/")
        
        # Listar extensões instaladas
        cursor_db.execute("SELECT extname, extversion FROM pg_extension ORDER BY extname;")
        extensions = cursor_db.fetchall()
        print(f"\n📦 Extensões instaladas em '{DATABASE_NAME}':")
        for ext_name, ext_version in extensions:
            print(f"   - {ext_name} ({ext_version})")
        
        cursor_db.close()
        conn_db.close()
        
    except Exception as e:
        print(f"❌ ERRO ao configurar extensões: {e}")
        sys.exit(1)
    
    # ========================================================================
    # PASSO 5: Confirmar permissões
    # ========================================================================
    print_step(f"PASSO 5: Confirmando permissões do usuário '{APP_USER}'")
    
    try:
        conn_admin = psycopg2.connect(
            dbname='postgres',
            user=ADMIN_USER,
            password=ADMIN_PASSWORD,
            host=HOST,
            port=PORT
        )
        conn_admin.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn_admin.cursor()
        
        # Dar permissões adicionais se necessário
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DATABASE_NAME} TO {APP_USER};")
        print(f"✅ Permissões confirmadas para usuário '{APP_USER}'")
        
        cursor.close()
        conn_admin.close()
        
    except Exception as e:
        print(f"⚠️  Aviso ao confirmar permissões: {e}")
    
    # ========================================================================
    # PASSO 6: Testar conexão com credenciais da aplicação
    # ========================================================================
    print_step(f"PASSO 6: Testando conexão com credenciais da aplicação")
    
    try:
        conn_test = psycopg2.connect(
            dbname=DATABASE_NAME,
            user=APP_USER,
            password=APP_PASSWORD,
            host=HOST,
            port=PORT
        )
        cursor_test = conn_test.cursor()
        cursor_test.execute("SELECT version();")
        pg_version = cursor_test.fetchone()[0]
        print(f"✅ Conexão bem-sucedida com usuário '{APP_USER}'!")
        print(f"   PostgreSQL: {pg_version.split(',')[0]}")
        
        cursor_test.close()
        conn_test.close()
        
    except Exception as e:
        print(f"❌ ERRO ao testar conexão: {e}")
        sys.exit(1)
    
    # ========================================================================
    # RESUMO FINAL
    # ========================================================================
    print_step("✅ SETUP CONCLUÍDO COM SUCESSO!")
    
    print(f"""
📋 RESUMO DA CONFIGURAÇÃO:
   
   Banco de dados:  {DATABASE_NAME}
   Host:            {HOST}:{PORT}
   Usuário:         {APP_USER}
   Senha:           {APP_PASSWORD}
   
🔧 PRÓXIMOS PASSOS:
   
   1. Testar Django:
      python manage.py check
   
   2. Criar estrutura de modelos:
      mkdir tds_new\\models
      New-Item -Path "tds_new\\models\\__init__.py" -ItemType File
      New-Item -Path "tds_new\\models\\base.py" -ItemType File
   
   3. Fazer commit:
      git add .
      git commit -m "feat(day3): configurar banco de dados PostgreSQL + TimescaleDB"
      git push
   
🎉 Dia 3 do roadmap concluído!
""")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelado pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERRO INESPERADO: {e}")
        sys.exit(1)
