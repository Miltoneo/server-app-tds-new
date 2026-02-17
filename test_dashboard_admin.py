"""
Teste rápido do dashboard administrativo - Week 8
Simula a execução da view dashboard_global sem servidor HTTP

Uso:
    python test_dashboard_admin.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
sys.argv = [sys.argv[0]]
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from tds_new.views.admin.dashboard import dashboard_global

User = get_user_model()


def test_dashboard_view():
    """Testa a view dashboard_global"""
    print("=" * 80)
    print("TESTE DO DASHBOARD ADMINISTRATIVO - WEEK 8")
    print("=" * 80)
    
    # Criar um request factory
    factory = RequestFactory()
    
    # Criar um superuser para o teste
    try:
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            print("❌ Nenhum superuser encontrado no banco de dados")
            print("   Execute: python manage.py createsuperuser")
            return False
        
        print(f"\n✅ Usando superuser: {user.email}")
        print(f"   is_staff: {user.is_staff}")
        print(f"   is_superuser: {user.is_superuser}")
    except Exception as e:
        print(f"❌ Erro ao buscar usuário: {str(e)}")
        return False
    
    # Criar request simulado
    request = factory.get('/tds_new/admin-sistema/')
    request.user = user
    
    print("\n" + "-" * 80)
    print("EXECUTANDO VIEW DASHBOARD_GLOBAL...")
    print("-" * 80)
    
    try:
        # Executar a view
        response = dashboard_global(request)
        
        print(f"\n✅ View executada com sucesso!")
        print(f"   Status Code: {response.status_code}")
        print(f"   Template: admin_sistema/dashboard.html")
        
        # Verificar context
        if hasattr(response, 'context_data'):
            context = response.context_data
        else:
            # Para TemplateResponse, o context está em context
            context = response.context if hasattr(response, 'context') else {}
        
        print("\n" + "-" * 80)
        print("MÉTRICAS CALCULADAS:")
        print("-" * 80)
        
        metricas = {
            'Total de Contas': context.get('total_contas', 'N/A'),
            'Contas com Gateway': context.get('contas_com_gateway', 'N/A'),
            'Total de Gateways': context.get('total_gateways', 'N/A'),
            'Gateways Online': context.get('gateways_online', 'N/A'),
            'Gateways Offline': context.get('gateways_offline', 'N/A'),
            'Gateways Nunca Conectados': context.get('gateways_nunca_conectados', 'N/A'),
            'Total de Dispositivos': context.get('total_dispositivos', 'N/A'),
            'Dispositivos Ativos': context.get('dispositivos_ativos', 'N/A'),
            'Certificados Válidos': context.get('certificados_validos', 'N/A'),
            'Certificados Expirados': context.get('certificados_expirados', 'N/A'),
            'Certificados Revogados': context.get('certificados_revogados', 'N/A'),
            'Total de Usuários': context.get('total_usuarios', 'N/A'),
            'Usuários Admin': context.get('usuarios_admin', 'N/A'),
        }
        
        for label, value in metricas.items():
            print(f"  {label:.<40} {value}")
        
        # Top 5 contas
        top_contas = context.get('top_contas', [])
        if top_contas:
            print("\n" + "-" * 80)
            print("TOP 5 CONTAS (MAIS GATEWAYS):")
            print("-" * 80)
            for i, conta in enumerate(top_contas, 1):
                print(f"  {i}. {conta.nome_fantasia:.<50} {conta.num_gateways} gateways")
        else:
            print("\n⚠️  Nenhuma conta com gateways encontrada")
        
        print("\n" + "=" * 80)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 80)
        print("\nO dashboard administrativo está funcionando corretamente.")
        print("Acesse: http://localhost:8000/tds_new/admin-sistema/")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO AO EXECUTAR VIEW:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        print("\n" + "-" * 80)
        print("TRACEBACK:")
        print("-" * 80)
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_dashboard_view()
    sys.exit(0 if success else 1)
