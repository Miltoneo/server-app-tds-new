#!/bin/bash
# ========================================
# PostgreSQL + TimescaleDB Initialization
# TDS New - Auto-setup script
# ========================================

set -e

echo "🚀 Inicializando TimescaleDB..."

# Conectar ao banco de dados
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Criar extensão TimescaleDB
    CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
    
    -- Verificar versão
    SELECT extversion FROM pg_extension WHERE extname = 'timescaledb';
    
    -- Habilitar telemetry (opcional, pode desabilitar com SET timescaledb.telemetry_level=off)
    -- SET timescaledb.telemetry_level=basic;
EOSQL

echo "✅ TimescaleDB inicializado com sucesso!"
echo "📊 Usuário: $POSTGRES_USER"
echo "🗄️  Banco: $POSTGRES_DB"
