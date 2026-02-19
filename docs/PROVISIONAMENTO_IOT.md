# Provisionamento IoT — Referência de Implementação

**Projeto:** TDS New — Sistema de Telemetria  
**Atualizado:** 19/02/2026 | **Migrations:** 0001–0005 aplicadas

---

## Índice

1. [Modelos Django](#modelos-django)
2. [Fluxo 1 — Per-Device Factory](#fluxo-1--per-device-factory)
3. [Fluxo 2 — Bootstrap + Auto-Register](#fluxo-2--bootstrap--auto-register)
4. [CertificadoService — Métodos Implementados](#certificadoservice--métodos-implementados)
5. [Interface Admin — URLs](#interface-admin--urls)
6. [Configuração Mosquitto mTLS](#configuração-mosquitto-mtls)
7. [Referências](#referências)

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

### `tds_new/models/certificados.py` — Migration 0001–0005

```python
class CertificadoDevice(SaaSBaseModel):
    # Certificado X.509 de operação — um por gateway ativo
    gateway            = ForeignKey(Gateway, on_delete=CASCADE)
    certificate_pem    = TextField()         # certificado público assinado pela CA
    cert_serial        = CharField(50)
    fingerprint_sha256 = CharField(64)
    expires_at         = DateTimeField()     # 10 anos
    is_revoked         = BooleanField(default=False)
    revoked_at         = DateTimeField(null=True)
    # private_key_pem AUSENTE: chave gerada e mantida no device (NVS)


class BootstrapCertificate(BaseAuditMixin):
    # Certificado compartilhado gravado em todos os devices de fábrica.
    # Não pertence a nenhuma conta (global/sistema).
    # Permite apenas conexão ao tópico de provisionamento.
    # Apenas um pode estar ativo por vez.
    label              = CharField(100)
    certificate_pem    = TextField()
    private_key_pem    = TextField()        # armazenado só para geração do ZIP de fábrica
    serial_number      = CharField(50, unique=True)
    fingerprint_sha256 = CharField(64)
    expires_at         = DateTimeField()    # 1 ano
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
    status               = CharField(20)    # PENDENTE | ALOCADO | PROVISIONADO | REJEITADO
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
                  ├─ RSA 2048 + assinado pela CA (1 ano)
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
  { "mac": "aa:bb:cc:dd:ee:ff", "serial": "...", "modelo": "DCU-8210", "fw_version": "4.0.1" }

  └─▶ CertificadoService.processar_auto_registro()
          ├─ Valida formato MAC
          ├─ Idempotente: retorna registro existente se MAC já enviou
          └─ Cria RegistroProvisionamento (status=PENDENTE)

  Resposta: { "status": "ok", "code": "registered" | "already_registered" }
```

### Fase 3 — Admin aloca o device

```
/admin-sistema/provisionamento/registros/
  ├─ Tabela de devices PENDENTES (MAC, modelo, firmware, IP)
  └─▶ "Alocar" → processar_registro_view
          ├─ Seleciona conta (tenant)
          ├─ Define device_id + nome_gateway
          ├─ "Gerar certificado agora?"
          │    SIM → gerar_certificado_factory() → CertificadoDevice
          │           registro.status = PROVISIONADO
          │    NÃO → registro.status = ALOCADO  (cert emitido depois)
          └─ Gateway criado na conta selecionada
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
      +-- (admin aloca sem cert) --> ALOCADO --> (cert emitido depois) --> PROVISIONADO
      |
      +-- (admin aloca com cert) --> PROVISIONADO
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

| Método | Descrição |
|--------|-----------|
| `gerar_certificado_factory(device_id, gateway, conta_id)` | Gera RSA 2048, assina com CA, salva `CertificadoDevice` |
| `gerar_zip_provisionamento(certificado)` | ZIP com `device.crt`, `device.key`, `ca.crt`, `README_nvs.txt` |
| `revogar_certificado(certificado, motivo, notas, usuario)` | Revoga cert + registra log |
| `gerar_bootstrap_cert(label, criado_por)` | Gera cert compartilhado de fábrica, desativa anterior |
| `gerar_zip_bootstrap(bootstrap)` | ZIP com `bootstrap.crt`, `bootstrap.key`, `ca.crt`, `README_nvs.txt` |
| `revogar_bootstrap_cert(bootstrap, motivo, notas, usuario)` | Revogação de emergência |
| `processar_auto_registro(mac, serial, modelo, fw_version, ip, bootstrap_fingerprint)` | Cria `RegistroProvisionamento` (idempotente) |

CA carregada de: `settings.MQTT_CA_CERT_PATH` + `settings.MQTT_CA_KEY_PATH`

---

## Interface Admin — URLs

Prefixo: `/tds_new/admin-sistema/provisionamento/`

### Certificados Per-Device

| URL | View | Ação |
|-----|------|------|
| `certificados/` | `admin_certificados_list` | Lista todos os certificados |
| `certificados/gerar/` | `admin_gerar_certificado` | Gera certificado para um gateway |
| `certificados/<id>/download/` | `admin_download_certificado` | Download do ZIP |
| `certificados/<id>/revogar/` | `admin_revogar_certificado` | Revogar certificado |

### Bootstrap Certs

| URL | View | Ação |
|-----|------|------|
| `bootstrap/` | `admin_bootstrap_list` | Lista todos os bootstrap certs |
| `bootstrap/gerar/` | `admin_gerar_bootstrap` | Gera novo + download ZIP |
| `bootstrap/<id>/download/` | `admin_download_bootstrap` | Re-download do ZIP |
| `bootstrap/<id>/revogar/` | `admin_revogar_bootstrap` | Revogação de emergência |

### Registros de Auto-Registro

| URL | View | Ação |
|-----|------|------|
| `registros/` | `admin_registros_pendentes` | Lista com filtro por status |
| `registros/<id>/processar/` | `admin_processar_registro` | Aloca device + emite cert |
| `registros/<id>/rejeitar/` | `admin_rejeitar_registro` | Rejeita (POST only) |

### API (device → backend)

| Método | URL | Autenticação | Descrição |
|--------|-----|-------------|-----------|
| `POST` | `api/provision/register/` | mTLS no broker | Auto-registro no primeiro boot |

---

## Configuração Mosquitto mTLS

```
listener 8883
cafile   /etc/mosquitto/certs/ca.crt
certfile /etc/mosquitto/certs/server.crt
keyfile  /etc/mosquitto/certs/server.key
require_certificate true
use_identity_as_username true
```

Permissões por tipo de cert (ACL):

- **Certificado de operação** (`CertificadoDevice`): acesso a `telemetry/{gateway_code}/#`
- **Bootstrap cert** (`BootstrapCertificate`): acesso restrito a `tds/provision/#`

---

## Referências

- Modelos: `tds_new/models/certificados.py`, `tds_new/models/dispositivos.py`
- Serviço: `tds_new/services/certificados.py`
- Views admin: `tds_new/views/admin/provisionamento.py`
- View API: `tds_new/views/api/provisionamento.py`
- Forms: `tds_new/forms/provisionamento.py`
- URLs: `tds_new/urls.py`
- Templates: `tds_new/templates/admin_sistema/provisionamento/`
- Migrations: `tds_new/migrations/0001`–`0005`
- Arquitetura end-to-end: `docs/architecture/INTEGRACAO.md`
- Decisões arquiteturais: `docs/architecture/DECISOES.md`
