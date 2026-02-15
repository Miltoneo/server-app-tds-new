"""
Script para configurar TimescaleDB - Hypertable e Continuous Aggregate
Alternativa a executar o arquivo SQL via psql (que não está no PATH do Windows)
"""
import psycopg2

DATABASE_HOST = "localhost"
DATABASE_PORT = 5442
DATABASE_NAME = "db_tds_new"
DATABASE_USER = "postgres"
DATABASE_PASSWORD = "postgres"

print("=" * 80)
print("CONFIGURANDO TIMESCALEDB - HYPERTABLE E CONTINUOUS AGGREGATE")
print("=" * 80)

try:
    # Conectar ao banco
    print("\n[1/6] Conectando ao banco de dados...")
    conn = psycopg2.connect(
        dbname=DATABASE_NAME,
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
        host=DATABASE_HOST,
        port=DATABASE_PORT
    )
    conn.autocommit = True
    cursor = conn.cursor()
    print("✅ Conexão estabelecida!")
    
    # Dropar tabela incorreta se existir
    print("\n[1.5/6] Removendo tabelas antigas (se existirem)...")
    cursor.execute("DROP TABLE IF EXISTS tds_new_leituradispositivo CASCADE;")
    cursor.execute("DROP MATERIALIZED VIEW IF EXISTS tds_new_consumomensal CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS tds_new_leitura_dispositivo CASCADE;")
    print("✅ Limpeza concluída!")
    
    # Criar tabela LeituraDispositivo (managed=False no Django)
    print("\n[2/6] Criando tabela tds_new_leitura_dispositivo (managed=False)...")
    cursor.execute("""
        CREATE TABLE tds_new_leitura_dispositivo (
            id BIGSERIAL NOT NULL,
            time TIMESTAMPTZ NOT NULL,
            conta_id BIGINT NOT NULL REFERENCES conta(id) ON DELETE CASCADE,
            gateway_id BIGINT NOT NULL REFERENCES tds_new_gateway(id) ON DELETE CASCADE,
            dispositivo_id BIGINT NOT NULL REFERENCES tds_new_dispositivo(id) ON DELETE CASCADE,
            valor NUMERIC(15, 3) NOT NULL,
            unidade VARCHAR(20),
            payload_raw JSONB
        );
    """)
    print("✅ Tabela criada!")
    
    # Converter para hypertable (se ainda não for)
    print("\n[3/6] Convertendo para hypertable...")
    try:
        cursor.execute("""
            SELECT create_hypertable(
                'tds_new_leitura_dispositivo',
                'time',
                chunk_time_interval => INTERVAL '1 day',
                if_not_exists => TRUE
            );
        """)
        print("✅ Hypertable criada com sucesso!")
    except Exception as e:
        if "already a hypertable" in str(e).lower():
            print("⚠️  Tabela já é uma hypertable. Pulando...")
        else:
            raise
    
    # Criar índices adicionais
    print("\n[4/6] Criando índices adicionais...")
    indexes = [
        ("idx_leitura_id", "CREATE INDEX IF NOT EXISTS idx_leitura_id ON tds_new_leitura_dispositivo (id);"),
        ("idx_leitura_time", "CREATE INDEX IF NOT EXISTS idx_leitura_time ON tds_new_leitura_dispositivo (time DESC);"),
        ("idx_leitura_conta_time", "CREATE INDEX IF NOT EXISTS idx_leitura_conta_time ON tds_new_leitura_dispositivo (conta_id, time DESC);"),
        ("idx_leitura_dispositivo_time", "CREATE INDEX IF NOT EXISTS idx_leitura_dispositivo_time ON tds_new_leitura_dispositivo (dispositivo_id, time DESC);"),
        ("idx_leitura_gateway_time", "CREATE INDEX IF NOT EXISTS idx_leitura_gateway_time ON tds_new_leitura_dispositivo (gateway_id, time DESC);"),
        ("idx_leitura_conta_dispositivo_time", "CREATE INDEX IF NOT EXISTS idx_leitura_conta_dispositivo_time ON tds_new_leitura_dispositivo (conta_id, dispositivo_id, time DESC);"),
    ]
    
    for idx_name, sql in indexes:
        try:
            cursor.execute(sql)
            print(f"   ✅ Índice {idx_name} criado")
        except Exception as e:
            print(f"   ⚠️  {idx_name}: {str(e)[:50]}")
    
    # Criar continuous aggregate (materialized view)
    print("\n[5/6] Criando continuous aggregate para consumo mensal...")
    try:
        cursor.execute("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS tds_new_consumomensal
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
        """)
        print("✅ Continuous aggregate criada!")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("⚠️  Continuous aggregate já existe. Pulando...")
        else:
            raise
    
    # Configurar política de refresh automático
    print("\n[6/6] Configurando refresh policy...")
    try:
        cursor.execute("""
            SELECT add_continuous_aggregate_policy(
                'tds_new_consumomensal',
                start_offset => INTERVAL '30 days',
                end_offset => INTERVAL '1 hour',
                schedule_interval => INTERVAL '1 hour',
                if_not_exists => TRUE
            );
        """)
        print("✅ Refresh policy configurada (atualização a cada 1 hora)!")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("⚠️  Refresh policy já existe. Pulando...")
        else:
            print(f"⚠️  Erro ao configurar refresh policy: {str(e)[:100]}")
    
    # Verificar configuração
    print("\n" + "=" * 80)
    print("VALIDANDO CONFIGURAÇÃO")
    print("=" * 80)
    
    cursor.execute("""
        SELECT hypertable_name, num_dimensions 
        FROM timescaledb_information.hypertables 
        WHERE hypertable_name = 'tds_new_leitura_dispositivo';
    """)
    hypertables = cursor.fetchall()
    if hypertables:
        print(f"\n✅ Hypertable: {hypertables[0][0]} (dimensões: {hypertables[0][1]})")
    
    cursor.execute("""
        SELECT view_name, materialized_only 
        FROM timescaledb_information.continuous_aggregates 
        WHERE view_name = 'tds_new_consumomensal';
    """)
    aggregates = cursor.fetchall()
    if aggregates:
        print(f"✅ Continuous Aggregate: {aggregates[0][0]}")
    
    cursor.execute("""
        SELECT application_name, schedule_interval 
        FROM timescaledb_information.jobs 
        WHERE application_name LIKE '%tds_new_consumomensal%'
        LIMIT 1;
    """)
    jobs = cursor.fetchall()
    if jobs:
        print(f"✅ Refresh Job: {jobs[0][1]} de intervalo")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ TIMESCALEDB CONFIGURADO COM SUCESSO!")
    print("=" * 80)
    print("\nPróximo passo:")
    print("  python manage.py createsuperuser    # Criar usuário admin")
    print("  python manage.py runserver          # Iniciar servidor")

except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
