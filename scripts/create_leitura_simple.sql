-- Drop se existe
DROP TABLE IF EXISTS tds_new_leitura_dispositivo CASCADE;

-- Criar tabela simples
CREATE TABLE tds_new_leitura_dispositivo (
    id BIGSERIAL,
    time TIMESTAMPTZ NOT NULL,
    valor NUMERIC(15, 4) NOT NULL,
    unidade TEXT NOT NULL,
    payload_raw JSONB,
    dispositivo_id BIGINT NOT NULL
);

-- Converter em hypertable ANTES de adicionar constraints
SELECT create_hypertable('tds_new_leitura_dispositivo', 'time',
    chunk_time_interval => INTERVAL '7 days'
);

-- Adicionar FK após criar hypertable
ALTER TABLE tds_new_leitura_dispositivo 
    ADD CONSTRAINT fk_leitura_dispositivo 
    FOREIGN KEY (dispositivo_id) 
    REFERENCES tds_new_dispositivo(id) 
    ON DELETE CASCADE;

-- Índices para performance
CREATE INDEX idx_leitura_disp_time ON tds_new_leitura_dispositivo(time DESC);
CREATE INDEX idx_leitura_disp_id_time ON tds_new_leitura_dispositivo(dispositivo_id, time DESC);

-- Verificar
SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = 'tds_new_leitura_dispositivo';
