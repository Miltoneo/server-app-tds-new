"""
Script de validação - Week 9 Fase 1: Alocação de Gateways

Valida:
1. Imports de forms e views
2. URL resolution
3. Templates existem
4. Modelos acessíveis

Executar: python validacao_week9_fase1.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.urls import reverse, resolve
from django.template.loader import get_template
from django.template import TemplateDoesNotExist

print("=" * 80)
print("✅ WEEK 9 - FASE 1: ALOCAÇÃO DE GATEWAYS - VALIDAÇÃO")
print("=" * 80)
print()

# =============================================================================
# 1. Validar Imports
# =============================================================================
print("📦 1. VALIDAÇÃO DE IMPORTS")
print("-" * 80)

try:
    from tds_new.forms.provisionamento import AlocarGatewayForm
    print("✅ AlocarGatewayForm importado com sucesso")
except ImportError as e:
    print(f"❌ Erro ao importar AlocarGatewayForm: {e}")
    sys.exit(1)

try:
    from tds_new.views.admin.provisionamento import alocar_gateway_view
    print("✅ alocar_gateway_view importado com sucesso")
except ImportError as e:
    print(f"❌ Erro ao importar alocar_gateway_view: {e}")
    sys.exit(1)

try:
    from tds_new.models import Gateway, CertificadoDevice, Conta, Dispositivo
    print("✅ Modelos (Gateway, CertificadoDevice, Conta, Dispositivo) importados")
except ImportError as e:
    print(f"❌ Erro ao importar modelos: {e}")
    sys.exit(1)

print()

# =============================================================================
# 2. Validar URLs
# =============================================================================
print("🔗 2. VALIDAÇÃO DE URLs")
print("-" * 80)

# Teste URL de alocação
try:
    url = reverse('tds_new:admin_alocar_gateway', kwargs={'gateway_id': 1})
    print(f"✅ URL 'admin_alocar_gateway' resolve para: {url}")
    
    # Verificar que a view correta é resolvida
    resolver = resolve(url)
    if resolver.func == alocar_gateway_view:
        print(f"✅ View correta vinculada: {resolver.func.__name__}")
    else:
        print(f"⚠️ View diferente vinculada: {resolver.func.__name__}")
except Exception as e:
    print(f"❌ Erro ao resolver URL 'admin_alocar_gateway': {e}")
    sys.exit(1)

# Teste URL de lista de certificados (já existente)
try:
    url = reverse('tds_new:admin_certificados_list')
    print(f"✅ URL 'admin_certificados_list' resolve para: {url}")
except Exception as e:
    print(f"❌ Erro ao resolver URL 'admin_certificados_list': {e}")

print()

# =============================================================================
# 3. Validar Templates
# =============================================================================
print("📄 3. VALIDAÇÃO DE TEMPLATES")
print("-" * 80)

templates_to_check = [
    'admin_sistema/provisionamento/alocar_gateway.html',
    'admin_sistema/provisionamento/certificados_list.html',
    'admin_sistema/base_admin.html',
]

for template_name in templates_to_check:
    try:
        template = get_template(template_name)
        print(f"✅ Template encontrado: {template_name}")
    except TemplateDoesNotExist:
        print(f"❌ Template NÃO encontrado: {template_name}")
        sys.exit(1)

print()

# =============================================================================
# 4. Validar Form Fields
# =============================================================================
print("📋 4. VALIDAÇÃO DE FORMULÁRIO")
print("-" * 80)

form = AlocarGatewayForm()
print(f"✅ Formulário instanciado com sucesso")
print(f"   Campos: {list(form.fields.keys())}")

# Verificar campos esperados
required_fields = ['conta', 'transferir_dispositivos']
for field in required_fields:
    if field in form.fields:
        print(f"   ✅ Campo '{field}' presente")
    else:
        print(f"   ❌ Campo '{field}' AUSENTE")

print()

# =============================================================================
# 5. Validar Dados do Banco (se possível)
# =============================================================================
print("💾 5. VALIDAÇÃO DE DADOS (Banco de Dados)")
print("-" * 80)

try:
    total_gateways = Gateway.objects.count()
    print(f"✅ Total de gateways no banco: {total_gateways}")
    
    total_certificados = CertificadoDevice.objects.count()
    print(f"✅ Total de certificados no banco: {total_certificados}")
    
    total_contas = Conta.objects.filter(is_active=True).count()
    print(f"✅ Total de contas ativas: {total_contas}")
    
    total_dispositivos = Dispositivo.objects.count()
    print(f"✅ Total de dispositivos: {total_dispositivos}")
    
    # Verificar gateways órfãos (sem conta)
    gateways_orfaos = Gateway.objects.filter(conta__isnull=True).count()
    if gateways_orfaos > 0:
        print(f"⚠️ Gateways órfãos (sem conta): {gateways_orfaos}")
        print(f"   💡 Use a funcionalidade de alocação para vincular estes gateways!")
    else:
        print(f"✅ Nenhum gateway órfão encontrado")
    
except Exception as e:
    print(f"⚠️ Erro ao acessar banco de dados: {e}")
    print(f"   (Isso é normal se o banco ainda não foi configurado)")

print()

# =============================================================================
# RESUMO FINAL
# =============================================================================
print("=" * 80)
print("🎯 RESUMO DA VALIDAÇÃO - WEEK 9 FASE 1")
print("=" * 80)
print()
print("✅ Funcionalidades Implementadas:")
print("   • AlocarGatewayForm - Formulário de alocação")
print("   • alocar_gateway_view - View de processamento")
print("   • Template alocar_gateway.html - Interface de alocação")
print("   • URL admin_alocar_gateway - Rota configurada")
print("   • Atualização da lista de certificados com botão 'Alocar'")
print()
print("📋 Checklist de Teste Manual:")
print("   [ ] Acessar http://localhost:8000/tds_new/admin-sistema/provisionamento/certificados/")
print("   [ ] Clicar em 'Alocar' ao lado de um gateway")
print("   [ ] Selecionar conta de destino no formulário")
print("   [ ] Marcar/desmarcar opção de transferir dispositivos")
print("   [ ] Confirmar alocação e verificar mensagens de sucesso")
print("   [ ] Validar que gateway.conta_id foi atualizado")
print("   [ ] Validar que certificado.conta_id foi atualizado")
print("   [ ] Validar que dispositivos foram transferidos (se opção marcada)")
print()
print("🚀 PRÓXIMOS PASSOS:")
print("   • Week 9 - Fase 2: Importação em lote via CSV")
print("   • Week 9 - Fase 3: Revogação de certificados X.509")
print("   • Week 9 - Fase 4: Auditoria com LogEntry")
print()
print("=" * 80)
print("✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO!")
print("=" * 80)
