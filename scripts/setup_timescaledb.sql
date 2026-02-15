-- ============================================================================
-- Configuração TimescaleDB para TDS New
-- ============================================================================
-- Arquivo: scripts/setup_timescaledb.sql
-- Executar após aplicar migrations Django
-- 
-- Comando: psql -U tsdb_django_d4j7g9 -d db_tds_new -f scripts/setup_timescaledb.sql
-- ============================================================================

-- Conectar ao banco correto
\c db_tds_new tsdb_django_d4j7g9

-- ============================================================================
-- 1. CRIAR HYPERTABLE PARA LEITURAS DE DISPOSITIVOS
-- ============================================================================

SELECT create_hypertable(
    'tds_new_leitura_dispositivo',
    'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Comentários na tabela
COMMENT ON TABLE tds_new_leitura_dispositivo IS 'Hypertable TimescaleDB para leituras de telemetria IoT';
COMMENT ON COLUMN tds_new_leitura_dispositivo.time IS 'Timestamp da leitura (partition key)';
COMMENT ON COLUMN tds_new_leitura_dispositivo.conta_id IS 'Isolamento multi-tenant';
COMMENT ON COLUMN tds_new_leitura_dispositivo.gateway_id IS 'Gateway que enviou a telemetria';
COMMENT ON COLUMN tds_new_leitura_dispositivo.dispositivo_id IS 'Dispositivo que gerou a leitura';
COMMENT ON COLUMN tds_new_leitura_dispositivo.valor IS 'Valor da leitura';
COMMENT ON COLUMN tds_new_leitura_dispositivo.unidade IS 'Unidade de medida (kWh, m³, L, etc)';
COMMENT ON COLUMN tds_new_leitura_dispositivo.payload_raw IS 'Payload JSON completo (opcional)';

-- ============================================================================
-- 2. ÍNDICES ADICIONAIS PARA PERFORMANCE
-- ============================================================================

-- Índice para queries por conta e tempo (mais comum)
CREATE INDEX IF NOT EXISTS idx_leitura_conta_time 
ON tds_new_leitura_dispositivo (conta_id, time DESC);

-- Índice para queries por dispositivo e tempo
CREATE INDEX IF NOT EXISTS idx_leitura_dispositivo_time 
ON tds_new_leitura_dispositivo (dispositivo_id, time DESC);

-- Índice para queries por gateway e tempo
CREATE INDEX IF NOT EXISTS idx_leitura_gateway_time 
ON tds_new_leitura_dispositivo (gateway_id, time DESC);

-- Índice composto para queries multi-tenant filtradas
CREATE INDEX IF NOT EXISTS idx_leitura_conta_dispositivo_time 
ON tds_new_leitura_dispositivo (conta_id, dispositivo_id, time DESC);

-- ============================================================================
-- 3. POLÍTICAS DE RETENÇÃO (OPCIONAL - Comentado por padrão)
-- ============================================================================
-- Descomentar para ativar política de retenção automática

-- Manter dados dos últimos 2 anos (730 dias)
-- SELECT add_retention_policy(
--     'tds_new_leitura_dispositivo',
--     INTERVAL '730 days',
--     if_not_exists => TRUE
-- );

-- ============================================================================
-- 4. CONTINUOUS AGGREGATE - CONSUMO MENSAL
-- ============================================================================

-- Criar view materializada para agregação mensal
CREATE MATERIALIZED VIEW IF NOT EXISTS tds_new_consumo_mensal
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

-- Comentários na view
COMMENT ON MATERIALIZED VIEW tds_new_consumo_mensal IS 'Continuous aggregate para consumo mensal por dispositivo';

-- ============================================================================
-- 5. POLÍTICA DE REFRESH DA CONTINUOUS AGGREGATE
-- ============================================================================

-- Atualizar a cada 1 hora, janela dos últimos 30 dias
SELECT add_continuous_aggregate_policy(
    'tds_new_consumo_mensal',
    start_offset => INTERVAL '30 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- ============================================================================
-- 6. REFRESH INICIAL DA CONTINUOUS AGGREGATE
-- ============================================================================

-- Popular a view com dados existentes (se houver)
CALL refresh_continuous_aggregate('tds_new_consumo_mensal', NULL, NULL);

-- ============================================================================
-- 7. VALIDAÇÃO DA CONFIGURAÇÃO
-- ============================================================================

-- Verificar hypertable criada
SELECT * FROM timescaledb_information.hypertables 
WHERE hypertable_name = 'tds_new_leitura_dispositivo';

-- Verificar continuous aggregate criada
SELECT * FROM timescaledb_information.continuous_aggregates 
WHERE view_name = 'tds_new_consumo_mensal';

-- Verificar políticas configuradas
SELECT * FROM timescaledb_information.jobs 
WHERE hypertable_name = 'tds_new_leitura_dispositivo' 
   OR hypertable_name = 'tds_new_consumo_mensal';

-- ============================================================================
-- 8. GRANTS DE PERMISSÃO
-- ============================================================================

-- Garantir que o usuário Django tem permissões completas
GRANT ALL PRIVILEGES ON TABLE tds_new_leitura_dispositivo TO tsdb_django_d4j7g9;
GRANT ALL PRIVILEGES ON MATERIALIZED VIEW tds_new_consumo_mensal TO tsdb_django_d4j7g9;

-- ============================================================================
-- CONCLUÍDO!
-- ============================================================================

\echo '✅ TimescaleDB configurado com sucesso!'
\echo ''
\echo 'Hypertable: tds_new_leitura_dispositivo'
\echo 'Continuous Aggregate: tds_new_consumo_mensal'
\echo 'Políticas de refresh: ATIVA (a cada 1 hora)'
\echo ''
\echo 'Próximos passos:'
\echo '1. Verificar hypertable: SELECT * FROM timescaledb_information.hypertables;'
\echo '2. Testar inserção: INSERT INTO tds_new_leitura_dispositivo (...);'
\echo '3. Validar aggregate: SELECT * FROM tds_new_consumo_mensal;'
