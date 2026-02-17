"""
Debug: Testar DispositivoListView manualmente
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from tds_new.models import CustomUser, Conta
from tds_new.views.dispositivo import DispositivoListView

print("=" * 60)
print("TESTANDO DispositivoListView COM MIDDLEWARE")
print("=" * 60)

# Criar request factory
factory = RequestFactory()

# Criar request GET simulado
request = factory.get('/tds_new/dispositivos/')

# Autenticar usuário
user = CustomUser.objects.get(username='miltoneo@gmail.com')
request.user = user

# Simular middleware: adicionar conta_ativa ao request
conta = Conta.objects.first()
request.conta_ativa = conta

print(f"\n✅ Request configurado:")
print(f"  User: {request.user.username}")
print(f"  Conta ativa: {request.conta_ativa.name} (ID: {request.conta_ativa.id})")

# Criar view
view = DispositivoListView()
view.request = request
view.kwargs = {}

print("\n📊 Executando get_queryset()...")
queryset = view.get_queryset()
print(f"  Queryset count: {queryset.count()}")

if queryset.count() > 0:
    print("  ✅ Dispositivos retornados:")
    for disp in queryset:
        print(f"    • {disp.codigo} - {disp.nome}")
else:
    print("  ❌ NENHUM dispositivo retornado!")
    
    # Verificar se request.conta_ativa está definido
    if hasattr(view.request, 'conta_ativa'):
        print(f"\n  ✓ request.conta_ativa existe: {view.request.conta_ativa}")
    else:
        print("\n  ✗ request.conta_ativa NÃO está definido!")

print("\n📄 Executando get_context_data()...")
try:
    # Simular page_obj
    from django.core.paginator import Paginator
    paginator = Paginator(queryset, 20)
    page_obj = paginator.page(1)
    
    view.object_list = queryset
    context = view.get_context_data(object_list=queryset, page_obj=page_obj)
    
    print(f"  ✅ Context gerado com sucesso")
    print(f"  dispositivos: {len(context.get('dispositivos', []))} items")
    print(f"  total_dispositivos: {context.get('total_dispositivos')}")
    print(f"  dispositivos_ativos: {context.get('dispositivos_ativos')}")
    print(f"  titulo_pagina: {context.get('titulo_pagina')}")
    
    if 'dispositivos' in context:
        dispositivos_list = context['dispositivos']
        print(f"\n  📋 Dispositivos no contexto:")
        for disp in dispositivos_list:
            print(f"    • {disp.codigo} - {disp.nome}")
    
except Exception as e:
    print(f"  ❌ ERRO ao gerar contexto: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
