-- =====================================================================
-- Script: Adicionar coluna gateway_id à tabela leitura_dispositivo
-- =====================================================================
-- Descrição: Adiciona ForeignKey para Gateway na hypertable
-- Autor: Auto-generated deployment script
-- Data: 2026-02-19
-- =====================================================================

-- 1. Adicionar coluna gateway_id como BIGINT
ALTER TABLE tds_new_leitura_dispositivo ADD COLUMN gateway_id BIGINT;

-- 2. Atualizar registros existentes (se houver)
--    Como não há registros, esse UPDATE não fará nada, mas mantemos para segurança
UPDATE tds_new_leitura_dispositivo 
SET gateway_id = d.gateway_id 
FROM tds_new_dispositivo d 
WHERE tds_new_leitura_dispositivo.dispositivo_id = d.id;

-- 3. Marcar coluna como NOT NULL
ALTER TABLE tds_new_leitura_dispositivo ALTER COLUMN gateway_id SET NOT NULL;

-- 4. Adicionar Foreign Key constraint para gateway
ALTER TABLE tds_new_leitura_dispositivo 
ADD CONSTRAINT fk_leitura_gateway 
FOREIGN KEY (gateway_id) REFERENCES tds_new_gateway(id) ON DELETE CASCADE;

-- 5. Criar índice para performance
CREATE INDEX idx_leitura_gateway_id ON tds_new_leitura_dispositivo(gateway_id);

-- 6. Verificar estrutura final
\d tds_new_leitura_dispositivo
