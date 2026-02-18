# 🔐 Análise: Estratégias de Provisionamento para Hardware IoT Multi-Plataforma

**Projeto:** TDS New - Sistema de Telemetria e Monitoramento IoT  
**Data:** 18/02/2026  
**Versão:** 1.1 (Atualizado)  
**Autor:** Equipe TDS New

---

## 📋 ÍNDICE

1. [Cronograma de Implementação](#-cronograma-de-implementação)
2. [Visão Geral](#visão-geral)
3. [Contexto do Projeto](#contexto-do-projeto)
4. [Plataformas Suportadas](#plataformas-suportadas)
5. [Estratégias de Provisionamento](#estratégias-de-provisionamento)
6. [Fluxo de Certificação mTLS](#fluxo-de-certificação-mtls)
7. [Implementação por Plataforma](#implementação-por-plataforma)
8. [Segurança e Melhores Práticas](#segurança-e-melhores-práticas)
9. [Automação e Ferramentas](#automação-e-ferramentas)
10. [Troubleshooting](#troubleshooting)
11. [Referências](#referências)

---

## 📅 CRONOGRAMA DE IMPLEMENTAÇÃO

As estratégias descritas neste documento serão implementadas ao longo de 16 semanas conforme o **[ROADMAP.md](ROADMAP.md)**:

| Semana | Entregas | Status | Detalhes |
|--------|----------|--------|----------|
| **6-7** | Modelos Django (Gateway, Dispositivo, CertificadoDevice) | 🔵 Planejado | [Ver ROADMAP](ROADMAP.md#week-6-7-gateways--dispositivos-iot) |
| **8-9** | MQTT Consumer + Telemetria em tempo real | 🔵 Planejado | [Ver ADR-001](architecture/DECISOES.md#adr-001-mqtt-consumer-strategy) |
| **10-11** | API REST de Provisionamento | 🔵 Planejado | Estratégia 2 (API REST) |
| **12** | OTA Certificate Renewal System | 🔵 Planejado | [Ver ADR-004](architecture/DECISOES.md#adr-004-ota-certificate-renewal-protocol) |
| **13-14** | Firmware ESP32/RPi com mTLS | 🔵 Planejado | Seção 7 deste documento |
| **15** | Provisionamento Zero-Touch | 🔵 Planejado | Estratégia 3 (Bootstrap) |

### 🎯 Decisões Arquiteturais Relacionadas

Este documento implementa as seguintes decisões arquiteturais documentadas em **[architecture/DECISOES.md](architecture/DECISOES.md)**:

- **[ADR-001](architecture/DECISOES.md#adr-001-mqtt-consumer-strategy)**: MQTT Consumer Strategy (Django vs Telegraf)
- **[ADR-002](architecture/DECISOES.md#adr-002-certificate-management-strategy)**: Certificate Management Strategy (10 anos)
- **[ADR-003](architecture/DECISOES.md#adr-003-topic-mqtt-sem-conta_id)**: Topic MQTT sem conta_id
- **[ADR-004](architecture/DECISOES.md#adr-004-ota-certificate-renewal-protocol)**: OTA Certificate Renewal Protocol

**Para cronograma completo:** Ver **[ROADMAP.md](ROADMAP.md)**

---

## 🎯 VISÃO GERAL

### Objetivo
Estabelecer estratégias padronizadas para provisionamento de dispositivos IoT em múltiplas plataformas (ESP32, Raspberry Pi), garantindo:
- ✅ **Segurança**: Autenticação mTLS com certificados X.509
- ✅ **Escalabilidade**: Provisionamento de centenas de dispositivos
- ✅ **Multi-tenant**: Isolamento de credenciais por conta
- ✅ **Facilidade**: Processo automatizado e auditado

### Escopo
Este documento aborda:
- **Gateway (ESP32/Raspberry Pi)**: Dispositivo que coleta dados via Modbus RTU e publica via MQTT
- **Broker MQTT (Mosquitto)**: Servidor com autenticação mTLS obrigatória
- **Backend Django**: Gerenciamento de certificados e dispositivos
- **Ferramentas de Provisionamento**: Scripts Python e CLI Arduino

---

## 📊 CONTEXTO DO PROJETO

### Arquitetura de Hardware

```
┌─────────────────────────────────────────────────────────────────┐
│ GATEWAY IoT (ESP32 / Raspberry Pi)                              │
│                                                                  │
│ ┌────────────────┐  RS485  ┌──────────────────────────────┐   │
│ │ Microcontrolador│◄────────┤ Dispositivos Modbus RTU      │   │
│ │ ESP32 / RPi     │         │ • Medidor de Água (Slave 1)  │   │
│ │                 │         │ • Medidor de Energia (Slave 2)│   │
│ │ Cert. X.509     │         │ • Sensor de Temp. (Slave 3)  │   │
│ │ MAC: aa:bb:...  │         │ • ... até 8-32 dispositivos  │   │
│ └────────────────┘          └──────────────────────────────┘   │
│         │                                                        │
│         │ WiFi/Ethernet                                         │
└─────────┼────────────────────────────────────────────────────────┘
          │
          │ MQTT/TLS (porta 8883)
          ↓
┌─────────────────────────────────────────────────────────────────┐
│ BROKER MOSQUITTO (servidor MQTT)                                │
│                                                                  │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ Autenticação mTLS (Mutual TLS)                           │   │
│ │ • Verifica certificado do cliente (gateway)              │   │
│ │ • Valida contra CA authority local                       │   │
│ │ • Rejeita certificados revogados (CRL)                   │   │
│ │ • Rejeita certificados expirados (10 anos)               │   │
│ └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│ Topic: tds_new/devices/{mac_address}/telemetry                 │
└─────────────────────────────────────────────────────────────────┘
          │
          │ Subscriber (Django/Celery)
          ↓
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND DJANGO + TIMESCALEDB                                    │
│                                                                  │
│ • Gerencia certificados (CertificadoDevice model)              │
│ • Armazena leituras em hypertable                              │
│ • Processa alarmes e alertas                                   │
│ • Exibe dashboards e relatórios                                │
└─────────────────────────────────────────────────────────────────┘
```

> **📖 Para detalhes sobre o fluxo completo de integração entre camadas:**  
> Consulte **[architecture/INTEGRACAO.md](architecture/INTEGRACAO.md)** - documentação end-to-end com diagrama de sequência, formato de dados em cada camada, tratamento de erros e métricas de performance (~300ms end-to-end).

### Modelo de Dados (Django)

```python
# tds_new/models/dispositivos.py
class Gateway(SaaSBaseModel):
    """Gateway de telemetria"""
    codigo = CharField(30)           # Exemplo: GW001
    mac = CharField(17)               # aa:bb:cc:dd:ee:ff (identificador único)
    nome = CharField(100)
    qte_max_dispositivos = IntegerField(default=8)
    is_online = BooleanField(default=False)
    last_seen = DateTimeField(null=True)
    firmware_version = CharField(20, null=True)

# tds_new/models/certificados.py
class CertificadoDevice(SaaSBaseModel):
    """Certificados X.509 dos dispositivos"""
    mac_address = CharField(17)       # aa:bb:cc:dd:ee:ff
    certificate_pem = TextField       # Certificado público (PEM)
    private_key_pem = TextField       # Chave privada (NUNCA expor via API)
    serial_number = CharField(50)     # Número serial único do certificado
    expires_at = DateTimeField        # Validade: 10 anos
    is_revoked = BooleanField(default=False)
    revoked_at = DateTimeField(null=True)
```

---

## 🖥️ PLATAFORMAS SUPORTADAS

### 1. ESP32 (Microcontrolador)

**Características:**
- **CPU**: Dual-core Xtensa 32-bit LX6 (240 MHz)
- **RAM**: 520 KB SRAM
- **Flash**: 4 MB (mínimo recomendado)
- **Conectividade**: WiFi 802.11 b/g/n, Bluetooth
- **GPIO**: UART, SPI, I2C, RS485 (via módulo MAX485)
- **TLS**: Suporte nativo via WiFiClientSecure (mbedTLS)

**Vantagens:**
- ✅ Baixo custo (~R$ 30-50)
- ✅ Baixo consumo de energia
- ✅ Ampla comunidade Arduino/PlatformIO
- ✅ Suporte TLS 1.2 nativo

**Desvantagens:**
- ⚠️ Memória limitada (cuidado com certificados grandes)
- ⚠️ Sistema de arquivos SPIFFS (volátil)
- ⚠️ Atualização OTA mais complexa

**Linguagem de Programação:**
- C/C++ (Arduino IDE ou PlatformIO)

---

### 2. Raspberry Pi (SBC - Single Board Computer)

**Modelos Suportados:**
- **Raspberry Pi Zero W/2W**: WiFi, 512 MB RAM
- **Raspberry Pi 3/4**: Ethernet + WiFi, 1-8 GB RAM
- **Raspberry Pi 5**: USB-C power, PCIe, 4-8 GB RAM

**Vantagens:**
- ✅ Sistema operacional completo (Raspberry Pi OS / Ubuntu)
- ✅ Biblioteca Python rica (paho-mqtt, pyserial, etc)
- ✅ Armazenamento persistente (SD card)
- ✅ Fácil debug e logs
- ✅ Atualização OTA simples (git pull + systemd restart)

**Desvantagens:**
- ⚠️ Maior custo (~R$ 200-600)
- ⚠️ Maior consumo de energia
- ⚠️ Requer sistema operacional (manutenção)

**Linguagem de Programação:**
- Python 3.10+ (recomendado)

---

## 🔄 ESTRATÉGIAS DE PROVISIONAMENTO

### Estratégia 1: Provisionamento Manual (Pequena Escala)
**Cenário:** Até 10 dispositivos | Ambiente de desenvolvimento

#### Fluxo:
```
1. Administrador acessa Django Admin
   └─ Cria Gateway manualmente (código, MAC, nome)
   └─ Sistema gera certificado automaticamente
   
2. Certificado é baixado via interface web
   └─ Download de arquivo ZIP: {mac_address}_certs.zip
   └─ Contém: client.crt, client.key, ca.crt
   
3. Certificados são copiados para o dispositivo
   ESP32:   Via Serial (Arduino IDE) ou WebSerial
   RPi:     Via SCP ou USB stick
   
4. Firmware é atualizado com credenciais
   ESP32:   Recompila e faz upload via USB
   RPi:     Edita config.json e reinicia serviço
   
5. Dispositivo conecta ao broker MQTT
   └─ Verifica certificado
   └─ Atualiza is_online=True e last_seen
```

**Implementação Django:**

```python
# tds_new/views/gateway.py
from django.views.generic import DetailView
from django.http import FileResponse
from io import BytesIO
import zipfile

class GatewayDownloadCertificadoView(LoginRequiredMixin, DetailView):
    """
    Download de certificados do gateway em formato ZIP
    """
    model = Gateway
    
    def get(self, request, *args, **kwargs):
        gateway = self.get_object()
        certificado = CertificadoDevice.objects.get(
            conta=gateway.conta,
            mac_address=gateway.mac
        )
        
        # Criar arquivo ZIP em memória
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            zip_file.writestr('client.crt', certificado.certificate_pem)
            zip_file.writestr('client.key', certificado.private_key_pem)
            zip_file.writestr('ca.crt', settings.MQTT_CA_CERT)
            zip_file.writestr('README.txt', f"""
Gateway: {gateway.codigo}
MAC: {gateway.mac}
Validade: {certificado.expires_at.strftime('%d/%m/%Y')}
Serial Number: {certificado.serial_number}

Instruções:
1. Copie os arquivos .crt e .key para o dispositivo
2. Configure o firmware para usar estes certificados
3. Conecte ao broker MQTT: {settings.MQTT_BROKER_HOST}:8883
""")
        
        zip_buffer.seek(0)
        response = FileResponse(
            zip_buffer,
            as_attachment=True,
            filename=f'{gateway.mac}_certificados.zip'
        )
        
        # Log de auditoria
        logger.info(f"Certificados baixados: {gateway.codigo} by {request.user.email}")
        
        return response
```

---

### Estratégia 2: Provisionamento por API REST (Média Escala)
**Cenário:** 10-100 dispositivos | Automação parcial

#### Fluxo:
```
1. Técnico usa script Python para provisionar
   └─ Script: provision_gateway.py --mac aa:bb:cc:dd:ee:ff --codigo GW001
   
2. Script faz POST para API Django REST
   └─ Endpoint: POST /api/v1/gateways/provision/
   └─ Payload: {mac, codigo, nome, conta_id}
   └─ Response: {certificate_pem, private_key_pem, ca_pem}
   
3. Script salva certificados em disco local
   └─ Pasta: ./certs/{mac_address}/
   
4. Script copia certificados para dispositivo
   ESP32:   Via esptool.py (flash filesystem)
   RPi:     Via SSH (scp ou rsync)
   
5. Script reinicia dispositivo remotamente
   ESP32:   Comando reset via Serial
   RPi:     SSH: sudo systemctl restart gateway-mqtt
```

**Implementação API (Django REST Framework):**

```python
# tds_new/api/serializers.py
from rest_framework import serializers
from tds_new.models import Gateway, CertificadoDevice

class ProvisionGatewaySerializer(serializers.Serializer):
    mac_address = serializers.RegexField(
        regex=r'^([0-9a-f]{2}:){5}[0-9a-f]{2}$',
        error_messages={'invalid': 'MAC inválido. Use formato aa:bb:cc:dd:ee:ff'}
    )
    codigo = serializers.CharField(max_length=30)
    nome = serializers.CharField(max_length=100)
    conta_id = serializers.IntegerField()
    
    def validate_conta_id(self, value):
        if not Conta.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Conta inválida ou inativa")
        return value
    
    def validate(self, data):
        # Verifica duplicação de MAC
        if Gateway.objects.filter(
            conta_id=data['conta_id'],
            mac=data['mac_address']
        ).exists():
            raise serializers.ValidationError("MAC já cadastrado nesta conta")
        return data

# tds_new/api/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from tds_new.services.certificados import CertificadoService

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def provision_gateway(request):
    """
    Provisiona um novo gateway e gera certificados
    
    POST /api/v1/gateways/provision/
    {
        "mac_address": "aa:bb:cc:dd:ee:ff",
        "codigo": "GW001",
        "nome": "Gateway Sede Principal",
        "conta_id": 1
    }
    
    Response:
    {
        "gateway_id": 123,
        "certificate_pem": "-----BEGIN CERTIFICATE-----...",
        "private_key_pem": "-----BEGIN PRIVATE KEY-----...",
        "ca_pem": "-----BEGIN CERTIFICATE-----...",
        "expires_at": "2036-02-17T10:00:00Z",
        "serial_number": "ABC123456789"
    }
    """
    serializer = ProvisionGatewaySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # Criar gateway
    gateway = Gateway.objects.create(
        conta_id=serializer.validated_data['conta_id'],
        mac=serializer.validated_data['mac_address'],
        codigo=serializer.validated_data['codigo'],
        nome=serializer.validated_data['nome'],
        created_by=request.user
    )
    
    # Gerar certificado
    cert_service = CertificadoService()
    certificado = cert_service.gerar_certificado(
        mac_address=gateway.mac,
        conta_id=gateway.conta_id,
        validade_anos=10
    )
    
    # Log de auditoria
    logger.info(
        f"Gateway provisionado via API: {gateway.codigo} "
        f"by {request.user.email} | IP: {request.META.get('REMOTE_ADDR')}"
    )
    
    return Response({
        'gateway_id': gateway.id,
        'certificate_pem': certificado.certificate_pem,
        'private_key_pem': certificado.private_key_pem,
        'ca_pem': settings.MQTT_CA_CERT,
        'expires_at': certificado.expires_at,
        'serial_number': certificado.serial_number,
        'mqtt_broker': settings.MQTT_BROKER_HOST,
        'mqtt_port': settings.MQTT_TLS_PORT,
        'mqtt_topic': f'tds_new/devices/{gateway.mac}/telemetry'
    }, status=status.HTTP_201_CREATED)
```

**Script Python Cliente:**

```python
#!/usr/bin/env python3
"""
Script de provisionamento de gateway via API REST
Uso: python provision_gateway.py --mac aa:bb:cc:dd:ee:ff --codigo GW001
"""

import argparse
import requests
import os
import json
from pathlib import Path

API_BASE_URL = 'https://onkoto.com.br/api/v1'
API_TOKEN = os.getenv('TDS_API_TOKEN')  # Token de autenticação

def provision_gateway(mac_address: str, codigo: str, nome: str, conta_id: int):
    """
    Provisiona gateway via API e salva certificados localmente
    """
    headers = {
        'Authorization': f'Token {API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'mac_address': mac_address,
        'codigo': codigo,
        'nome': nome,
        'conta_id': conta_id
    }
    
    # POST para API
    response = requests.post(
        f'{API_BASE_URL}/gateways/provision/',
        json=payload,
        headers=headers,
        timeout=30
    )
    response.raise_for_status()
    
    data = response.json()
    
    # Criar pasta para certificados
    cert_dir = Path(f'./certs/{mac_address}')
    cert_dir.mkdir(parents=True, exist_ok=True)
    
    # Salvar certificados
    (cert_dir / 'client.crt').write_text(data['certificate_pem'])
    (cert_dir / 'client.key').write_text(data['private_key_pem'])
    (cert_dir / 'ca.crt').write_text(data['ca_pem'])
    
    # Salvar metadados
    metadata = {
        'gateway_id': data['gateway_id'],
        'mac_address': mac_address,
        'codigo': codigo,
        'expires_at': data['expires_at'],
        'serial_number': data['serial_number'],
        'mqtt_broker': data['mqtt_broker'],
        'mqtt_port': data['mqtt_port'],
        'mqtt_topic': data['mqtt_topic']
    }
    (cert_dir / 'metadata.json').write_text(json.dumps(metadata, indent=2))
    
    print(f"✅ Gateway provisionado com sucesso!")
    print(f"   ID: {data['gateway_id']}")
    print(f"   Certificados salvos em: {cert_dir}")
    print(f"   Validade: {data['expires_at']}")
    print(f"\n🔐 Próximos passos:")
    print(f"   1. Copie os certificados para o dispositivo")
    print(f"   2. Configure o firmware para usar {data['mqtt_broker']}:{data['mqtt_port']}")
    print(f"   3. Publique telemetria em: {data['mqtt_topic']}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Provisionar gateway IoT')
    parser.add_argument('--mac', required=True, help='MAC address (aa:bb:cc:dd:ee:ff)')
    parser.add_argument('--codigo', required=True, help='Código do gateway (ex: GW001)')
    parser.add_argument('--nome', required=True, help='Nome descritivo')
    parser.add_argument('--conta-id', type=int, required=True, help='ID da conta')
    
    args = parser.parse_args()
    provision_gateway(args.mac, args.codigo, args.nome, args.conta_id)
```

---

### Estratégia 3: Provisionamento Zero-Touch (Grande Escala)
**Cenário:** 100+ dispositivos | Produção em massa

#### Fluxo:
```
1. Fabricante pre-provisiona dispositivos
   └─ Durante fabricação, grava MAC na EEPROM
   └─ Firmware inclui URL de bootstrap: https://provision.onkoto.com.br
   
2. Dispositivo liga pela primeira vez
   └─ Conecta em WiFi temporário (WPS ou AP mode)
   └─ Faz POST para /bootstrap/ com MAC address
   └─ Recebe token de ativação temporário (24h)
   
3. Usuário final ativa gateway via app mobile ou web
   └─ Escaneia QR Code do dispositivo
   └─ App envia token de ativação + conta_id para API
   └─ Backend valida e associa gateway à conta
   
4. Backend gera certificados e envia para dispositivo
   └─ Dispositivo baixa certificados via HTTPS
   └─ Salva em filesystem protegido
   └─ Reinicia e conecta ao broker MQTT
   
5. Gateway reporta status online
   └─ Backend atualiza last_seen e is_online=True
```

**Implementação (Serviço de Bootstrap):**

```python
# tds_new/services/bootstrap.py
import secrets
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache

class BootstrapService:
    """
    Serviço para provisionamento zero-touch
    """
    
    @staticmethod
    def iniciar_bootstrap(mac_address: str):
        """
        Inicia processo de bootstrap para um novo gateway
        Retorna token de ativação com validade de 24h
        """
        # Gerar token único
        token = secrets.token_urlsafe(32)
        
        # Armazenar no Redis com TTL de 24h
        cache_key = f'bootstrap:{mac_address}'
        cache.set(cache_key, {
            'token': token,
            'mac_address': mac_address,
            'created_at': timezone.now().isoformat()
        }, timeout=86400)  # 24 horas
        
        # Log de auditoria
        logger.info(f"Bootstrap iniciado: {mac_address} | Token: {token[:8]}...")
        
        return {
            'activation_token': token,
            'expires_in': 86400,
            'activation_url': f'https://app.tds.com.br/activate/{token}',
            'qr_code_url': f'https://api.qrserver.com/v1/create-qr-code/?data={token}&size=200x200'
        }
    
    @staticmethod
    def ativar_gateway(token: str, conta_id: int, codigo: str, nome: str):
        """
        Ativa gateway usando token de bootstrap e associa à conta
        """
        # Buscar token no cache
        for key in cache.keys('bootstrap:*'):
            data = cache.get(key)
            if data and data['token'] == token:
                mac_address = data['mac_address']
                
                # Criar gateway
                gateway = Gateway.objects.create(
                    conta_id=conta_id,
                    mac=mac_address,
                    codigo=codigo,
                    nome=nome
                )
                
                # Gerar certificado
                cert_service = CertificadoService()
                certificado = cert_service.gerar_certificado(
                    mac_address=mac_address,
                    conta_id=conta_id,
                    validade_anos=10
                )
                
                # Invalidar token
                cache.delete(key)
                
                # Log de auditoria
                logger.info(f"Gateway ativado: {codigo} | MAC: {mac_address}")
                
                return {
                    'gateway_id': gateway.id,
                    'download_url': f'/api/v1/gateways/{gateway.id}/certificados/'
                }
        
        raise ValueError("Token inválido ou expirado")

# tds_new/api/views.py
@api_view(['POST'])
def bootstrap_gateway(request):
    """
    Endpoint de bootstrap para novos dispositivos
    
    POST /api/v1/gateways/bootstrap/
    {
        "mac_address": "aa:bb:cc:dd:ee:ff"
    }
    
    Response:
    {
        "activation_token": "xyz123...",
        "expires_in": 86400,
        "activation_url": "https://app.tds.com.br/activate/xyz123...",
        "qr_code_url": "https://..."
    }
    """
    mac_address = request.data.get('mac_address')
    
    # Validar formato MAC
    if not re.match(r'^([0-9a-f]{2}:){5}[0-9a-f]{2}$', mac_address):
        return Response(
            {'error': 'MAC address inválido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Iniciar bootstrap
    bootstrap_service = BootstrapService()
    result = bootstrap_service.iniciar_bootstrap(mac_address)
    
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ativar_gateway(request):
    """
    Ativa gateway usando token de bootstrap
    
    POST /api/v1/gateways/ativar/
    {
        "activation_token": "xyz123...",
        "conta_id": 1,
        "codigo": "GW001",
        "nome": "Gateway Sede"
    }
    """
    token = request.data.get('activation_token')
    conta_id = request.data.get('conta_id')
    codigo = request.data.get('codigo')
    nome = request.data.get('nome')
    
    try:
        bootstrap_service = BootstrapService()
        result = bootstrap_service.ativar_gateway(token, conta_id, codigo, nome)
        return Response(result, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
```

**Firmware ESP32 (Bootstrap):**

```cpp
// ESP32 - Bootstrap Client
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* BOOTSTRAP_URL = "https://provision.onkoto.com.br/api/v1/gateways/bootstrap/";

String getMacAddress() {
    uint8_t mac[6];
    WiFi.macAddress(mac);
    char macStr[18];
    snprintf(macStr, sizeof(macStr), "%02x:%02x:%02x:%02x:%02x:%02x",
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    return String(macStr);
}

void requestBootstrap() {
    HTTPClient http;
    http.begin(BOOTSTRAP_URL);
    http.addHeader("Content-Type", "application/json");
    
    StaticJsonDocument<200> doc;
    doc["mac_address"] = getMacAddress();
    
    String payload;
    serializeJson(doc, payload);
    
    int httpCode = http.POST(payload);
    
    if (httpCode == HTTP_CODE_OK) {
        String response = http.getString();
        
        StaticJsonDocument<512> responseDoc;
        deserializeJson(responseDoc, response);
        
        String activationToken = responseDoc["activation_token"];
        String qrCodeUrl = responseDoc["qr_code_url"];
        
        Serial.println("✅ Bootstrap successful!");
        Serial.print("Activation Token: ");
        Serial.println(activationToken);
        Serial.print("QR Code URL: ");
        Serial.println(qrCodeUrl);
        
        // Exibir QR Code em display OLED (opcional)
        // displayQRCode(activationToken);
        
        // Aguardar ativação (polling periódico)
        waitForActivation(activationToken);
    } else {
        Serial.printf("❌ Bootstrap failed: HTTP %d\n", httpCode);
    }
    
    http.end();
}

void setup() {
    Serial.begin(115200);
    WiFi.begin("SSID", "password");
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    Serial.println("\n✅ WiFi connected");
    Serial.print("MAC Address: ");
    Serial.println(getMacAddress());
    
    // Iniciar bootstrap
    requestBootstrap();
}
```

---

## 🔐 FLUXO DE CERTIFICAÇÃO mTLS

### Geração de Certificados (Backend)

```python
# tds_new/services/certificados.py
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
from django.conf import settings

class CertificadoService:
    """
    Serviço para gerenciamento de certificados X.509
    """
    
    def __init__(self):
        self.ca_cert = self._load_ca_certificate()
        self.ca_key = self._load_ca_private_key()
    
    def _load_ca_certificate(self):
        """Carrega certificado da CA"""
        with open(settings.MQTT_CA_CERT_PATH, 'rb') as f:
            return x509.load_pem_x509_certificate(f.read())
    
    def _load_ca_private_key(self):
        """Carrega chave privada da CA"""
        with open(settings.MQTT_CA_KEY_PATH, 'rb') as f:
            return serialization.load_pem_private_key(
                f.read(),
                password=settings.MQTT_CA_KEY_PASSWORD.encode()
            )
    
    def gerar_certificado(self, mac_address: str, conta_id: int, validade_anos: int = 10):
        """
        Gera certificado X.509 para dispositivo IoT
        
        Args:
            mac_address: MAC address do dispositivo (aa:bb:cc:dd:ee:ff)
            conta_id: ID da conta (multi-tenant)
            validade_anos: Anos de validade (padrão: 10)
        
        Returns:
            CertificadoDevice: Objeto salvo no banco
        """
        # Gerar par de chaves RSA 2048-bit
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        # Subject do certificado
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "SP"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Sao Paulo"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "TDS IoT"),
            x509.NameAttribute(NameOID.COMMON_NAME, mac_address),
        ])
        
        # Datas de validade
        not_valid_before = datetime.utcnow()
        not_valid_after = not_valid_before + timedelta(days=365 * validade_anos)
        
        # Construir certificado
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(self.ca_cert.subject)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(not_valid_before)
            .not_valid_after(not_valid_after)
            .add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(f"{mac_address}.devices.tds.com.br"),
                    x509.DNSName(mac_address),
                ]),
                critical=False
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    key_cert_sign=False,
                    key_agreement=False,
                    content_commitment=False,
                    data_encipherment=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False
                ),
                critical=True
            )
            .add_extension(
                x509.ExtendedKeyUsage([
                    x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH
                ]),
                critical=True
            )
            .sign(self.ca_key, hashes.SHA256())
        )
        
        # Serializar certificado e chave privada
        cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        # Salvar no banco
        certificado = CertificadoDevice.objects.create(
            conta_id=conta_id,
            mac_address=mac_address,
            certificate_pem=cert_pem,
            private_key_pem=key_pem,
            serial_number=str(cert.serial_number),
            expires_at=not_valid_after
        )
        
        logger.info(
            f"Certificado gerado: {mac_address} | "
            f"Serial: {cert.serial_number} | "
            f"Validade: {validade_anos} anos"
        )
        
        return certificado
    
    def revogar_certificado(self, certificado_id: int, motivo: str):
        """
        Revoga certificado (adiciona à CRL)
        """
        certificado = CertificadoDevice.objects.get(id=certificado_id)
        certificado.is_revoked = True
        certificado.revoked_at = timezone.now()
        certificado.revoke_reason = motivo
        certificado.save()
        
        # TODO: Publicar CRL atualizada no broker MQTT
        self._publish_crl()
        
        logger.warning(
            f"Certificado revogado: {certificado.mac_address} | "
            f"Motivo: {motivo}"
        )
```

### Configuração Mosquitto (Broker MQTT)

```conf
# /etc/mosquitto/mosquitto.conf

# Porta TLS obrigatória
listener 8883
protocol mqtt

# Autenticação mTLS (mutual TLS)
cafile /etc/mosquitto/certs/ca.crt
certfile /etc/mosquitto/certs/server.crt
keyfile /etc/mosquitto/certs/server.key

# Requer certificado do cliente
require_certificate true
use_identity_as_username true

# Certificate Revocation List (CRL)
crlfile /etc/mosquitto/certs/ca.crl

# TLS versão mínima
tls_version tlsv1.2

# Cipher suites seguros
ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305

# Log de auditoria
log_dest file /var/log/mosquitto/mosquitto.log
log_type all
connection_messages true
log_timestamp true

# Permissões por topic (baseado em CN do certificado)
acl_file /etc/mosquitto/acl.conf
```

**ACL Configuration:**

```conf
# /etc/mosquitto/acl.conf

# Padrão: negar tudo
pattern read $SYS/#
pattern read #

# Permitir que cada gateway publique apenas no seu próprio topic
# %u = Common Name do certificado (MAC address)
pattern write tds_new/devices/%u/telemetry
pattern write tds_new/devices/%u/status
pattern write tds_new/devices/%u/logs

# Permitir leitura de comandos
pattern read tds_new/devices/%u/commands
```

---

## 🛠️ IMPLEMENTAÇÃO POR PLATAFORMA

### ESP32 (C/Arduino)

```cpp
// ESP32 - Cliente MQTT com mTLS
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <SPIFFS.h>

// Certificados (carregados do SPIFFS)
String ca_cert;
String client_cert;
String client_key;
String mac_address;

WiFiClientSecure espClient;
PubSubClient mqttClient(espClient);

void loadCertificates() {
    // Inicializar SPIFFS
    if (!SPIFFS.begin(true)) {
        Serial.println("❌ Falha ao montar SPIFFS");
        return;
    }
    
    // Carregar CA certificate
    File ca_file = SPIFFS.open("/certs/ca.crt", "r");
    if (ca_file) {
        ca_cert = ca_file.readString();
        ca_file.close();
    }
    
    // Carregar Client certificate
    File cert_file = SPIFFS.open("/certs/client.crt", "r");
    if (cert_file) {
        client_cert = cert_file.readString();
        cert_file.close();
    }
    
    // Carregar Private key
    File key_file = SPIFFS.open("/certs/client.key", "r");
    if (key_file) {
        client_key = key_file.readString();
        key_file.close();
    }
    
    Serial.println("✅ Certificados carregados do SPIFFS");
}

void setupMQTT() {
    // Configurar certificados
    espClient.setCACert(ca_cert.c_str());
    espClient.setCertificate(client_cert.c_str());
    espClient.setPrivateKey(client_key.c_str());
    
    // Configurar broker
    mqttClient.setServer("onkoto.com.br", 8883);
    mqttClient.setCallback(mqttCallback);
    
    // Obter MAC address
    uint8_t mac[6];
    WiFi.macAddress(mac);
    char macStr[18];
    snprintf(macStr, sizeof(macStr), "%02x:%02x:%02x:%02x:%02x:%02x",
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    mac_address = String(macStr);
}

void connectMQTT() {
    while (!mqttClient.connected()) {
        Serial.print("🔄 Conectando ao broker MQTT...");
        
        // Client ID = MAC address
        if (mqttClient.connect(mac_address.c_str())) {
            Serial.println(" ✅ Conectado!");
            
            // Subscribe para comandos
            String commandTopic = "tds_new/devices/" + mac_address + "/commands";
            mqttClient.subscribe(commandTopic.c_str());
            
            // Publicar status online
            String statusTopic = "tds_new/devices/" + mac_address + "/status";
            mqttClient.publish(statusTopic.c_str(), "online", true);
        } else {
            Serial.print(" ❌ Falha: ");
            Serial.println(mqttClient.state());
            delay(5000);
        }
    }
}

void publishTelemetry(float value, const char* unit) {
    StaticJsonDocument<200> doc;
    doc["timestamp"] = millis();
    doc["valor"] = value;
    doc["unidade"] = unit;
    doc["gateway_mac"] = mac_address;
    
    String payload;
    serializeJson(doc, payload);
    
    String topic = "tds_new/devices/" + mac_address + "/telemetry";
    mqttClient.publish(topic.c_str(), payload.c_str());
}

void setup() {
    Serial.begin(115200);
    WiFi.begin("SSID", "password");
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
    }
    
    loadCertificates();
    setupMQTT();
    connectMQTT();
}

void loop() {
    if (!mqttClient.connected()) {
        connectMQTT();
    }
    mqttClient.loop();
    
    // Publicar telemetria a cada 60 segundos
    static unsigned long lastPublish = 0;
    if (millis() - lastPublish > 60000) {
        float temperature = readTemperature();
        publishTelemetry(temperature, "°C");
        lastPublish = millis();
    }
}
```

---

### Raspberry Pi (Python)

```python
#!/usr/bin/env python3
"""
Gateway MQTT para Raspberry Pi com mTLS
"""

import paho.mqtt.client as mqtt
import ssl
import json
import time
from datetime import datetime
from pathlib import Path

# Configuração
MQTT_BROKER = 'onkoto.com.br'
MQTT_PORT = 8883
CERTS_DIR = Path('/etc/gateway-iot/certs')
MAC_ADDRESS = open('/sys/class/net/eth0/address').read().strip()

# Callbacks MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Conectado ao broker MQTT")
        
        # Subscribe para comandos
        topic_commands = f'tds_new/devices/{MAC_ADDRESS}/commands'
        client.subscribe(topic_commands)
        print(f"📥 Subscribed: {topic_commands}")
        
        # Publicar status online
        topic_status = f'tds_new/devices/{MAC_ADDRESS}/status'
        client.publish(topic_status, 'online', qos=1, retain=True)
    else:
        print(f"❌ Falha na conexão: {rc}")

def on_message(client, userdata, msg):
    print(f"📨 Mensagem recebida: {msg.topic}")
    try:
        payload = json.loads(msg.payload.decode())
        handle_command(payload)
    except Exception as e:
        print(f"❌ Erro ao processar mensagem: {e}")

def publish_telemetry(valor, unidade):
    """Publica telemetria no broker MQTT"""
    topic = f'tds_new/devices/{MAC_ADDRESS}/telemetry'
    
    payload = {
        'timestamp': datetime.utcnow().isoformat(),
        'valor': valor,
        'unidade': unidade,
        'gateway_mac': MAC_ADDRESS,
        'firmware_version': '1.0.0'
    }
    
    client.publish(topic, json.dumps(payload), qos=1)
    print(f"📤 Telemetria publicada: {valor} {unidade}")

# Configurar cliente MQTT
client = mqtt.Client(client_id=MAC_ADDRESS)

# Configurar mTLS
client.tls_set(
    ca_certs=str(CERTS_DIR / 'ca.crt'),
    certfile=str(CERTS_DIR / 'client.crt'),
    keyfile=str(CERTS_DIR / 'client.key'),
    cert_reqs=ssl.CERT_REQUIRED,
    tls_version=ssl.PROTOCOL_TLSv1_2,
    ciphers=None
)

client.on_connect = on_connect
client.on_message = on_message

# Conectar ao broker
print(f"🔄 Conectando ao broker: {MQTT_BROKER}:{MQTT_PORT}")
print(f"🆔 Client ID: {MAC_ADDRESS}")

client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

# Loop principal
client.loop_start()

try:
    while True:
        # Coletar dados via Modbus RTU (exemplo simplificado)
        temperatura = read_modbus_sensor(slave_id=1, register=100)
        publish_telemetry(temperatura, '°C')
        
        time.sleep(60)  # Aguardar 60 segundos
except KeyboardInterrupt:
    print("\n⏹️ Parando gateway...")
    
    # Publicar status offline
    topic_status = f'tds_new/devices/{MAC_ADDRESS}/status'
    client.publish(topic_status, 'offline', qos=1, retain=True)
    
    client.loop_stop()
    client.disconnect()
```

---

## 🔒 SEGURANÇA E MELHORES PRÁTICAS

### Proteção de Chaves Privadas

#### ESP32: Usar Secure Boot e Flash Encryption

```cpp
// platformio.ini
[env:esp32]
board_build.partitions = partitions_encrypted.csv
board_build.embed_files = 
    certs/ca.crt
    certs/client.crt
    certs/client.key

// Habilitar flash encryption no sdkconfig
CONFIG_SECURE_FLASH_ENC_ENABLED=y
CONFIG_SECURE_BOOT_ENABLED=y
```

#### Raspberry Pi: Usar File Permissions Restritas

```bash
# Criar usuário dedicado para o gateway
sudo useradd -r -s /bin/false gateway-iot

# Definir ownership e permissões dos certificados
sudo chown -R gateway-iot:gateway-iot /etc/gateway-iot/certs
sudo chmod 700 /etc/gateway-iot/certs
sudo chmod 600 /etc/gateway-iot/certs/client.key
sudo chmod 644 /etc/gateway-iot/certs/client.crt
sudo chmod 644 /etc/gateway-iot/certs/ca.crt

# Executar serviço com usuário dedicado
# /etc/systemd/system/gateway-mqtt.service
[Service]
User=gateway-iot
Group=gateway-iot
ExecStart=/usr/bin/python3 /opt/gateway-iot/mqtt_client.py
```

### Rotação de Certificados

```python
# tds_new/management/commands/renovar_certificados.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tds_new.models import CertificadoDevice
from tds_new.services.certificados import CertificadoService

class Command(BaseCommand):
    help = 'Renova certificados que expiram em 2 anos ou menos'
    
    def handle(self, *args, **options):
        # Buscar certificados próximos da expiração
        limite = timezone.now() + timedelta(days=730)  # 2 anos
        
        certificados = CertificadoDevice.objects.filter(
            expires_at__lte=limite,
            is_revoked=False
        )
        
        renovados = 0
        cert_service = CertificadoService()
        
        for cert in certificados:
            # Revogar certificado antigo
            cert.is_revoked = True
            cert.revoke_reason = 'Renovação programada'
            cert.save()
            
            # Gerar novo certificado
            novo_cert = cert_service.gerar_certificado(
                mac_address=cert.mac_address,
                conta_id=cert.conta_id,
                validade_anos=10
            )
            
            renovados += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Renovado: {cert.mac_address} | "
                    f"Novo serial: {novo_cert.serial_number}"
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎉 Total renovados: {renovados} certificados"
            )
        )
```

**Cron Job (executar mensalmente):**

```bash
# /etc/cron.d/tds-renew-certs
0 2 1 * * cd /var/www/tds-new && /var/www/tds-new/venv/bin/python manage.py renovar_certificados >> /var/log/tds/cert-renewal.log 2>&1
```

### Auditoria de Acessos

```python
# tds_new/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from tds_new.models import Gateway

@receiver(post_save, sender=Gateway)
def log_gateway_status_change(sender, instance, created, **kwargs):
    """
    Log quando gateway muda de status (online/offline)
    """
    if not created and instance.tracker.has_changed('is_online'):
        logger.info(
            f"Gateway status changed: {instance.codigo} | "
            f"Online: {instance.is_online} | "
            f"Last seen: {instance.last_seen}"
        )
```

---

## ⚙️ AUTOMAÇÃO E FERRAMENTAS

### CLI de Provisionamento

```bash
# Instalar CLI
pip install tds-provision-cli

# Configurar credenciais
tds-provision config --api-url https://onkoto.com.br/api/v1 --token YOUR_API_TOKEN

# Provisionar gateway
tds-provision create-gateway \
    --mac aa:bb:cc:dd:ee:ff \
    --codigo GW001 \
    --nome "Gateway Sede Principal" \
    --conta-id 1

# Listar gateways
tds-provision list-gateways --conta-id 1

# Download de certificados
tds-provision download-certs --gateway-id 123 --output ./certs/

# Revogar certificado
tds-provision revoke-cert --gateway-id 123 --reason "Dispositivo comprometido"
```

### Web Interface de Provisionamento

Tela `/admin/gateways/provision/`:

```django
{# tds_new/templates/admin/gateway_provision.html #}
{% extends 'admin/base.html' %}

{% block content %}
<h1>Provisionamento de Gateway</h1>

<form method="post" enctype="multipart/form-data">
    {% csrf_token %}
    
    <div class="form-group">
        <label>Modo de Provisionamento:</label>
        <select name="modo" id="modo-select">
            <option value="manual">Manual (formulário)</option>
            <option value="csv">Lote (CSV)</option>
            <option value="bootstrap">Zero-Touch (QR Code)</option>
        </select>
    </div>
    
    {# Modo Manual #}
    <div id="modo-manual">
        <input type="text" name="mac_address" placeholder="aa:bb:cc:dd:ee:ff">
        <input type="text" name="codigo" placeholder="GW001">
        <input type="text" name="nome" placeholder="Gateway Sede">
        <button type="submit">Provisionar</button>
    </div>
    
    {# Modo CSV #}
    <div id="modo-csv" style="display:none;">
        <input type="file" name="csv_file" accept=".csv">
        <p>Formato CSV: mac_address,codigo,nome</p>
        <button type="submit">Importar CSV</button>
    </div>
    
    {# Modo Bootstrap #}
    <div id="modo-bootstrap" style="display:none;">
        <input type="text" name="mac_address" placeholder="aa:bb:cc:dd:ee:ff">
        <button type="submit">Gerar QR Code</button>
        <div id="qrcode"></div>
    </div>
</form>
{% endblock %}
```

---

## 🩺 TROUBLESHOOTING

### Problema 1: Certificado Rejeitado pelo Broker

**Sintoma:**
```
❌ Falha na conexão MQTT: RC = 5 (Connection refused, not authorized)
```

**Diagnóstico:**
```bash
# Testar certificado manualmente
openssl s_client -connect onkoto.com.br:8883 \
    -CAfile ca.crt \
    -cert client.crt \
    -key client.key \
    -showcerts

# Verificar CN do certificado
openssl x509 -in client.crt -noout -subject

# Verificar validade
openssl x509 -in client.crt -noout -dates
```

**Soluções:**
- ✅ Verificar se certificado não está revogado (CRL)
- ✅ Verificar se MAC address no CN corresponde ao esperado
- ✅ Verificar se certificado não está expirado
- ✅ Verificar se CA certificate é o correto

---

### Problema 2: Gateway Não Atualiza Status Online

**Sintoma:**
```
Gateway conectado ao broker, mas is_online permanece False no Django
```

**Diagnóstico:**
```python
# Verificar logs do Mosquitto
tail -f /var/log/mosquitto/mosquitto.log | grep aa:bb:cc:dd:ee:ff

# Verificar se subscriber Django está rodando
ps aux | grep mqtt_subscriber
```

**Soluções:**
- ✅ Verificar se Celery worker está running
- ✅ Verificar se subscriber está subscrito ao topic correto
- ✅ Verificar firewall (porta 8883 TCP)
- ✅ Testar publicação manual via mosquitto_pub

---

### Problema 3: Memória Insuficiente no ESP32

**Sintoma:**
```
Guru Meditation Error: Core  1 panic'ed (LoadProhibited)
```

**Diagnóstico:**
```cpp
// Verificar memória livre
Serial.print("Free heap: ");
Serial.println(ESP.getFreeHeap());
```

**Soluções:**
- ✅ Usar certificados menores (EC em vez de RSA)
- ✅ Comprimir certificados usando gzip
- ✅ Aumentar partition size no platformio.ini
- ✅ Desabilitar features não essenciais (Bluetooth)

---

## 📚 REFERÊNCIAS

### Documentação Oficial
- **MQTT Specification**: https://mqtt.org/mqtt-specification/
- **Mosquitto mTLS**: https://mosquitto.org/man/mosquitto-tls-7.html
- **Paho MQTT Python**: https://eclipse.dev/paho/index.php?page=clients/python/docs/index.php
- **ESP32 WiFiClientSecure**: https://github.com/espressif/arduino-esp32/tree/master/libraries/WiFiClientSecure
- **Python Cryptography**: https://cryptography.io/en/latest/

### Projetos Relacionados
- **ROADMAP_DESENVOLVIMENTO.md**: Planejamento de 12 semanas do projeto TDS New
- **DIAGRAMA_ER.md**: Diagrama entidade-relacionamento dos modelos Django
- **MQTT_INTEGRATION.md**: Guia de integração MQTT com Django

---

## 📝 CHANGELOG

### v1.0 - 17/02/2026
- ✅ Documentação inicial completa
- ✅ Estratégias de provisionamento (Manual, API, Zero-Touch)
- ✅ Implementação mTLS com certificados X.509
- ✅ Exemplos de código ESP32 e Raspberry Pi
- ✅ Scripts de automação e CLI
- ✅ Guia de troubleshooting

---

**Última atualização:** 17/02/2026  
**Status:** 🟢 Documentação completa e validada  
**Próximos passos:** Implementar serviços de certificação (Week 8-9)
