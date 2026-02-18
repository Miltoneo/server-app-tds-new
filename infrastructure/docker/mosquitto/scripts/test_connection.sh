#!/bin/bash
# ========================================
# Test MQTT Broker Connection
# TDS New - Verify Mosquitto is working
# ========================================

set -e

CONTAINER_NAME="tds-new-mosquitto-dev"
BROKER="localhost"
PORT="1883"
USERNAME="admin"
PASSWORD="admin"

echo "🧪 Testando conexão MQTT..."
echo "Broker: $BROKER:$PORT"
echo "Usuário: $USERNAME"
echo ""

# Teste 1: System topics
echo "📊 Teste 1: Lendo topics do sistema..."
timeout 5 docker exec "$CONTAINER_NAME" mosquitto_sub -h localhost -p 1883 -t '$SYS/#' -C 5 -u "$USERNAME" -P "$PASSWORD" || true
echo ""

# Teste 2: Publish e Subscribe
echo "📤 Teste 2: Publish/Subscribe..."
echo "Iniciando subscriber em background..."
timeout 10 docker exec "$CONTAINER_NAME" sh -c "mosquitto_sub -h localhost -p 1883 -t 'test/telemetry' -u '$USERNAME' -P '$PASSWORD' &
sleep 2
mosquitto_pub -h localhost -p 1883 -t 'test/telemetry' -m '{\"device\":\"TEST-001\",\"value\":123.45}' -u '$USERNAME' -P '$PASSWORD'
sleep 1
" || true
echo ""

# Teste 3: ACL - tentar escrever em topic protegido
echo "🔒 Teste 3: Verificando ACL (deve falhar)..."
docker exec "$CONTAINER_NAME" mosquitto_pub -h localhost -p 1883 -t 'admin/commands' -m 'test' -u dashboard -P dashboard123 2>&1 | grep -i "denied\|error" && echo "✅ ACL funcionando corretamente!" || echo "⚠️ ACL pode não estar funcionando"
echo ""

echo "✅ Testes concluídos!"
