# PKI — Certificate Authority

Este diretório contém os arquivos da CA (Certificate Authority) usada para assinar os
certificados dos dispositivos IoT (mTLS com o broker MQTT Mosquitto).

## Estrutura esperada

```
certs/
└── ca/
    ├── ca.key          ← Chave privada da CA (NUNCA commitar — ver .gitignore)
    ├── ca.crt          ← Certificado público da CA (pode ser distribuído)
    ├── ca.srl          ← Arquivo de serial counter (gerado pelo openssl)
    └── README.md       ← Este arquivo
```

## Gerar a CA (primeiro uso — desenvolvimento)

```bash
# 1. Gerar chave privada RSA 4096 bits
openssl genrsa -out certs/ca/ca.key 4096

# 2. Gerar certificado auto-assinado (10 anos)
openssl req -new -x509 -days 3650 -key certs/ca/ca.key -out certs/ca/ca.crt \
  -subj "/C=BR/ST=SP/O=Onkoto IoT/CN=Onkoto-Root-CA"
```

## Assinar CSR de dispositivo (referência — uso via Django admin)

O Django admin realiza a assinatura automaticamente via `tds_new/services/certificados.py`.
O fluxo via linha de comando é documentado aqui apenas como referência:

```bash
# Assinar CSR enviado pelo dispositivo
openssl x509 -req -in device.csr -CA certs/ca/ca.crt -CAkey certs/ca/ca.key \
  -CAcreateserial -out client.crt -days 3650 -sha256
```

## Segurança

- **`ca.key`** → NUNCA commitar. Protegido por `.gitignore`. Em produção: usar HashiCorp Vault ou AWS KMS.
- **`ca.crt`** → Arquivo público. Incluído nos ZIPs de provisionamento e no broker MQTT.
- Em produção, a variável `MQTT_CA_KEY_PATH` no `.env.prod` deve apontar para o caminho seguro da chave.

## Ambiente de produção

No servidor de produção, os caminhos são configurados via `.env.prod`:

```env
MQTT_CA_CERT_PATH=/etc/ssl/onkoto-ca/ca.crt
MQTT_CA_KEY_PATH=/etc/ssl/onkoto-ca/ca.key
MQTT_CA_KEY_PASSWORD=
```
