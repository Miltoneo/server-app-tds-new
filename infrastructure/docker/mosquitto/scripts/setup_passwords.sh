#!/bin/bash
# ========================================
# Setup Mosquitto Passwords
# TDS New - Generate encrypted password file
# ========================================

set -e

CONTAINER_NAME="tds-new-mosquitto-dev"
PASSWORD_FILE="/mosquitto/config/password.txt"

echo "🔐 Configurando senhas do Mosquitto..."

# Verificar se container está rodando
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Erro: Container $CONTAINER_NAME não está rodando!"
    echo "Execute primeiro: docker compose up -d"
    exit 1
fi

# Criar arquivo de senhas vazio
docker exec "$CONTAINER_NAME" sh -c "rm -f $PASSWORD_FILE && touch $PASSWORD_FILE"

# Adicionar usuários
echo "➕ Adicionando usuário 'admin'..."
docker exec "$CONTAINER_NAME" mosquitto_passwd -b "$PASSWORD_FILE" admin admin

echo "➕ Adicionando usuário 'django_backend'..."
docker exec "$CONTAINER_NAME" mosquitto_passwd -b "$PASSWORD_FILE" django_backend django123

echo "➕ Adicionando usuário 'dashboard'..."
docker exec "$CONTAINER_NAME" mosquitto_passwd -b "$PASSWORD_FILE" dashboard dashboard123

# Recarregar configuração do Mosquitto
echo "🔄 Recarregando configuração..."
docker exec "$CONTAINER_NAME" kill -HUP 1

echo "✅ Senhas configuradas com sucesso!"
echo ""
echo "Usuários criados:"
echo "  - admin:admin (acesso total)"
echo "  - django_backend:django123 (backend telemetria)"
echo "  - dashboard:dashboard123 (somente leitura)"
