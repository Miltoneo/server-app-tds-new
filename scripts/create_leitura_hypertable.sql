-- Criar tabela tds_new_leitura_dispositivo como Hypertable do TimescaleDB
-- Baseado no modelo LeituraDispositivo

-- 1. Criar tabela normal primeiro (SEM PRIMARY KEY tradicional para hypertable)
CREATE TABLE IF NOT EXISTS tds_new_leitura_dispositivo (
    id BIGSERIAL,
    time TIMESTAMPTZ NOT NULL,
    valor NUMERIC(15, 4) NOT NULL,
    unidade VARCHAR(10) NOT NULL,
    payload_raw JSONB,
    dispositivo_id BIGINT NOT NULL,
    PRIMARY KEY (id, time)  -- Chave primária composta para hypertable
);

-- Adicionar FK manualmente (após criar table)
ALTER TABLE tds_new_leitura_dispositivo 
    ADD CONSTRAINT fk_leitura_dispositivo 
    FOREIGN KEY (dispositivo_id) 
    REFERENCES tds_new_dispositivo(id) 
    ON DELETE CASCADE;

-- 2. Criar índice no campo time (necessário para hypertable)
CREATE INDEX IF NOT EXISTS idx_leitura_dispositivo_time ON tds_new_leitura_dispositivo(time DESC);

-- 3. Converter em hypertable do Timescale (particionada por time)
SELECT create_hypertable('tds_new_leitura_dispositivo', 'time', 
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- 4. Criar índice composto para consultas por dispositivo
CREATE INDEX IF NOT EXISTS idx_leitura_dispositivo_id_time 
    ON tds_new_leitura_dispositivo(dispositivo_id, time DESC);

-- 5. Criar índice composto para consultas por dispositivo
CREATE INDEX IF NOT EXISTS idx_leitura_dispositivo_id_time 
    ON tds_new_leitura_dispositivo(dispositivo_id, time DESC);

-- 6. Habilitar compressão automática (chunks mais antigos que 7 dias)
ALTER TABLE tds_new_leitura_dispositivo SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC',
    timescaledb.compress_segmentby = 'dispositivo_id'
);

SELECT add_compression_policy('tds_new_leitura_dispositivo', INTERVAL '7 days');

-- 7. Criar política de retenção (manter 365 dias)
SELECT add_retention_policy('tds_new_leitura_dispositivo', INTERVAL '365 days');

-- Verificação
SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = 'tds_new_leitura_dispositivo';
