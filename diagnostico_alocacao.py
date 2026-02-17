"""
Diagnóstico: Interface de Alocação de Gateways
Verifica por que a interface não aparece
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from tds_new.models import Gateway, CertificadoDevice, Conta

print("=" * 80)
print("🔍 DIAGNÓSTICO: INTERFACE DE ALOCAÇÃO DE GATEWAYS")
print("=" * 80)
print()

# 1. Verificar gateways no banco
print("📊 1. GATEWAYS NO BANCO DE DADOS")
print("-" * 80)
gateways = Gateway.objects.all()
print(f"Total de gateways: {gateways.count()}")
print()

for gw in gateways:
    print(f"Gateway ID: {gw.id}")
    print(f"  Código: {gw.codigo}")
    print(f"  MAC: {gw.mac}")
    print(f"  Nome: {gw.nome}")
    print(f"  Conta: {gw.conta.name if gw.conta else 'SEM CONTA (Órfão)'}")
    print()

# 2. Verificar certificados no banco
print("📊 2. CERTIFICADOS NO BANCO DE DADOS")
print("-" * 80)
certificados = CertificadoDevice.objects.all()
print(f"Total de certificados: {certificados.count()}")
print()

if certificados.count() == 0:
    print("⚠️ PROBLEMA IDENTIFICADO: Não há certificados no banco!")
    print("   A lista de certificados estará vazia.")
    print("   O botão 'Alocar' só aparece na lista de certificados.")
    print()
    print("💡 SOLUÇÕES:")
    print("   1. Criar certificados manualmente no admin Django")
    print("   2. Importar certificados via fixture")
    print("   3. Usar factory/script de geração de certificados")
    print()
else:
    for cert in certificados:
        print(f"Certificado MAC: {cert.mac_address}")
        print(f"  Serial: {cert.serial_number}")
        print(f"  Conta: {cert.conta.name if cert.conta else 'SEM CONTA'}")
        
        # Verificar se existe gateway com este MAC
        gw = Gateway.objects.filter(mac=cert.mac_address).first()
        if gw:
            print(f"  ✅ Gateway encontrado: ID {gw.id} - {gw.codigo}")
        else:
            print(f"  ❌ Gateway NÃO encontrado para MAC {cert.mac_address}")
        print()

# 3. Verificar relacionamento Gateway ↔ Certificado
print("📊 3. RELACIONAMENTO GATEWAY ↔ CERTIFICADO")
print("-" * 80)

for gw in gateways:
    cert = CertificadoDevice.objects.filter(mac_address=gw.mac).first()
    if cert:
        print(f"✅ Gateway {gw.mac} → Certificado {cert.serial_number[:16]}...")
    else:
        print(f"⚠️ Gateway {gw.mac} → SEM CERTIFICADO")
        print(f"   Este gateway NÃO aparece na lista de certificados")
        print(f"   (porque a lista é de certificados, não de gateways)")

print()

# 4. Diagnóstico final
print("=" * 80)
print("🎯 DIAGNÓSTICO FINAL")
print("=" * 80)
print()

if certificados.count() == 0:
    print("❌ CAUSA RAIZ: Não há certificados no banco de dados")
    print()
    print("📝 EXPLICAÇÃO:")
    print("   - A interface de alocação é acessada pela lista de certificados")
    print("   - URL: /tds_new/admin-sistema/provisionamento/certificados/")
    print("   - Se não há certificados, a lista está vazia")
    print("   - Logo, não há botão 'Alocar' para clicar")
    print()
    print("🔧 SOLUÇÃO IMEDIATA:")
    print("   1. Criar certificado via Django Admin:")
    print("      http://localhost:8000/admin/tds_new/certificadodevice/add/")
    print()
    print("   2. Ou criar via shell:")
    print("      python manage.py shell")
    print("      >>> from tds_new.models import CertificadoDevice, Gateway")
    print("      >>> gw = Gateway.objects.first()")
    print("      >>> cert = CertificadoDevice.objects.create(")
    print("      ...     mac_address=gw.mac,")
    print("      ...     serial_number='TEST123456789',")
    print("      ...     certificate_pem='-----BEGIN CERTIFICATE-----\\nTEST\\n-----END CERTIFICATE-----',")
    print("      ...     expires_at='2036-01-01',")
    print("      ...     conta=gw.conta")
    print("      ... )")
    print()
elif gateways.count() == 0:
    print("❌ CAUSA RAIZ: Há certificados mas NÃO há gateways")
    print()
    print("📝 EXPLICAÇÃO:")
    print("   - Certificados existem mas não há gateways para alocar")
    print("   - O botão 'Alocar' aparece mas levaria a erro 404")
    print()
else:
    # Verificar se há match entre certificados e gateways
    match_count = 0
    for cert in certificados:
        if Gateway.objects.filter(mac=cert.mac_address).exists():
            match_count += 1
    
    if match_count == 0:
        print("⚠️ PROBLEMA: Certificados e Gateways com MACs diferentes")
        print()
        print(f"   Certificados MACs: {[c.mac_address for c in certificados]}")
        print(f"   Gateways MACs: {[g.mac for g in gateways]}")
        print()
        print("🔧 SOLUÇÃO:")
        print("   - Alinhar os MACs entre certificados e gateways")
        print("   - Ou criar certificados com MACs dos gateways existentes")
    else:
        print("✅ Certificados e Gateways parecem OK")
        print(f"   {match_count}/{certificados.count()} certificados têm gateway correspondente")
        print()
        print("🔍 VERIFICAÇÕES ADICIONAIS:")
        print()
        print("   1. Acesse URL da lista de certificados:")
        print("      http://localhost:8000/tds_new/admin-sistema/provisionamento/certificados/")
        print()
        print("   2. Verifique se o botão 'Alocar' aparece na coluna 'Ações'")
        print()
        print("   3. Se o botão NÃO aparece, verifique:")
        print("      - Console do navegador (F12) para erros JavaScript")
        print("      - Template: templates/admin_sistema/provisionamento/certificados_list.html")
        print("      - View: tds_new/views/admin/provisionamento.py (método get_context_data)")
        print()
        print("   4. Se o botão aparece mas não funciona:")
        print("      - Verifique URL gerada (hover sobre o botão)")
        print("      - Deve ser: /tds_new/admin-sistema/provisionamento/alocar/{gateway_id}/")
        print()

print("=" * 80)
