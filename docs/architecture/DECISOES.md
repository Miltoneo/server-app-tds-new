# 🏛️ Architectural Decision Records (ADR)

**Projeto:** TDS New - Sistema de Telemetria e Monitoramento IoT  
**Repositório:** [Miltoneo/server-app-tds-new](https://github.com/Miltoneo/server-app-tds-new)  
**Última Atualização:** 18/02/2026

---

## 📋 ÍNDICE DE DECISÕES

| ADR | Data | Status | Título |
|-----|------|--------|--------|
| [ADR-001](#adr-001-mqtt-consumer-strategy) | 14/02/2026 | ✅ Aprovado | MQTT Consumer Strategy |
| [ADR-002](#adr-002-certificate-management-strategy) | 14/02/2026 | ✅ Aprovado | Certificate Management Strategy |
| [ADR-003](#adr-003-topic-mqtt-sem-conta_id) | 17/02/2026 | ✅ Aprovado | Topic MQTT sem conta_id |
| [ADR-004](#adr-004-ota-certificate-renewal-protocol) | 14/02/2026 | ✅ Aprovado | OTA Certificate Renewal Protocol |
| [ADR-005](#adr-005-mqtt-consumer-location) | 18/02/2026 | ✅ Aprovado | MQTT Consumer Location - Backend vs Infrastructure |

---

## ADR-001: MQTT Consumer Strategy

**Data:** 14/02/2026  
**Status:** ✅ **APROVADO**  
**Decisor:** Equipe TDS New  
**Contexto:** Week 8-9 do ROADMAP

### Contexto

Escolha de tecnologia para consumir mensagens MQTT e gravar telemetria no Django:

**Opções avaliadas:**
- **Opção A:** Telegraf (Go/C) → Grava diretamente em SQL (tabela `telegraf_ana`)
- **Opção B:** Django Consumer (Python) → Usa ORM Django para gravar em `LeituraDispositivo`

**Requisitos críticos:**
1. Multi-tenant: Isolamento por `conta_id`
2. Lógica de negócio: Validações, alarmes, atualização de `Gateway.is_online`
3. Auditoria: Logs rastreáveis de todas as leituras
4. Performance: Processar 100+ mensagens/segundo

### Decisão

**Django Consumer (Celery + Paho-MQTT)**

**Implementação:**
```python
# tds_new/consumers/mqtt_telemetry.py
import paho.mqtt.client as mqtt
from tds_new.models import Gateway, LeituraDispositivo
from tds_new.services.telemetry import TelemetryProcessorService

def on_message(client, userdata, msg):
    # Extrair MAC do topic: tds_new/devices/{mac}/telemetry
    mac_address = msg.topic.split('/')[2]
    
    # Resolver conta_id via Gateway
    gateway = Gateway.objects.get(mac=mac_address)
    
    # Processar com serviço de negócio
    service = TelemetryProcessorService(conta_id=gateway.conta_id)
    service.processar_telemetria(gateway, json.loads(msg.payload))
```

### Consequências

#### ✅ Positivas
- Acesso completo ao ORM Django (queries, validações, signals)
- Isolamento multi-tenant nativo via `conta_id`
- Validações de modelo automáticas
- Integração com sistema de auditoria Django
- Fácil testar (unit tests Django)
- Logs centralizados em `django_logs/`

#### ⚠️ Negativas
- Requer Celery worker dedicado (recurso adicional ~256MB RAM)
- Performance ~20% inferior ao Telegraf (aceitável para escala atual)
- Mais código Python para manter

### Alternativas Rejeitadas

**Telegraf (Opção A):**
- ✅ Alta performance (escrito em Go)
- ✅ Já configurado na infraestrutura
- ❌ Grava em tabela externa ao Django (`telegraf_ana`)
- ❌ Não executa validações de negócio
- ❌ Não atualiza `Gateway.is_online` ou `last_seen`
- ❌ Dificulta auditoria (logs separados)
- ❌ Requer SQL views complexas para integrar com Django

### Implementação

**Código:**
- `tds_new/consumers/mqtt_telemetry.py` (Consumer MQTT)
- `tds_new/services/telemetry.py` (TelemetryProcessorService)

**Documentação:**
- [PROVISIONAMENTO_IOT.md - Seção 10](../PROVISIONAMENTO_IOT.md#arquitetura-de-ingestão-de-telemetria)
- [ROADMAP.md - Week 8-9](../ROADMAP.md#week-8-9-mqtt-consumer--telemetria-tempo-real)

**Testes:**
- `tds_new/tests/test_mqtt_consumer.py` (unit tests)
- `tds_new/tests/integration/test_telemetry_flow.py` (integration tests)

---

## ADR-002: Certificate Management Strategy

**Data:** 14/02/2026  
**Status:** ✅ **APROVADO**  
**Decisor:** Equipe TDS New  
**Contexto:** Week 6-7 (Modelos) e Week 12 (OTA Renewal)

### Contexto

Estratégia de validade de certificados X.509 para dispositivos IoT em campo:

**Opções avaliadas:**
- **Opção A:** Bootstrap (24h) + Operational (90 dias) - Renovação frequente
- **Opção B:** Operational (10 anos) - Renovação rara

**Cenário real:**
- 1.000+ dispositivos em campo
- Alguns dispositivos podem ficar offline por meses (ex: medidores sazonais)
- Comunicação 4G/WiFi pode falhar temporariamente
- Intervenção manual é cara (técnico de campo)

### Decisão

**Certificados Operational de 10 anos (não bootstrap curto)**

**Implementação:**
```python
# tds_new/services/certificados.py
class CertificadoService:
    def gerar_certificado(self, mac_address: str, conta_id: int, validade_anos: int = 10):
        # Gerar certificado X.509 com validade de 10 anos
        not_valid_after = datetime.utcnow() + timedelta(days=365 * validade_anos)
        
        cert = (
            x509.CertificateBuilder()
            .subject_name(x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, mac_address)
            ]))
            .not_valid_after(not_valid_after)
            .sign(self.ca_key, hashes.SHA256())
        )
```

### Consequências

#### ✅ Positivas
- Dispositivo offline por **meses/anos** pode reconectar sem intervenção
- Zero intervenção manual para renovação
- Reduz drasticamente custos operacionais (visitas técnicas)
- Dispositivo funciona "out of the box" por 10 anos

#### ⚠️ Negativas
- Certificado comprometido é válido por até 10 anos (mitigado por CRL)
- Requer sistema robusto de revogação (CRL publicada no broker MQTT)

#### 🔧 Mitigações
- **CRL (Certificate Revocation List):** Broker Mosquitto verifica CRL antes de aceitar conexão
- **OTA Renewal:** Renovação automática com 2 anos de antecedência (Week 12)
- **Auditoria:** Logs de conexão com MAC address e serial do certificado

### Alternativas Rejeitadas

**Opção A: Bootstrap (24h) + Operational (90 dias):**
- ✅ Certificado comprometido expira rápido
- ❌ Dispositivo offline por >90 dias para de funcionar
- ❌ Requer renovação frequente (overhead de rede)
- ❌ Risco de expiração em massa (falha de rede)

### Implementação

**Modelo Django:**
```python
# tds_new/models/certificados.py
class CertificadoDevice(SaaSBaseModel):
    mac_address = CharField(17)
    certificate_pem = TextField()
    private_key_pem = TextField()  # NUNCA expor via API
    serial_number = CharField(50, unique=True)
    expires_at = DateTimeField()  # 10 anos
    is_revoked = BooleanField(default=False)
```

**Documentação:**
- [PROVISIONAMENTO_IOT.md - Seção 5](../PROVISIONAMENTO_IOT.md#fluxo-de-certificação-mtls)
- [ROADMAP.md - Week 6-7](../ROADMAP.md#week-6-7-gateways--dispositivos-iot)

**Testes:**
- `tds_new/tests/test_certificados.py` (unit tests)

---

## ADR-003: Topic MQTT sem conta_id

**Data:** 17/02/2026  
**Status:** ✅ **APROVADO**  
**Decisor:** Equipe TDS New  
**Contexto:** Revisão de segurança do fluxo de telemetria

### Contexto

Definição do padrão de topics MQTT para telemetria de dispositivos:

**Opções avaliadas:**
- **Opção A:** `tds_new/conta_{id}/devices/{mac}/telemetry` - Dispositivo conhece `conta_id`
- **Opção B:** `tds_new/devices/{mac}/telemetry` - Dispositivo **NÃO** conhece `conta_id`

**Problemas da Opção A:**
1. **Violação de segurança:** Dispositivo poderia "spoofar" `conta_id` e enviar dados para outras contas
2. **Acoplamento desnecessário:** Firmware precisaria ser recompilado ao mudar de conta
3. **Complexidade de provisionamento:** API precisaria enviar `conta_id` junto com certificados

### Decisão

**Topic baseado APENAS em MAC address: `tds_new/devices/{mac}/telemetry`**

**Fluxo completo:**
```
1. Firmware publica em: tds_new/devices/aa:bb:cc:dd:ee:ff/telemetry
   Payload: {timestamp, valor, unidade}
   ❌ NÃO conhece conta_id

2. Mosquitto valida mTLS:
   - Extrai CN (Common Name) = aa:bb:cc:dd:ee:ff
   - ACL: pattern write tds_new/devices/%u/telemetry
   - ✅ Autoriza apenas se CN == MAC no topic

3. Backend Consumer MQTT:
   - Recebe payload de aa:bb:cc:dd:ee:ff
   - Busca Gateway no banco: Gateway.objects.get(mac='aa:bb:cc:dd:ee:ff')
   - Descobre conta_id = gateway.conta_id
   - Grava em LeituraDispositivo(conta_id=conta_id, ...)
```

### Consequências

#### ✅ Positivas
- **Segurança:** Dispositivo só pode publicar no próprio topic (validado por CN do certificado)
- **Isolamento:** Backend resolve `conta_id` via lookup, dispositivo não precisa saber
- **Simplicidade:** Firmware genérico (mesmo código para todas as contas)
- **ACL granular:** Mosquitto valida topic vs CN automaticamente

#### ⚠️ Negativas
- Requer lookup adicional no banco (cache com Redis minimiza impacto)

### Alternativas Rejeitadas

**Opção A: Topic com conta_id:**
```
tds_new/conta_123/devices/aa:bb:cc:dd:ee:ff/telemetry
         ^^^^^^^^ Dispositivo precisa conhecer conta_id
```
- ❌ Violação de segurança (spoofing)
- ❌ Firmware acoplado à conta
- ❌ Complexidade de provisionamento

### Implementação

**ACL Mosquitto:**
```conf
# /etc/mosquitto/acl.conf
# %u = Common Name do certificado (MAC address)
pattern write tds_new/devices/%u/telemetry
pattern write tds_new/devices/%u/status
```

**Firmware ESP32:**
```cpp
// ✅ CORRETO - Firmware NÃO conhece conta_id
String mac = getMacAddress();  // aa:bb:cc:dd:ee:ff
String topic = "tds_new/devices/" + mac + "/telemetry";
mqttClient.publish(topic.c_str(), payload.c_str());
```

**Backend Consumer:**
```python
# Extrair MAC do topic
mac_address = msg.topic.split('/')[2]  # aa:bb:cc:dd:ee:ff

# Resolver conta_id via Gateway
gateway = Gateway.objects.get(mac=mac_address)
conta_id = gateway.conta_id  # ← Descobre aqui
```

**Documentação:**
- [PROVISIONAMENTO_IOT.md - Seção 10](../PROVISIONAMENTO_IOT.md#arquitetura-de-ingestão-de-telemetria)
- [ROADMAP.md - Week 8-9](../ROADMAP.md#week-8-9-mqtt-consumer--telemetria-tempo-real)

**Testes:**
- Teste de ACL: dispositivo não pode publicar em topic de outro MAC
- Teste de lookup: consumer resolve conta_id corretamente

---

## ADR-004: OTA Certificate Renewal Protocol

**Data:** 14/02/2026  
**Status:** ✅ **APROVADO**  
**Decisor:** Equipe TDS New  
**Contexto:** Week 12 do ROADMAP

### Contexto

Protocolo de renovação automática de certificados para evitar expiração em massa:

**Cenário:**
- 1.000+ dispositivos em campo com certificados de 10 anos
- Sem renovação automática, todos expiram simultaneamente após 10 anos
- Intervenção manual (visita técnica) de 1.000 dispositivos seria inviável

**Requisitos:**
1. Renovação deve ser automática (over-the-air)
2. Evitar renovação em massa simultânea (pico de carga)
3. Garantir que dispositivo offline não perca a validade

### Decisão

**Renovação OTA com 2 anos de antecedência + Rate limiting (10 devices/day)**

**Protocolo:**
```python
# tds_new/management/commands/renovar_certificados.py
class Command(BaseCommand):
    def handle(self, *args, **options):
        # Buscar certificados que expiram em 2 anos ou menos
        limite = timezone.now() + timedelta(days=730)  # 2 anos
        
        certificados = CertificadoDevice.objects.filter(
            expires_at__lte=limite,
            is_revoked=False
        ).order_by('expires_at')[:10]  # Max 10 por dia
        
        for cert in certificados:
            # Gerar novo certificado
            novo_cert = cert_service.gerar_certificado(
                mac_address=cert.mac_address,
                conta_id=cert.conta_id,
                validade_anos=10
            )
            
            # Publicar comando OTA para dispositivo baixar novo cert
            mqtt_client.publish(
                f'tds_new/devices/{cert.mac_address}/commands',
                json.dumps({
                    'command': 'renew_certificate',
                    'download_url': f'https://api.tds.com/certs/{novo_cert.id}/'
                })
            )
```

### Consequências

#### ✅ Positivas
- **Sem expiração em massa:** Renovação distribuída ao longo de 2 anos
- **Rate limiting:** Max 10 devices/dia evita pico de carga
- **Garantia de funcionamento:** Dispositivo offline por <2 anos continua funcionando
- **Zero intervenção manual:** Completamente automatizado

#### ⚠️ Negativas
- Certificado antigo e novo coexistem por um período (mitigado por revogação do antigo após sucesso)
- Requer endpoint HTTPS seguro para download de certificados

#### 🔧 Mitigações
- **Revogação automática:** Certificado antigo revogado após dispositivo confirmar renovação
- **Retry automático:** Dispositivo offline tentará renovar ao reconectar
- **Auditoria:** Log de todas as renovações (sucesso/falha)

### Alternativas Rejeitadas

**Opção A: Renovação manual (visita técnica):**
- ❌ Inviável economicamente (1.000+ dispositivos)
- ❌ Alto risco de esquecimento (expiração)

**Opção B: Renovação em massa (todos de uma vez):**
- ❌ Pico de carga no servidor
- ❌ Risco de DDoS acidental

### Implementação

**Cron Job:**
```bash
# /etc/cron.d/tds-renew-certs
0 2 * * * cd /var/www/tds-new && python manage.py renovar_certificados >> /var/log/tds/cert-renewal.log 2>&1
```

**API Endpoint:**
```python
# tds_new/api/views.py
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_certificado(request, certificado_id):
    # Autenticar dispositivo via mTLS
    cert = CertificadoDevice.objects.get(id=certificado_id)
    return Response({
        'certificate_pem': cert.certificate_pem,
        'private_key_pem': cert.private_key_pem
    })
```

**Documentação:**
- [PROVISIONAMENTO_IOT.md - Seção 7](../PROVISIONAMENTO_IOT.md#rotação-de-certificados)
- [ROADMAP.md - Week 12](../ROADMAP.md#week-12-ota-certificate-renewal)

**Testes:**
- `tds_new/tests/test_ota_renewal.py` (unit tests)
- Teste de integração: simular renovação de 100 dispositivos

---

## 📝 TEMPLATE PARA NOVOS ADRs

```markdown
## ADR-XXX: Título da Decisão

**Data:** DD/MM/YYYY  
**Status:** 🔵 Em Discussão | ✅ Aprovado | ❌ Rejeitado | ⚠️ Obsoleto  
**Decisor:** Nome/Equipe  
**Contexto:** Week XX do ROADMAP / Sprint XX

### Contexto
[Descreva o problema ou oportunidade que motivou a decisão]

**Opções avaliadas:**
- Opção A: [Descrição]
- Opção B: [Descrição]

**Requisitos críticos:**
1. [Requisito 1]
2. [Requisito 2]

### Decisão
[Descrição clara da decisão tomada]

### Consequências

#### ✅ Positivas
- [Benefício 1]
- [Benefício 2]

#### ⚠️ Negativas
- [Trade-off 1]
- [Trade-off 2]

#### 🔧 Mitigações
- [Como mitigar trade-off 1]

### Alternativas Rejeitadas
[Por que outras opções foram descartadas]

### Implementação
**Código:** [Arquivos relevantes]  
**Documentação:** [Links para docs]  
**Testes:** [Arquivos de teste]
```

---

## ADR-005: MQTT Consumer Location - Backend vs Infrastructure

**Data:** 18/02/2026  
**Status:** ✅ **APROVADO**  
**Decisor:** Equipe de Arquitetura  
**Contexto:** Implementação Fase 2 - MQTT Consumer Telemetria

### Contexto

**Questão crítica:** Onde implementar o MQTT Consumer que processa telemetria de dispositivos IoT?

**Opções avaliadas:**

1. **Dentro do Backend Django** (`/tds_new/consumers/`)
   - Consumer como parte da aplicação Django
   - Acesso direto ao Django ORM
   - Deploy acoplado

2. **Na Infraestrutura Separada** (`/infrastructure/mqtt-consumer/`)
   - Consumer como microservice standalone
   - Comunica com backend via REST API
   - Deploy independente

3. **Híbrido** (`/infrastructure/django-mqtt-consumer/`)
   - Container separado usando Django
   - Importa código do backend (models, services)
   - Conecta ao mesmo banco

### Decisão

**✅ Opção 1: Consumer DENTRO do Backend Django** (`/tds_new/consumers/`)

**Motivos:**
- ✅ **Simplicidade** - 1 serviço, 1 deploy, menos overhead
- ✅ **Baixa Latência** - Sem overhead de API REST (~100ms economizados)
- ✅ **Reutilização de Código** - Usa models, services, validators existentes
- ✅ **Transações Atômicas** - Garantia de consistência (bulk insert → update gateway)
- ✅ **Fase MVP** - Projeto em estágio inicial, escala prematura é overengineering
- ✅ **Padrão Django Channels** - Comum processar eventos em Django

**Implementação:**
```python
# tds_new/consumers/mqtt_telemetry.py
import paho.mqtt.client as mqtt
from tds_new.services.telemetry_processor import TelemetryProcessorService

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload)
    service = TelemetryProcessorService(...)
    service.processar_telemetria(payload)
```

**Arquitetura (Fase 1):**
```
┌─────────────────────────────────────┐
│  Django Backend                     │
│  ├── REST API (Gunicorn - 2 workers)│
│  ├── MQTT Consumer (thread)         │  ← AQUI
│  └── Celery Tasks                   │
└─────────────────────────────────────┘
   ↓ acesso direto ORM
┌─────────────────────────────────────┐
│  PostgreSQL + TimescaleDB           │
└─────────────────────────────────────┘
```

### Comparação de Performance

| Métrica | Opção 1: Django | Opção 2: Microservice | Opção 3: Híbrido |
|---------|-----------------|----------------------|------------------|
| **Latência** | 🟢 100-200ms | 🟡 200-400ms | 🟢 100-200ms |
| **Throughput** | 🟡 5k msgs/s | 🟢 50k msgs/s | 🟡 5k msgs/s |
| **Simplicidade** | 🟢 1 serviço | 🔴 2 serviços | 🟡 2 serviços |
| **Escalabilidade** | 🔴 Acoplada | 🟢 Independente | 🟢 Independente |
| **Manutenibilidade** | 🟢 Alta | 🔴 Duplicação | 🟢 Alta |

**Decisão:** Opção 1 é ideal para **MVP e primeiros 6-12 meses**

### Estratégia de Evolução

**Quando Migrar para Opção 3 (Híbrido):**
- ✅ Se >100 gateways ativos
- ✅ Se >5.000 leituras/minuto
- ✅ Se consumer consumir >50% CPU do backend
- ✅ Se precisar escalar consumer independente

**Quando Migrar para Opção 2 (Microservice Go/Rust):**
- ✅ Se >1.000 gateways
- ✅ Se >50.000 leituras/minuto
- ✅ Se latência <50ms for crítica
- ✅ Se Python for gargalo de performance

**Migração Gradual (Quando chegar a hora):**
```bash
# 1. Criar Dockerfile separado
FROM python:3.12-slim
COPY tds_new/consumers/ /app/consumers/
CMD ["python", "manage.py", "start_mqtt_consumer"]

# 2. Deploy Blue-Green
docker compose up -d mqtt-consumer-new
systemctl stop tds-new-mqtt-consumer  # Antiga
# Monitorar, testar, commit ou rollback
```

### Consequências

#### ✅ Positivas
- Desenvolvimento mais rápido (menos infra para gerenciar)
- Debugging mais fácil (mesmo ambiente)
- Logs centralizados (Django logging)
- Transações atômicas (insert leituras + update gateway = 1 transação)
- Código DRY (validações, transformações em 1 lugar)

#### ⚠️ Negativas
- Escalabilidade acoplada (precisa escalar Django inteiro)
- Deploy acoplado (mudança no consumer = restart backend)
- Monolito (viola SRP - backend REST + consumer no mesmo processo)

#### 🔧 Mitigações
- Isolar código em `tds_new/consumers/` (fácil extrair depois)
- Monitorar métricas de CPU/memória por componente
- Preparar Dockerfile do consumer para migração futura
- Revisar esta decisão a cada 3 meses ou ao atingir 100 gateways

### Alternativas Rejeitadas

**Opção 2 (Microservice REST) rejeitada para MVP:**
- ❌ Latência adicional de 50-100ms inaceitável
- ❌ Duplicação de validações/transformações
- ❌ Complexidade prematura (YAGNI - You Ain't Gonna Need It)
- ❌ Overhead de autenticação entre serviços

**Opção 3 (Híbrido) adiada:**
- ⏸️ Solução ótima para Fase 2 (crescimento)
- ⏸️ Mas adiciona complexidade sem ganho imediato no MVP
- ⏸️ Implementar quando escala justificar

### Implementação

**Código:**
- `tds_new/consumers/mqtt_telemetry.py` (250 linhas)
- `tds_new/consumers/mqtt_config.py` (80 linhas)
- `tds_new/services/telemetry_processor.py` (200 linhas)
- `tds_new/management/commands/start_mqtt_consumer.py` (80 linhas)

**Documentação:**
- [ADR-005-MQTT-CONSUMER-LOCATION.md](ADR-005-MQTT-CONSUMER-LOCATION.md) (análise completa)
- [INTEGRACAO.md](INTEGRACAO.md) (fluxo end-to-end, linhas 200-500)
- [VIABILIDADE_TELEMETRIA.md](../VIABILIDADE_TELEMETRIA.md) (Fase 2, código completo)

**Testes:**
- `tests/integration/test_e2e_telemetria.py`
- `tests/simuladores/simulador_gateway.py`

**Referências:**
- Martin Fowler - Monolith First Pattern
- 12-Factor App - Processes
- Sam Newman - Building Microservices (extract microservices, don't start with them)

---

**Última atualização:** 18/02/2026  
**Total de ADRs:** 5 (todos aprovados)  
**Status:** 🟢 Ativo
