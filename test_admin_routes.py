"""
Script de validação das rotas administrativas - Week 8
Testa se as rotas administrativas foram criadas corretamente

Uso:
    python test_admin_routes.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')

# Evitar que o Django tente reconhecer argumentos de linha de comando
sys.argv = [sys.argv[0]]

django.setup()

from django.urls import reverse, resolve
from django.test import RequestFactory
from django.contrib.auth import get_user_model

User = get_user_model()


def test_admin_urls():
    """Testa se as URLs administrativas estão configuradas corretamente"""
    print("=" * 80)
    print("TESTE DE ROTAS ADMINISTRATIVAS - WEEK 8")
    print("=" * 80)
    
    urls_to_test = [
        ('admin_dashboard', 'Dashboard Global'),
        ('admin_certificados_list', 'Lista de Certificados'),
    ]
    
    print("\n1. TESTANDO RESOLUÇÃO DE URLS:")
    print("-" * 80)
    
    for url_name, description in urls_to_test:
        try:
            url = reverse(f'tds_new:{url_name}')
            resolved = resolve(url)
            print(f"✅ {description}")
            print(f"   URL: {url}")
            print(f"   View: {resolved.func.__module__}.{resolved.func.__name__}")
        except Exception as e:
            print(f"❌ {description}")
            print(f"   Erro: {str(e)}")
        print()


def test_templates_exist():
    """Verifica se os templates foram criados"""
    print("\n2. TESTANDO EXISTÊNCIA DE TEMPLATES:")
    print("-" * 80)
    
    from django.conf import settings
    import os
    
    templates_to_check = [
        'admin_sistema/base_admin.html',
        'admin_sistema/dashboard.html',
        'admin_sistema/provisionamento/certificados_list.html',
    ]
    
    # Procurar templates
    for app_dir in settings.INSTALLED_APPS:
        if 'tds_new' in app_dir:
            template_base = os.path.join(
                settings.BASE_DIR, 
                'tds_new', 
                'templates'
            )
            break
    
    for template in templates_to_check:
        template_path = os.path.join(template_base, template)
        if os.path.exists(template_path):
            print(f"✅ {template}")
            print(f"   Path: {template_path}")
        else:
            print(f"❌ {template}")
            print(f"   Path esperado: {template_path}")
        print()


def test_middleware():
    """Verifica se o middleware foi registrado"""
    print("\n3. TESTANDO MIDDLEWARE:")
    print("-" * 80)
    
    from django.conf import settings
    
    middleware_to_check = 'tds_new.middleware.SuperAdminMiddleware'
    
    if middleware_to_check in settings.MIDDLEWARE:
        print(f"✅ SuperAdminMiddleware registrado")
        print(f"   Posição: {settings.MIDDLEWARE.index(middleware_to_check) + 1}")
    else:
        print(f"❌ SuperAdminMiddleware NÃO registrado")
    print()


def test_constants():
    """Verifica se as constantes foram atualizadas"""
    print("\n4. TESTANDO CONSTANTES:")
    print("-" * 80)
    
    from tds_new.constants import Cenarios, Permissoes
    
    # Verificar ADMIN_SISTEMA
    if hasattr(Cenarios, 'ADMIN_SISTEMA'):
        print(f"✅ Cenarios.ADMIN_SISTEMA existe")
        print(f"   Título: {Cenarios.ADMIN_SISTEMA['titulo_pagina']}")
    else:
        print(f"❌ Cenarios.ADMIN_SISTEMA NÃO existe")
    print()
    
    # Verificar SUPER_ADMIN
    if hasattr(Permissoes, 'SUPER_ADMIN'):
        print(f"✅ Permissoes.SUPER_ADMIN existe")
        print(f"   Valor: {Permissoes.SUPER_ADMIN}")
    else:
        print(f"❌ Permissoes.SUPER_ADMIN NÃO existe")
    print()


def test_views_exist():
    """Verifica se as views administrativas foram criadas"""
    print("\n5. TESTANDO VIEWS:")
    print("-" * 80)
    
    try:
        from tds_new.views.admin import dashboard, provisionamento
        print(f"✅ Módulo admin.dashboard importado")
        print(f"   Functions: {dir(dashboard)}")
        print()
        print(f"✅ Módulo admin.provisionamento importado")
        print(f"   Classes: {dir(provisionamento)}")
    except ImportError as e:
        print(f"❌ Erro ao importar views admin")
        print(f"   Erro: {str(e)}")
    print()


def main():
    """Executa todos os testes"""
    test_admin_urls()
    test_templates_exist()
    test_middleware()
    test_constants()
    test_views_exist()
    
    print("\n" + "=" * 80)
    print("TESTES CONCLUÍDOS")
    print("=" * 80)
    print("\nPRÓXIMOS PASSOS:")
    print("1. Criar superuser: python manage.py createsuperuser")
    print("2. Iniciar servidor: python manage.py runserver")
    print("3. Acessar: http://localhost:8000/tds_new/admin-sistema/")
    print("\nVALIDAÇÃO DE SEGURANÇA:")
    print("- Login como usuário comum → tentar acessar /admin-sistema/ → deve bloquear")
    print("- Login como staff/superuser → deve acessar normalmente")
    print()


if __name__ == '__main__':
    main()
