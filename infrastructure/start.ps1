# ==================================================
# TDS New - Quick Start Script
# Inicializacao rapida da infraestrutura Docker
# ==================================================

Write-Host "TDS New - Infraestrutura Docker" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se Docker esta rodando
Write-Host "[*] Verificando Docker..." -ForegroundColor Yellow
try {
    docker info > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker nao esta rodando"
    }
    Write-Host "[OK] Docker OK" -ForegroundColor Green
} catch {
    Write-Host "[ERRO] Docker nao esta rodando!" -ForegroundColor Red
    Write-Host "Inicie o Docker Desktop e tente novamente." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Navegar para pasta de desenvolvimento
$devPath = "f:/projects/infrastructure/docker/development"
if (-not (Test-Path $devPath)) {
    Write-Host "[ERRO] Pasta nao encontrada: $devPath" -ForegroundColor Red
    exit 1
}

Set-Location $devPath
Write-Host "[*] Pasta: $devPath" -ForegroundColor Cyan

# Verificar se .env existe, senao copiar de .env.example
if (-not (Test-Path ".env")) {
    Write-Host "[*] Criando arquivo .env..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "[OK] Arquivo .env criado" -ForegroundColor Green
} else {
    Write-Host "[OK] Arquivo .env ja existe" -ForegroundColor Green
}

Write-Host ""

# Iniciar stack Docker
Write-Host "[*] Iniciando stack Docker..." -ForegroundColor Yellow
Write-Host "   - PostgreSQL + TimescaleDB (porta 5442)" -ForegroundColor Gray
Write-Host "   - Redis (porta 6379)" -ForegroundColor Gray
Write-Host "   - Mosquitto MQTT (porta 1883)" -ForegroundColor Gray
Write-Host "   - Adminer (porta 8080)" -ForegroundColor Gray
Write-Host ""

docker compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Erro ao iniciar stack Docker!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[*] Aguardando servicos iniciarem (10 segundos)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Verificar status dos containers
Write-Host ""
Write-Host "[*] Status dos containers:" -ForegroundColor Cyan
docker compose ps

Write-Host ""

# Configurar senhas do Mosquitto (se Git Bash estiver disponivel)
if (Get-Command bash -ErrorAction SilentlyContinue) {
    Write-Host "[*] Configurando senhas do Mosquitto..." -ForegroundColor Yellow
    bash ../mosquitto/scripts/setup_passwords.sh
    Write-Host ""
} else {
    Write-Host "[AVISO] Git Bash nao encontrado. Configure senhas manualmente:" -ForegroundColor Yellow
    Write-Host "   docker exec tds-new-mosquitto-dev mosquitto_passwd -b /mosquitto/config/password.txt admin admin" -ForegroundColor Gray
    Write-Host "   docker exec tds-new-mosquitto-dev kill -HUP 1" -ForegroundColor Gray
    Write-Host ""
}

# Resumo final
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "[OK] Infraestrutura iniciada com sucesso!" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Servicos disponiveis:" -ForegroundColor Cyan
Write-Host "   PostgreSQL:  localhost:5442 (user: tsdb_django_d4j7g9, pass: admin)" -ForegroundColor White
Write-Host "   Redis:       localhost:6379" -ForegroundColor White
Write-Host "   Mosquitto:   localhost:1883 (user: admin, pass: admin)" -ForegroundColor White
Write-Host "   Adminer:     http://localhost:8080" -ForegroundColor White
Write-Host ""
Write-Host "Proximos passos:" -ForegroundColor Cyan
Write-Host "   1. Configure o Django (.env.dev com as credenciais acima)" -ForegroundColor Gray
Write-Host "   2. Execute: python manage.py migrate" -ForegroundColor Gray
Write-Host "   3. Execute: python manage.py start_mqtt_consumer --debug" -ForegroundColor Gray
Write-Host ""
Write-Host "Ver logs:        docker compose logs -f" -ForegroundColor Gray
Write-Host "Parar stack:     docker compose down" -ForegroundColor Gray
Write-Host "Limpar volumes:  docker compose down -v" -ForegroundColor Gray
Write-Host ""
