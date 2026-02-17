"""
Teste da view de lista de certificados
Verifica se os certificados estão sendo renderizados corretamente
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from tds_new.views.admin.provisionamento import CertificadosListView
from tds_new.models import CertificadoDevice, Gateway

User = get_user_model()

def testar_lista_certificados():
    print("=" * 80)
    print("🧪 TESTE: LISTA DE CERTIFICADOS")
    print("=" * 80)
    
    # Criar request factory
    factory = RequestFactory()
    request = factory.get('/tds_new/admin-sistema/provisionamento/certificados/')
    
    # Criar usuário staff para simular acesso
    user = User.objects.filter(is_staff=True).first()
    if not user:
        print("❌ ERRO: Nenhum usuário staff encontrado")
        print("   Crie um superuser com: python manage.py createsuperuser")
        return
    
    request.user = user
    print(f"\n✅ Usuário de teste: {user.email} (staff={user.is_staff})")
    
    # Instanciar view
    view = CertificadosListView()
    view.request = request
    view.kwargs = {}
    
    # Testar acesso
    print(f"\n🔐 Teste de acesso (test_func): {view.test_func()}")
    
    # Obter queryset
    queryset = view.get_queryset()
    print(f"\n📊 Total de certificados no queryset: {queryset.count()}")
    
    # Listar certificados
    for i, cert in enumerate(queryset[:10], 1):
        print(f"\nCertificado #{i}")
        print(f"  MAC: {cert.mac_address}")
        print(f"  Serial: {cert.serial_number}")
        print(f"  Conta: {cert.conta.name if cert.conta else 'Sem conta'}")
        print(f"  Criado em: {cert.created_at}")
        print(f"  Expira em: {cert.expires_at}")
        print(f"  Revogado: {cert.is_revoked}")
    
    # Obter contexto
    view.object_list = queryset
    context = view.get_context_data()
    
    print(f"\n📋 Context keys: {list(context.keys())}")
    print(f"   - certificados: {len(context.get('certificados', []))} itens")
    print(f"   - titulo_pagina: {context.get('titulo_pagina')}")
    print(f"   - total_validos: {context.get('total_validos')}")
    print(f"   - total_expirados: {context.get('total_expirados')}")
    print(f"   - total_revogados: {context.get('total_revogados')}")
    
    # Verificar se gateways foram adicionados aos certificados
    certificados_list = context.get('certificados', [])
    if certificados_list:
        print(f"\n🔍 Verificando atributo 'gateway' nos certificados:")
        for i, cert in enumerate(list(certificados_list)[:3], 1):
            has_gateway_attr = hasattr(cert, 'gateway')
            gateway = getattr(cert, 'gateway', None)
            print(f"  Certificado #{i} - hasattr('gateway'): {has_gateway_attr}")
            if has_gateway_attr:
                print(f"    → Gateway: {gateway.codigo if gateway else 'None'}")
    
    print("\n" + "=" * 80)
    print("✅ Teste concluído")
    print("=" * 80)
    
    # Verificar gateways no banco
    print(f"\n🔧 DEBUG: Gateways no banco de dados")
    gateways = Gateway.objects.all()
    print(f"   Total: {gateways.count()}")
    for gw in gateways:
        print(f"   - {gw.mac} → {gw.codigo} ({gw.nome})")

if __name__ == '__main__':
    testar_lista_certificados()
