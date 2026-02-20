# Provisionamento IoT — Referência de Implementação

**Projeto:** TDS New — Sistema de Telemetria  
**Atualizado:** 20/02/2026 | **Migrations:** 0001–0006 aplicadas

---

## Índice

1. [Comparação dos Fluxos](#comparação-dos-fluxos)
2. [Modelos Django](#modelos-django)
3. [Fluxo 1 — Per-Device Factory](#fluxo-1--per-device-factory)
4. [Fluxo 2 — Bootstrap + Auto-Register](#fluxo-2--bootstrap--auto-register)
5. [CertificadoService — Métodos Implementados](#certificadoservice--métodos-implementados)
6. [Interface Admin — URLs](#interface-admin--urls)
7. [Configuração Mosquitto mTLS](#configuração-mosquitto-mtls)
8. [Análise Revisada — Aderência às Boas Práticas](#análise-revisada--aderência-às-boas-práticas)
9. [Referências](#referências)

---

## Comparação dos Fluxos

| Aspecto                                          | Fluxo 1 — Per-Device Factory                              | Fluxo 2 — Bootstrap + Auto-Register                                  |
|--------------------------------------------------|-----------------------------------------------------------|-----------------------------------------------------------------------|
| **Resumo**                                       | Cert individual gerado antes da saída da fábrica          | Cert compartilhado na fábrica; cert individual emitido após alocação  |
| **Cert gravado em fábrica**                      | `device.crt` / `device.key` — único por device           | `bootstrap.crt` / `bootstrap.key` — único para todo o lote           |
| **Quantidade de certs de fábrica**               | Um por device                                             | Um por lote                                                           |
| **`device_id` e tenant conhecidos na fábrica**   | ✅ Sim — obrigatório                                      | ❌ Não — definidos pelo admin no backoffice depois                    |
| **Cert de operação emitido em**                  | Fábrica, pelo admin (antes do flash)                      | Backoffice, automaticamente ao alocar o device                        |
| **Etapas no campo**                              | Nenhuma — conecta direto com cert operacional             | Boot → auto-registro HTTP → admin aloca → técnico re-flasha NVS `tls/` |
| **Intervenção do admin**                         | Pré-fábrica: gera cert + baixa ZIP                        | Pós-instalação: aloca device pendente à conta                         |
| **Intervenção do técnico no campo**              | Nenhuma                                                   | Re-flash do namespace `tls/` com cert operacional                     |
| **Acesso MQTT — primeiro boot**                  | Pleno — `telemetry/{gateway_code}/#`                      | Restrito — `tds/provision/#` (via bootstrap cert)                     |
| **Acesso MQTT — operacional**                    | Desde o primeiro boot                                     | Após re-flash com `device.crt`                                        |
| **Namespace NVS final**                          | `tls/cert`, `tls/key`, `tls/ca_crt`                      | Idem — gravado em dois momentos (bootstrap → substituído)             |
| **Validade do cert**                             | 10 anos (`DEVICE_CERT_VALIDITY_DAYS = 3650`)              | 10 anos (mesmo parâmetro)                                             |
| **Estados de `RegistroProvisionamento`**         | Não se aplica                                             | `PENDENTE` → `PROVISIONADO` ou `REJEITADO`                           |
| **Revogação de emergência**                      | Por device — revoga `CertificadoDevice`                   | Por lote — revoga `BootstrapCertificate`; impede todo o lote          |
| **Complexidade de fábrica**                      | Alta — requer integração com backoffice por device        | Baixa — mesmo ZIP para toda a linha de produção                       |
| **Complexidade de campo**                        | Baixa                                                     | Média — requer conectividade HTTP + re-flash pós-alocação             |
| **Caso de uso ideal**                            | Devices pré-vendidos com tenant conhecido                 | Produção em lote com alocação posterior ao cliente                    |

---

## Modelos Django

### `tds_new/models/dispositivos.py`

```python
class Gateway(SaaSBaseModel):
    device_id         = CharField(24, unique=True)  # identidade lógica MQTT; gravado em fábrica
    serial_number     = CharField(24)               # identidade física irrevogável (PCB)
    mac               = CharField(17)               # aa:bb:cc:dd:ee:ff — hardware-burned (eFuse)
    gateway_code      = CharField(32)               # derivado em firmware: "{device_id}-{LAST4HEX_MAC}"
    modelo            = CharField(24)               # ex: "DCU-1800"
    hardware_version  = CharField(12)
    nome              = CharField(100, null=True)
    is_online         = BooleanField(default=False)
    last_seen         = DateTimeField(null=True)
    firmware_version  = CharField(20, null=True)
```

Tópico MQTT operacional: `telemetry/{gateway_code}/data`

---

### `tds_new/models/certificados.py` — Migration 0001–0006

```python
class CertificadoDevice(SaaSBaseModel):
    # Certificado X.509 de operação — um por gateway ativo
    gateway            = ForeignKey(Gateway, on_delete=CASCADE)
    certificate_pem    = TextField()         # certificado público assinado pela CA
    csr_pem            = TextField(null=True) # CSR enviado pelo device (fluxo PKI correto)
    cert_serial        = CharField(50)
    fingerprint_sha256 = CharField(64)
    expires_at         = DateTimeField()     # 10 anos
    is_revoked         = BooleanField(default=False)
    revoked_at         = DateTimeField(null=True)
    revoke_reason      = CharField(30, null=True)
    renewal_scheduled  = BooleanField(default=False)  # OTA renewal agendado
    renewal_date       = DateTimeField(null=True)      # data de início da renovação
    # private_key_pem [LEGADO — NÃO USE]: chave deve ser gerada e mantida no device


class BootstrapCertificate(BaseAuditMixin):
    # Certificado compartilhado gravado em todos os devices de fábrica.
    # Não pertence a nenhuma conta (global/sistema).
    # Permite apenas conexão ao tópico de provisionamento.
    # Apenas um pode estar ativo por vez.
    label              = CharField(100)
    certificate_pem    = TextField()
    private_key_pem    = TextField()        # apagado do banco após o download do ZIP de fábrica
    serial_number      = CharField(50, unique=True)
    fingerprint_sha256 = CharField(64)
    expires_at         = DateTimeField()     # 10 anos
    is_active          = BooleanField(default=True)
    is_revoked         = BooleanField(default=False)
    revoked_at         = DateTimeField(null=True)
    revoke_reason      = CharField(50, null=True)
    revoke_notes       = TextField(null=True)


class RegistroProvisionamento(BaseAuditMixin):
    # Registro enviado pelo device no primeiro boot via bootstrap cert.
    # Permanece PENDENTE até o admin alocar o device a uma conta.
    mac_address          = CharField(17)
    serial_number_device = CharField(50, null=True)
    modelo               = CharField(50, null=True)
    fw_version           = CharField(30, null=True)
    ip_origem            = CharField(45, null=True)
    bootstrap_cert       = ForeignKey(BootstrapCertificate, null=True, on_delete=SET_NULL)
    csr_pem              = TextField(null=True)  # CSR enviado pelo device (migration 0006)
    status               = CharField(20)    # PENDENTE | PROVISIONADO | REJEITADO
    gateway              = ForeignKey(Gateway, null=True, on_delete=SET_NULL)
    certificado          = OneToOneField(CertificadoDevice, null=True, on_delete=SET_NULL)
    processado_por       = ForeignKey(CustomUser, null=True, on_delete=SET_NULL)
    processado_em        = DateTimeField(null=True)
    notas_admin          = TextField(null=True)
```

---

## Fluxo 1 — Per-Device Factory

Certificado individual gerado **antes** do device sair da fábrica.

```
Admin
  └─▶ /admin-sistema/provisionamento/certificados/gerar/
          └─▶ CertificadoService.gerar_certificado_factory(device_id, conta, gateway)
                  ├─ Gera RSA 2048 + CSR (CN = device_id)
                  ├─ Assina com CA interna (10 anos)
                  └─ Salva CertificadoDevice (status=ATIVO)

Admin baixa ZIP de provisionamento:
  ├─ device.crt   ← certificado TLS do device
  ├─ device.key   ← chave privada
  ├─ ca.crt       ← CA raiz do broker
  └─ README_nvs.txt  ← valores prontos para flash NVS

Fábrica flasha NVS na placa:
  namespace: tls
  ├─ tls/cert    = device.crt
  ├─ tls/key     = device.key
  └─ tls/ca_crt  = ca.crt

Campo — device ligado:
  └─▶ ESP32 conecta ao broker via mTLS
          ├─ Broker valida: certificado assinado pela CA ✓
          └─▶ Publica em: telemetry/{gateway_code}/data
```

---

## Fluxo 2 — Bootstrap + Auto-Register

Um único certificado compartilhado grava em **todos** os devices de fábrica.  
O certificado de operação individual é emitido **depois**, quando o device chega ao campo.

### Fase 1 — Fábrica (preparação única)

```
Admin
  └─▶ /admin-sistema/provisionamento/bootstrap/gerar/
          └─▶ CertificadoService.gerar_bootstrap_cert(label)
                  ├─ RSA 2048 + assinado pela CA (10 anos)
                  ├─ Desativa bootstrap anterior (um ativo por vez)
                  └─ Salva BootstrapCertificate (is_active=True)

Download ZIP (gravado em TODOS os devices do lote):
  ├─ bootstrap.crt
  ├─ bootstrap.key
  ├─ ca.crt
  └─ README_nvs.txt
        namespace: bootstrap
        ├─ bootstrap/cert    = bootstrap.crt
        ├─ bootstrap/key     = bootstrap.key
        └─ bootstrap/ca_crt  = ca.crt
```

### Fase 2 — Campo (primeiro boot)

```
ESP32 conecta ao broker com bootstrap cert (mTLS)
  ├─ Broker valida: assinado pela CA ✓
  └─ Permissão restrita: somente tds/provision/#

Device envia registro:
  POST /tds_new/api/provision/register/
  {
    "mac":                   "aa:bb:cc:dd:ee:ff",   // obrigatório
    "serial":                "DCU-8210-001234",      // opcional
    "modelo":                "DCU-8210",             // opcional
    "fw_version":            "4.0.1",                // opcional
    "bootstrap_fingerprint": "AA:BB:CC:...",         // opcional — fingerprint do bootstrap cert
    "csr_pem":               "-----BEGIN CERTIFICATE REQUEST-----\n..." // opcional — firmware atualizado
  }

  auto_register_view  (views/api/provisionamento.py)
    ├─ Extrai IP de origem (X-Forwarded-For ou REMOTE_ADDR)
    ├─ Rate limiting por IP: max 10 req/hora (PROVISION_RATE_LIMIT_MAX/WINDOW)
    │    → 429 { "status": "error", "code": "rate_limited" }
    ├─ Valida presença e formato do MAC (regex aa:bb:cc:dd:ee:ff)
    │    → 400 { "status": "error", "code": "invalid_request" }
    └─▶ CertificadoService.processar_auto_registro()
            ├─ Idempotente: exclui apenas status REJEITADO da busca
            │    → se MAC já possui registro PENDENTE ou PROVISIONADO:
            │         retorna registro existente (criado=False)
            └─ Cria RegistroProvisionamento(status=PENDENTE, csr_pem=...)  se MAC novo

  Resposta — primeiro registro (HTTP 200):
    { "status": "ok", "code": "registered",
      "message": "Device registrado. Aguardando alocação pelo administrador.",
      "registro_id": <int> }

  Resposta — MAC já registrado (HTTP 200):
    { "status": "ok", "code": "already_registered",
      "message": "Device já registrado. Status: <status>",
      "registro_status": "PENDENTE" | "PROVISIONADO",
      "registro_id": <int> }
    // se PROVISIONADO: message = "Device já provisionado. Use o certificado individual."

  Resposta — MAC rejeitado anteriormente:
    novo RegistroProvisionamento criado (status=PENDENTE)  ← registro REJEITADO é ignorado

  Resposta — erro (HTTP 400 / 429 / 500):
    { "status": "error", "code": "invalid_request" | "rate_limited" | "server_error", "message": "..." }
```

### Fase 3 — Admin aloca o device

```
/admin-sistema/provisionamento/registros/
  ├─ Tabela de devices PENDENTES (MAC, modelo, firmware, IP)
  └─▶ "Alocar" → processar_registro_view
          ├─ Seleciona conta (tenant)
          ├─ Define device_id + nome_gateway
          ├─ Gateway criado na conta selecionada
          ├─ Geração do cert (modo determinado pelo registro):
          │     se registro.csr_pem preenchido (firmware atualizado):
          │       → gerar_certificado_de_csr()   ← PKI correto: chave não sai do device
          │     senão (firmware legado):
          │       → gerar_certificado_factory()  ← [LEGADO] registra aviso no log
          ├─ registro.status = PROVISIONADO
          └─▶ Redireciona para download do ZIP de provisionamento
```

### Fase 4 — Técnico reconfigura o device

```
Flasha namespace: tls  (substitui bootstrap)
  ├─ tls/cert    = device.crt
  ├─ tls/key     = device.key
  └─ tls/ca_crt  = ca.crt

Device reinicia → conecta com cert de operação
  └─▶ Acesso pleno: telemetry/{gateway_code}/data
```

### Estados de `RegistroProvisionamento`

```
[device faz POST]
      |
      v
  PENDENTE --> (admin rejeita) --> REJEITADO
      |
      +-- (admin aloca) --> PROVISIONADO  ← cert gerado automaticamente
```

### Firmware ESP32 — auto-registro

```cpp
// Chamado no primeiro boot após conectar ao broker com bootstrap cert
bool sendAutoRegister(const String& serial, const String& modelo, const String& fwVersion) {
    WiFiClientSecure client;
    client.setCACert(SERVER_CA_CERT);  // mesma CA do broker

    HTTPClient http;
    http.begin(client, "https://onkoto.com.br/tds_new/api/provision/register/");
    http.addHeader("Content-Type", "application/json");

    StaticJsonDocument<256> doc;
    doc["mac"]        = getMac();   // WiFi.macAddress()
    doc["serial"]     = serial;
    doc["modelo"]     = modelo;
    doc["fw_version"] = fwVersion;

    String body;
    serializeJson(doc, body);

    int code = http.POST(body);
    // 200/201: { "status": "ok", "code": "registered" | "already_registered" }
    http.end();
    return (code == 200 || code == 201);
}
```

---

## CertificadoService — Métodos Implementados

Arquivo: `tds_new/services/certificados.py`

| Método                                                                                       | Descrição                                                                        |
|----------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| `gerar_certificado_de_csr(device_id, csr_pem, mac, conta, gateway)`                          | Assina CSR enviado pelo device; `private_key_pem=None` ← **fluxo PKI correto**   |
| `gerar_certificado_factory(device_id, mac, conta, gateway)`                                  | Gera RSA 2048 no servidor **[LEGADO]** — usar somente sem CSR do firmware         |
| `gerar_zip_provisionamento(certificado)`                                                     | ZIP com `device.crt`, `device.key`, `ca.crt`, `README_nvs.txt`                   |
| `revogar_certificado(certificado, motivo, notas, usuario)`                                   | Revoga cert + atualiza CRL do broker automaticamente                              |
| `gerar_bootstrap_cert(label, criado_por)`                                                    | Gera cert compartilhado de fábrica, desativa anterior                            |
| `gerar_zip_bootstrap(bootstrap)`                                                             | ZIP de fábrica (erro se chave já removida — re-download não permitido)           |
| `revogar_bootstrap_cert(bootstrap, motivo, notas, usuario)`                                  | Revogação de emergência + atualiza CRL do broker                                 |
| `processar_auto_registro(mac, serial, modelo, fw_version, ip, bootstrap_fingerprint, csr_pem)` | Cria `RegistroProvisionamento` (idempotente); persiste CSR se enviado           |

CA carregada de: `settings.MQTT_CA_CERT_PATH` + `settings.MQTT_CA_KEY_PATH`

### CRL — `tds_new/utils/crl.py`

| Função                     | Descrição                                                                              |
|---------------------------|-----------------------------------------------------------------------------------------|
| `gerar_crl_pem()`         | Gera CRL PEM com todos os certs revogados (`CertificadoDevice` + `BootstrapCertificate`) |
| `atualizar_crl_broker()`  | Escreve CRL em `settings.MQTT_CRL_PATH`; fail-safe (não propaga excessão)               |

CRL atualizada automaticamente a cada `revogar()` (modelo `CertificadoDevice` e `BootstrapCertificate`).

---

## Interface Admin — URLs

Prefixo: `/tds_new/admin-sistema/provisionamento/`

### Certificados Per-Device

| URL                           | View                        | Ação                              |
|-------------------------------|-----------------------------|-----------------------------------|
| `certificados/`               | `admin_certificados_list`   | Lista todos os certificados       |
| `certificados/gerar/`         | `admin_gerar_certificado`   | Gera certificado para um gateway  |
| `certificados/<id>/download/` | `admin_download_certificado` | Download do ZIP                  |
| `certificados/<id>/revogar/`  | `admin_revogar_certificado` | Revogar certificado               |

### Bootstrap Certs

| URL                        | View                       | Ação                                                   |
|----------------------------|----------------------------|--------------------------------------------------------|
| `bootstrap/`               | `admin_bootstrap_list`     | Lista todos os bootstrap certs                         |
| `bootstrap/gerar/`         | `admin_gerar_bootstrap`    | Gera novo + download ZIP                               |
| `bootstrap/<id>/download/` | `admin_download_bootstrap` | Download do ZIP (**único** — chave removida após o download) |
| `bootstrap/<id>/revogar/`  | `admin_revogar_bootstrap`  | Revogação de emergência                                  |

### Registros de Auto-Registro

| URL                         | View                        | Ação                        |
|-----------------------------|-----------------------------|-----------------------------|
| `registros/`                | `admin_registros_pendentes` | Lista com filtro por status |
| `registros/<id>/processar/` | `admin_processar_registro`  | Aloca device + emite cert   |
| `registros/<id>/rejeitar/`  | `admin_rejeitar_registro`   | Rejeita (POST only)         |

### API (device → backend)

| Método  | URL                        | Autenticação    | Descrição                       |
|---------|----------------------------|-----------------|---------------------------------|
| `POST`  | `api/provision/register/`  | mTLS no broker  | Auto-registro no primeiro boot  |

---

## Configuração Mosquitto mTLS

```
listener 8883
cafile   /etc/mosquitto/certs/ca.crt
certfile /etc/mosquitto/certs/server.crt
keyfile  /etc/mosquitto/certs/server.key
crlfile  /etc/mosquitto/certs/ca.crl
require_certificate true
use_identity_as_username true
```

> `crlfile` — Mosquitto recarrega a CRL a cada nova conexão TLS (sem restart).
> O caminho deve coincidir com `settings.MQTT_CRL_PATH`.

Permissões por tipo de cert (ACL):

- **Certificado de operação** (`CertificadoDevice`): acesso a `telemetry/{gateway_code}/#`
- **Bootstrap cert** (`BootstrapCertificate`): acesso restrito a `tds/provision/#`

---

## Análise Revisada — Aderência às Boas Práticas

> Avaliação do estado atual da implementação (20/02/2026) em relação às boas práticas de PKI para IoT.

### ✅ Já estava correto (baseline)

| Prática | Evidência no código |
|---------|---------------------|
| mTLS obrigatório — broker rejeita conexões sem cert cliente | `require_certificate true` no Mosquitto |
| CA interna — não exposta, não compartilhada | `settings.MQTT_CA_CERT_PATH` + `MQTT_CA_KEY_PATH`; chave nunca trafega na rede |
| Isolamento do bootstrap — topico restrito | ACL: `BootstrapCertificate` → somente `tds/provision/#` |
| Um bootstrap ativo por vez | `BootstrapCertificate.is_active`; `gerar_bootstrap_cert()` desativa o anterior |
| Validade explícita nos certs | `DEVICE_CERT_VALIDITY_DAYS = 3650`; `expires_at` persistido |
| Revogação suportada no modelo | `is_revoked`, `revoked_at`, `revoke_reason` em ambos os modelos |
| Bootstrap cert vinculado ao registro | `RegistroProvisionamento.bootstrap_cert` — rastreabilidade completa |

---

### ✅ Implementado nesta revisão (20/02/2026)

#### 1 — Rate Limiting no endpoint de auto-registro

| Item | Detalhe |
|------|---------|
| **O quê** | Limite de 10 requisições por hora por IP de origem |
| **Onde** | `auto_register_view` → `_check_rate_limit(ip)` |
| **Mecanismo** | `django.core.cache` (Redis); chave `autoregister_rl:{ip}`; fail-open se cache indisponível |
| **Resposta** | HTTP 429 `{ "code": "rate_limited" }` |
| **Config** | `PROVISION_RATE_LIMIT_MAX=10`, `PROVISION_RATE_LIMIT_WINDOW=3600` em `settings.py` |
| **Risco mitigado** | Enumeração de MACs / flood de registros falsos |

#### 2 — CRL publicada automaticamente após revogação

| Item | Detalhe |
|------|---------|
| **O quê** | CRL PEM gerada e escrita em disco a cada `revogar()` |
| **Onde** | `tds_new/utils/crl.py` → `atualizar_crl_broker()` |
| **Chamado por** | `CertificadoDevice.revogar()` e `BootstrapCertificate.revogar()` |
| **Mosquitto** | `crlfile /etc/mosquitto/certs/ca.crl`; recarrega a cada nova conexão TLS |
| **Fail-safe** | Exceção na escrita do arquivo **não** desfaz a revogação no banco |
| **Risco mitigado** | Cert revogado continuaria aceito pelo broker até reinício manual |

#### 3 — Chave privada do bootstrap removida após download

| Item | Detalhe |
|------|---------|
| **O quê** | `private_key_pem` zerado no banco imediatamente após o admin baixar o ZIP |
| **Onde** | `download_bootstrap_zip_view` → `bootstrap.limpar_chave_privada()` |
| **Guard** | `gerar_zip_bootstrap()` lança `CertificadoServiceError` se chave já removida |
| **Re-download** | Impossível por design — admin ciente via log `WARNING` |
| **Risco mitigado** | Chave privada do bootstrap exposta indefinidamente no banco de dados |

#### 4 — Agendamento automático de renovação (Celery)

| Item | Detalhe |
|------|---------|
| **O quê** | Tasks periódicas para agendamento e alerta de renovação de certs |
| **Onde** | `tds_new/tasks.py`; `prj_tds_new/celery.py` |
| **Tasks** | `agendar_renovacoes_task` (diário 02h UTC) · `alertar_renovacoes_pendentes_task` (por hora) |
| **Lógica** | Certs com `expires_at <= now + 730d` → `renewal_scheduled=True`; alerta se `renewal_date <= now` |
| **Risco mitigado** | Expiração silenciosa de certificados operacionais |

#### 5a — CSR enviado pelo device (server-side)

| Item | Detalhe |
|------|---------|
| **O quê** | Device envia o próprio CSR no POST de auto-registro |
| **Onde** | `RegistroProvisionamento.csr_pem` (migration 0006); `processar_auto_registro(csr_pem=...)` |
| **Fluxo PKI** | Admin aloca → se `registro.csr_pem` → `gerar_certificado_de_csr()` → chave nunca sai do device |
| **Legado** | Se `registro.csr_pem` vazio → `gerar_certificado_factory()` com `logger.warning("[LEGADO]")` |
| **Risco mitigado** | Chave privada do device trafegando entre servidor e fábrica |

---

### ⏳ Pendente — Fase 5b (firmware)

| Item | Situação | Impacto |
|------|----------|---------|
| **CSR no firmware ESP32** | Firmware atual **não** gera CSR — continua sem campo `csr_pem` no POST | Admin usa `gerar_certificado_factory()` (legado) até atualização do firmware |
| **Migração do campo legado** | `CertificadoDevice.private_key_pem` ainda existe no modelo (comentado como LEGADO) | Remover somente após todos os devices com firmware atualizado |

**Próximos passos — Fase 5b:**

```cpp
// Firmware ESP32 — geração de CSR com mbedTLS
// 1. Gerar par RSA 2048 e armazenar em NVS (tls/key)
// 2. Gerar CSR com CN = device_id (ou MAC como fallback pré-alocação)
// 3. Incluir "csr_pem" no body do POST /api/provision/register/

// Após implementar, o doc snippet em "Firmware ESP32 — auto-registro"
// deve incluir doc["csr_pem"] = gerarCSR();
```

---

### Matriz consolidada de riscos PKI

| Risco | Gravidade | Status |
|-------|-----------|--------|
| Cert revogado aceito pelo broker | Alta | ✅ Resolvido — CRL auto-publicada |
| Flood de registros falsos por IP | Média | ✅ Resolvido — Rate limiting 429 |
| Chave bootstrap exposta no banco | Alta | ✅ Resolvido — Removida pós-download |
| Expiração silenciosa de certs | Alta | ✅ Resolvido — Celery tasks |
| Chave privada do device no servidor | Alta | 🔄 Parcial — backend pronto; aguarda firmware |
| CA key sem HSM/TPM | Muito Alta | ⚠️ Aceito — escopo futuro |
| Bootstrap cert compartilhado por lote | Média | ⚠️ Aceito por design — revogação em lote disponível |
| Renovação OTA não automatizada | Média | ⚠️ Aceito — alertas implementados; OTA é escopo futuro |

---

## Referências

- Modelos: `tds_new/models/certificados.py`, `tds_new/models/dispositivos.py`
- Serviço: `tds_new/services/certificados.py`
- CRL utils: `tds_new/utils/crl.py`
- Tasks Celery: `tds_new/tasks.py`, `prj_tds_new/celery.py`
- Views admin: `tds_new/views/admin/provisionamento.py`
- View API: `tds_new/views/api/provisionamento.py`
- Forms: `tds_new/forms/provisionamento.py`
- URLs: `tds_new/urls.py`
- Templates: `tds_new/templates/admin_sistema/provisionamento/`
- Migrations: `tds_new/migrations/0001`–0006
- Arquitetura end-to-end: `docs/architecture/INTEGRACAO.md`
- Decisões arquiteturais: `docs/architecture/DECISOES.md`
