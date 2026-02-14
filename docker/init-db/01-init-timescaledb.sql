-- =============================================================================
-- Script de Inicialização do TimescaleDB
-- =============================================================================
-- Executado automaticamente na primeira vez que o container sobe
-- =============================================================================

-- Criar extensão TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Verificar versão instalada
SELECT extversion FROM pg_extension WHERE extname = 'timescaledb';

-- Log de sucesso
DO $$
BEGIN
    RAISE NOTICE 'TimescaleDB inicializado com sucesso!';
    RAISE NOTICE 'Database: %', current_database();
    RAISE NOTICE 'User: %', current_user;
END $$;
