-- Adicionar coluna conta_id para isolamento multi-tenant
ALTER TABLE tds_new_leitura_dispositivo 
    ADD COLUMN conta_id BIGINT;

-- Atualizar registros existentes (se houver) pegando conta_id do dispositivo
UPDATE tds_new_leitura_dispositivo 
SET conta_id = d.conta_id 
FROM tds_new_dispositivo d 
WHERE tds_new_leitura_dispositivo.dispositivo_id = d.id;

-- Tornar NOT NULL após preencher
ALTER TABLE tds_new_leitura_dispositivo 
    ALTER COLUMN conta_id SET NOT NULL;

-- Adicionar FK para conta
ALTER TABLE tds_new_leitura_dispositivo 
    ADD CONSTRAINT fk_leitura_conta 
    FOREIGN KEY (conta_id) 
    REFERENCES conta(id) 
    ON DELETE CASCADE;

-- Criar índice para performance em filtros multi-tenant
CREATE INDEX idx_leitura_conta_id ON tds_new_leitura_dispositivo(conta_id);

-- Verificar estrutura
\d tds_new_leitura_dispositivo
