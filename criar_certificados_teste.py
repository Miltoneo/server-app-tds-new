"""
Script para criar certificados de teste para os gateways existentes

Execução: python criar_certificados_teste.py
"""

import os
import sys
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.utils import timezone
from tds_new.models import Gateway, CertificadoDevice, Conta

print("=" * 80)
print("🔐 CRIANDO CERTIFICADOS DE TESTE PARA GATEWAYS")
print("=" * 80)
print()

# Buscar todos os gateways
gateways = Gateway.objects.all()

if gateways.count() == 0:
    print("❌ Não há gateways no banco para criar certificados!")
    sys.exit(1)

print(f"✅ Encontrados {gateways.count()} gateway(s)")
print()

certificados_criados = 0
certificados_existentes = 0

for gw in gateways:
    print(f"Gateway: {gw.codigo} (MAC: {gw.mac})")
    
    # Verificar se já existe certificado
    cert_existente = CertificadoDevice.objects.filter(mac_address=gw.mac).first()
    
    if cert_existente:
        print(f"  ⚠️ Certificado já existe: {cert_existente.serial_number}")
        certificados_existentes += 1
    else:
        # Criar certificado de teste
        serial_number = f"TEST-{gw.mac.replace(':', '').upper()}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        cert = CertificadoDevice.objects.create(
            mac_address=gw.mac,
            serial_number=serial_number,
            certificate_pem=f"""-----BEGIN CERTIFICATE-----
MIICertificadoTeste{gw.codigo}Base64EncodedContent
Este é um certificado de TESTE criado automaticamente
Para gateway: {gw.codigo}
MAC Address: {gw.mac}
Serial Number: {serial_number}
-----END CERTIFICATE-----""",
            expires_at=timezone.now() + timedelta(days=3650),  # 10 anos
            conta=gw.conta,
            created_by=None  # Sistema
        )
        
        print(f"  ✅ Certificado criado: {cert.serial_number}")
        print(f"     Expira em: {cert.expires_at.strftime('%d/%m/%Y')}")
        print(f"     Conta: {cert.conta.name if cert.conta else 'Sem conta'}")
        certificados_criados += 1
    
    print()

print("=" * 80)
print("📊 RESUMO")
print("=" * 80)
print(f"✅ Certificados criados: {certificados_criados}")
print(f"⚠️ Certificados já existentes: {certificados_existentes}")
print(f"📦 Total de certificados no banco: {CertificadoDevice.objects.count()}")
print()

if certificados_criados > 0:
    print("🎉 SUCESSO! Certificados criados com sucesso.")
    print()
    print("🔗 Próximo passo:")
    print("   1. Iniciar servidor: python manage.py runserver")
    print("   2. Acessar: http://localhost:8000/tds_new/admin-sistema/provisionamento/certificados/")
    print("   3. Clicar no botão 'Alocar' ao lado de cada certificado")
    print()
else:
    print("ℹ️ Nenhum certificado novo foi criado (todos já existem).")
    print()

print("=" * 80)
