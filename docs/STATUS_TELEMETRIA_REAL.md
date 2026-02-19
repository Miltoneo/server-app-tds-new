# STATUS DO SISTEMA - Telemetria Real e Atualização de Firmware

**Data de Análise:** 18/02/2026  
**Objetivo:** Avaliar prontidão para iniciar telemetria real e OTA firmware updates

---

## 🔍 RESUMO EXECUTIVO

### ✅ PRONTO PARA TELEMETRIA REAL
- **Backend Django:** ✅ Operacional (http://127.0.0.1:8000)
- **Dashboard Web:** ✅ Funcional com Chart.js e AJAX polling
- **TimescaleDB:** ✅ Healthy (porta 5442)
- **Redis:** ✅ Operacional (porta 6379)
- **Infraestrutura MQTT:** ⚠️ Mosquitto UP mas UNHEALTHY

### ⚠️ PENDÊNCIAS CRÍTICAS
- **MQTT Consumer:** ❌ NÃO ESTÁ RODANDO (precisa reiniciar)
- **Código MQTT no Firmware:** ❌ NÃO IMPLEMENTADO
- **Configuração de Conexão:** ❌ FALTA configurar broker/topics no firmware
- **Certificados mTLS:** ⏸️ Opcional para MVP (disponíveis em server-iot)

### ✅ PRONTO PARA OTA UPDATES
- **Servidor OTA:** ✅ Código Python disponível (`server-iot/infrastructure/ota/secure_server.py`)
- **Firmwares Compilados:** ✅ Binários existentes (`firmware.bin`, `hello.bin`)
- **Certificados TLS:** ✅ Prontos em `server_certs/`
- **Código OTA no Firmware:** ⚠️ PRECISA VERIFICAR se está implementado

---

## 📊 STATUS DETALHADO DOS COMPONENTES

### 1. Infraestrutura Backend (Django + DB)

#### Django Web Server ✅
```
Status: Running
URL: http://127.0.0.1:8000
Processo: Terminal 5c60b014-2c3f-4973-9d9d-d82a6cfe77dc
Último Reload: 14:43:44 (auto-reload ativo)
Requests Recentes:
  - GET /tds_new/telemetria/ → 200 OK
  - GET /tds_new/telemetria/api/timeline/ → 200 OK
  - GET /tds_new/telemetria/api/barras/ → 200 OK
```

**Funcionalidades Ativas:**
- ✅ Dashboard telemetria em tempo real
- ✅ AJAX polling (30s)
- ✅ Filtros de período (24h/7d/30d)
- ✅ Múltiplos dispositivos
- ✅ Agregação horária (TruncHour)

#### PostgreSQL + TimescaleDB ✅
```
Container: tsdb_c
Status: Up 8 hours (healthy)
Porta: 5442 → 5432
Health: ✅ HEALTHY
```

**Recursos Configurados:**
- ✅ Hypertable: `tds_new_leituradispositivo`
- ✅ Compression Policy (dados > 7 dias)
- ✅ Retention Policy (90 dias)
- ✅ Continuous Aggregate (métricas horárias)
- ✅ Indexes otimizados para queries multi-tenant

#### Redis ✅
```
Container: redis_c
Status: Up 8 hours
Porta: 6379 → 6379
Uso: Cache de sessões Django
```

---

### 2. Infraestrutura MQTT

#### Mosquitto Broker ⚠️
```
Container: tds-new-mosquitto-dev (d83156347988)
Status: Up 6 hours (UNHEALTHY) ⚠️
Portas:
  - 1883 → 1883 (MQTT)
  - 9001 → 9001 (WebSocket)
```

**ATENÇÃO:** Container está UP mas **UNHEALTHY**!

**Ações Necessárias:**
1. Verificar logs: `docker logs tds-new-mosquitto-dev`
2. Possível causa: health check failure
3. Solução: Reiniciar container ou verificar configuração

**Configuração Atual (esperada):**
```conf
# mosquitto.conf
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest stdout
log_type all
```

#### MQTT Consumer ❌
```
Status: NÃO ESTÁ RODANDO
Terminal: bbf2c522-a46d-4826-96a9-4d0f61939eb0 (vazio)
```

**CRÍTICO:** Consumer precisa ser reiniciado para processar telemetria real!

**Como Reiniciar:**
```bash
python manage.py mqtt_consumer
```

**Validação (quando ativo):**
- ✅ Conecta em `localhost:1883`
- ✅ Subscreve em `telemetry/+/+/data`
- ✅ Processa JSON com validação
- ✅ Persiste em TimescaleDB via Django ORM
- ✅ Logs detalhados em console

**Topics Esperados:**
```
telemetry/<gateway_code>/<device_code>/data

Exemplo:
telemetry/GW-TEST-001/D01/data
```

**Payload JSON Esperado:**
```json
{
  "gateway_code": "GW-TEST-001",
  "device_code": "D01",
  "timestamp": "2026-02-18T15:30:00-03:00",
  "leituras": [
    {
      "tipo": "energia",
      "valor": 123.45,
      "unidade": "kWh"
    }
  ]
}
```

---

### 3. Firmware (Devices IoT)

#### Projeto Firmware ✅
```
Localização: f:\projects\firmware
Estrutura:
  - common/         (bibliotecas compartilhadas)
  - devices/        (firmwares específicos)
  - docs/           (documentação)
  - factory/        (dados de fábrica)
  - tools/          (scripts utilitários)
```

#### Dispositivos Disponíveis
```
1. dcu-0080/       - Controlador base
2. dcu-8000-sim/   - IoT com SIM7080G (NB-IoT/Cat-M/GPRS)
3. dcu-all/        - Firmware unificado
4. relay-mfr/      - Relé multifuncional
```

#### DCU-8000-SIM (Exemplo Analisado) ⚠️
**Hardware:**
- MCU: ESP32 WROOM-32
- Módulo: SIM7080G (NB-IoT/Cat-M/GPRS + GPS)
- RS-485: GPIO 16/17/18
- LEDs: GPIO 2 (RUN), 19 (FAULT)

**Framework:** ESP-IDF (não Arduino)

**PROBLEMA IDENTIFICADO:**
- ❌ **Código MQTT NÃO encontrado** nos arquivos `.c/.cpp/.h`
- ❌ Falta implementar cliente MQTT
- ❌ Falta configurar broker/topics
- ❌ Falta integração com protocolo de telemetria

**PENDÊNCIAS FIRMWARE:**
1. Implementar cliente MQTT (usar `esp-mqtt` do ESP-IDF)
2. Configurar broker: `localhost:1883` ou IP do servidor
3. Configurar topics: `telemetry/<gateway_code>/<device_code>/data`
4. Implementar serialização JSON do payload
5. Adicionar retry logic para conexão
6. Implementar certificados (se usar mTLS)

---

### 4. OTA (Over-The-Air Updates)

#### Servidor OTA ✅
```
Localização: server-iot/infrastructure/ota/
Script: secure_server.py (Python HTTPS server)
Certificados: server_certs/ (prontos)
```

**Arquivos Disponíveis:**
```
ota/
├── dcu/
│   ├── firmware.bin      ✅ Firmware compilado
│   └── hello.bin         ✅ Firmware de teste
├── server_certs/         ✅ Certificados TLS
├── secure_server.py      ✅ Servidor HTTPS
└── env.bat               ✅ Script de ambiente
```

**Como Iniciar Servidor OTA:**
```bash
cd f:\projects\server-iot\infrastructure\ota
python secure_server.py
```

**Configuração Esperada:**
- Porta: 8070 (HTTPS)
- Endpoint: `/ota/dcu/firmware.bin`
- Autenticação: Certificado TLS (opcional para teste)

#### Código OTA no Firmware ⚠️
**STATUS:** Precisa verificar se ESP32 tem rotina OTA implementada

**Implementação Típica (ESP-IDF):**
```c
#include "esp_https_ota.h"
#include "esp_ota_ops.h"

void perform_ota_update(const char* url) {
    esp_http_client_config_t config = {
        .url = url,
        .cert_pem = server_cert_pem_start,  // Certificado
        .timeout_ms = 30000,
    };
    
    esp_err_t ret = esp_https_ota(&config);
    if (ret == ESP_OK) {
        esp_restart();  // Reinicia com novo firmware
    }
}
```

**OTA Trigger Options:**
1. **Push via MQTT:** Broker envia comando `ota/update` com URL
2. **Pull Periódico:** Firmware consulta servidor a cada X horas
3. **Manual:** Usuário aciona via dashboard web

---

## 🚀 ROADMAP PARA TELEMETRIA REAL

### FASE 1: Corrigir Infraestrutura MQTT (URGENTE)

#### Passo 1.1: Diagnosticar Mosquitto Unhealthy
```bash
# Ver logs
docker logs tds-new-mosquitto-dev --tail 50

# Se necessário, reiniciar
docker restart tds-new-mosquitto-dev

# Verificar health
docker ps --filter "name=mosquitto"
```

**Resultado Esperado:** Container HEALTHY

#### Passo 1.2: Reiniciar MQTT Consumer
```bash
cd F:\projects\server-app\server-app-tds-new
python manage.py mqtt_consumer
```

**Validação:**
```
[INFO] Conectado ao MQTT broker em localhost:1883
[INFO] Subscrito em: telemetry/+/+/data
```

**Manter Rodando:** Deixar em terminal background

---

### FASE 2: Implementar MQTT no Firmware

#### Passo 2.1: Adicionar Dependência esp-mqtt
**Arquivo:** `devices/dcu-8000-sim/idf_component.yml`
```yaml
dependencies:
  espressif/esp_mqtt: "^2.0.0"
```

#### Passo 2.2: Criar Módulo MQTT Client
**Arquivo:** `devices/dcu-8000-sim/main/mqtt_client.c`
```c
#include "mqtt_client.h"
#include <string.h>
#include "esp_log.h"
#include "cJSON.h"

#define MQTT_BROKER_URI "mqtt://192.168.1.100:1883"  // IP do servidor
#define MQTT_TOPIC_TELEMETRY "telemetry/%s/%s/data"
#define MQTT_TOPIC_OTA "ota/%s/update"

static const char *TAG = "MQTT";
static esp_mqtt_client_handle_t client;

// Callback de eventos MQTT
static void mqtt_event_handler(void *handler_args, esp_event_base_t base, 
                               int32_t event_id, void *event_data) {
    esp_mqtt_event_handle_t event = event_data;
    
    switch (event->event_id) {
        case MQTT_EVENT_CONNECTED:
            ESP_LOGI(TAG, "MQTT Connected");
            // Subscrever em topic de OTA
            char ota_topic[64];
            snprintf(ota_topic, sizeof(ota_topic), MQTT_TOPIC_OTA, "GW-001");
            esp_mqtt_client_subscribe(client, ota_topic, 1);
            break;
            
        case MQTT_EVENT_DATA:
            ESP_LOGI(TAG, "MQTT Data: %.*s", event->data_len, event->data);
            // Processar comando OTA
            if (strstr(event->topic, "ota/") != NULL) {
                handle_ota_command(event->data, event->data_len);
            }
            break;
            
        default:
            break;
    }
}

// Inicializar cliente MQTT
void mqtt_client_init(void) {
    esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = MQTT_BROKER_URI,
        .session.keepalive = 60,
    };
    
    client = esp_mqtt_client_init(&mqtt_cfg);
    esp_mqtt_client_register_event(client, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(client);
}

// Publicar telemetria
void mqtt_publish_telemetry(const char* gateway_code, const char* device_code,
                            const char* tipo, float valor, const char* unidade) {
    // Criar JSON
    cJSON *root = cJSON_CreateObject();
    cJSON_AddStringToObject(root, "gateway_code", gateway_code);
    cJSON_AddStringToObject(root, "device_code", device_code);
    cJSON_AddStringToObject(root, "timestamp", get_iso_timestamp());
    
    cJSON *leituras = cJSON_CreateArray();
    cJSON *leitura = cJSON_CreateObject();
    cJSON_AddStringToObject(leitura, "tipo", tipo);
    cJSON_AddNumberToObject(leitura, "valor", valor);
    cJSON_AddStringToObject(leitura, "unidade", unidade);
    cJSON_AddItemToArray(leituras, leitura);
    cJSON_AddItemToObject(root, "leituras", leituras);
    
    char *json_str = cJSON_Print(root);
    
    // Publicar
    char topic[128];
    snprintf(topic, sizeof(topic), MQTT_TOPIC_TELEMETRY, gateway_code, device_code);
    esp_mqtt_client_publish(client, topic, json_str, 0, 1, 0);
    
    ESP_LOGI(TAG, "Published: %s", json_str);
    
    cJSON_Delete(root);
    free(json_str);
}
```

#### Passo 2.3: Integrar no Loop Principal
**Arquivo:** `devices/dcu-8000-sim/main/main.c`
```c
#include "mqtt_client.h"

void app_main(void) {
    // Inicializar WiFi ou SIM7080G
    init_connectivity();
    
    // Inicializar MQTT
    mqtt_client_init();
    
    // Loop de telemetria
    while (1) {
        // Ler sensor (exemplo)
        float temperatura = read_temperature_sensor();
        
        // Publicar via MQTT
        mqtt_publish_telemetry("GW-001", "D01", "temperatura", temperatura, "°C");
        
        vTaskDelay(pdMS_TO_TICKS(60000));  // A cada 1 minuto
    }
}
```

#### Passo 2.4: Configuração de Rede

**WiFi (se DCU-0080):**
```c
#define WIFI_SSID "SuaRedeWiFi"
#define WIFI_PASS "SuaSenha"
```

**SIM7080G (se DCU-8000-SIM):**
```c
// Configurar APN da operadora
#define APN_NAME "claro.com.br"
#define APN_USER ""
#define APN_PASS ""
```

---

### FASE 3: Compilar e Flashar Firmware

#### Passo 3.1: Compilar
```bash
cd f:\projects\firmware\devices\dcu-8000-sim
pio run
```

**Output Esperado:**
```
Linking .pio\build\dcu-8000-sim\firmware.elf
Building .pio\build\dcu-8000-sim\firmware.bin
RAM:   [=         ]  12.3% (used 40256 bytes from 327680 bytes)
Flash: [====      ]  42.1% (used 551440 bytes from 1310720 bytes)
```

#### Passo 3.2: Copiar Firmware para OTA Server
```bash
copy .pio\build\dcu-8000-sim\firmware.bin f:\projects\server-iot\infrastructure\ota\dcu\firmware.bin
```

#### Passo 3.3: Flash Inicial (USB)
```bash
pio run -t upload
```

**Porta:** Ver em Device Manager (ex: COM3)

---

### FASE 4: Testar Telemetria Real

#### Passo 4.1: Iniciar Servidor OTA (opcional)
```bash
cd f:\projects\server-iot\infrastructure\ota
python secure_server.py
```

#### Passo 4.2: Verificar Consumer Rodando
```bash
# Em outro terminal
python manage.py mqtt_consumer

# Deve mostrar:
# [INFO] Conectado ao MQTT broker em localhost:1883
# [INFO] Subscrito em: telemetry/+/+/data
```

#### Passo 4.3: Ligar Dispositivo Físico
- Conectar ESP32 via USB ou alimentação externa
- Device deve:
  1. Conectar na rede (WiFi ou Celular)
  2. Conectar no MQTT broker (192.168.1.100:1883)
  3. Publicar telemetria a cada 1 minuto

#### Passo 4.4: Monitorar Logs
**No Consumer:**
```
[INFO] Mensagem recebida em telemetry/GW-001/D01/data
[INFO] Payload: {"gateway_code":"GW-001","device_code":"D01",...}
[INFO] Leitura salva: temperatura=23.5°C
```

**No Django:**
```
"POST /tds_new/telemetria/api/leituras/" 200 OK
```

#### Passo 4.5: Verificar Dashboard
- Abrir: http://localhost:8000/tds_new/telemetria/
- Aguardar AJAX polling (30s)
- **Esperado:** Gráfico atualiza com dados reais!

---

## 📋 CHECKLIST COMPLETO

### Infraestrutura Backend
- [x] Django Server rodando
- [x] TimescaleDB healthy
- [x] Redis operacional
- [ ] Mosquitto HEALTHY (atualmente unhealthy)
- [ ] MQTT Consumer rodando (atualmente parado)

### Dashboard Web
- [x] Template renderizando
- [x] Chart.js funcionando
- [x] AJAX polling configurado
- [x] Filtros operacionais
- [x] Multi-tenant enforcement

### Firmware
- [ ] Código MQTT implementado
- [ ] Certificados configurados (opcional)
- [ ] Topics configurados
- [ ] Payload JSON correto
- [ ] WiFi/SIM configurado
- [ ] Compilado e testado
- [ ] Flashado em device físico

### OTA Update
- [x] Servidor Python pronto
- [x] Certificados disponíveis
- [x] Firmwares compilados
- [ ] Código OTA no firmware (verificar)
- [ ] Trigger de update (MQTT ou polling)
- [ ] Teste de update bem-sucedido

### Testes End-to-End
- [ ] Device publica em MQTT
- [ ] Consumer recebe e persiste
- [ ] Dashboard exibe dados reais
- [ ] OTA update funciona
- [ ] Rollback em caso de falha

---

## ⚠️ RISCOS E MITIGAÇÕES

### Risco 1: Mosquitto Unhealthy
**Impacto:** Consumer não consegue conectar  
**Probabilidade:** Baixa (só configuração)  
**Mitigação:** Verificar logs e reiniciar container

### Risco 2: Firmware MQTT Não Implementado
**Impacto:** Não há telemetria real  
**Probabilidade:** Alta (código não encontrado)  
**Mitigação:** Implementar conforme FASE 2 (~4h trabalho)

### Risco 3: Conectividade de Rede
**Impacto:** Device não alcança broker  
**Probabilidade:** Média  
**Mitigação:**
- Testar WiFi/SIM antes de flash
- Usar IP fixo do servidor
- Implementar retry logic no código

### Risco 4: Payload JSON Inválido
**Impacto:** Consumer rejeita mensagem  
**Probabilidade:** Média  
**Mitigação:**
- Validar JSON no firmware antes de publicar
- Logs detalhados no consumer para debug

### Risco 5: OTA Brick (Device Inutilizado)
**Impacto:** Device precisa reflash via USB  
**Probabilidade:** Baixa (ESP-IDF tem proteção)  
**Mitigação:**
- Usar partição de rollback do ESP32
- Testar firmware antes de OTA massivo
- Manter cabo USB conectado durante testes

---

## 🎯 PRÓXIMOS PASSOS RECOMENDADOS

### IMEDIATO (hoje)
1. ✅ Diagnosticar Mosquitto unhealthy
2. ✅ Reiniciar MQTT Consumer
3. ✅ Validar infraestrutura com dados de teste

### CURTO PRAZO (2-3 dias)
4. ⚙️ Implementar código MQTT no firmware
5. ⚙️ Compilar e flash em device de teste
6. ⚙️ Testar telemetria real end-to-end

### MÉDIO PRAZO (1 semana)
7. 🔒 Implementar certificados mTLS (segurança)
8. 📡 Implementar OTA trigger via MQTT
9. 🧪 Testes de stress (múltiplos devices)

### LONGO PRAZO (2+ semanas)
10. 🚀 Deploy em produção
11. 📊 Monitoramento com alertas
12. 🔧 Ajustes de performance

---

**Autor:** GitHub Copilot (Claude Sonnet 4.5)  
**Data:** 18/02/2026 15:30  
**Versão:** 1.0
