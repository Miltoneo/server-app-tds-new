"""
Debug: Simular o que a DispositivoListView deveria retornar
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from tds_new.models import Dispositivo, Gateway, Conta
from django.db.models import Q

print("=" * 60)
print("DEBUG: DispositivoListView.get_queryset()")
print("=" * 60)

# Simular request.conta_ativa
conta = Conta.objects.first()
print(f"\n📊 Conta ativa: {conta.name} (ID: {conta.id})")

# Simular a queryset da view
print("\n🔍 QUERYSET BASE:")
queryset_base = Dispositivo.objects.filter(
    gateway__conta=conta
).select_related('gateway').order_by('gateway__codigo', 'codigo')

print(f"  SQL: {queryset_base.query}")
print(f"  Count: {queryset_base.count()}")

if queryset_base.count() == 0:
    print("\n❌ PROBLEMA: Nenhum dispositivo retornado!")
    print("\n🔍 VERIFICANDO PASSO A PASSO:")
    
    # 1. Gateways da conta
    gateways = Gateway.objects.filter(conta=conta)
    print(f"\n  1. Gateways da conta {conta.id}: {gateways.count()}")
    for gw in gateways:
        print(f"     • {gw.codigo} (ID: {gw.id})")
    
    # 2. Dispositivos sem filtro
    dispositivos_all = Dispositivo.objects.all()
    print(f"\n  2. Total de dispositivos (SEM filtro): {dispositivos_all.count()}")
    for disp in dispositivos_all:
        print(f"     • {disp.codigo} | Gateway: {disp.gateway.codigo} (conta: {disp.gateway.conta_id})")
    
    # 3. Dispositivos por gateway specific
    for gw in gateways:
        disps_gw = Dispositivo.objects.filter(gateway=gw)
        print(f"\n  3. Dispositivos do gateway {gw.codigo}: {disps_gw.count()}")
        for disp in disps_gw:
            print(f"     • {disp.codigo} - {disp.nome}")
    
    # 4. Join reverso
    dispositivos_via_filter = Dispositivo.objects.filter(gateway__conta=conta)
    print(f"\n  4. Dispositivos via gateway__conta={conta.id}: {dispositivos_via_filter.count()}")
    
    # 5. Verificar se há gateways NULL
    dispositivos_sem_gateway = Dispositivo.objects.filter(gateway__isnull=True)
    print(f"\n  5. Dispositivos SEM gateway: {dispositivos_sem_gateway.count()}")

else:
    print("\n✅ Dispositivos encontrados:")
    for disp in queryset_base:
        print(f"  • {disp.codigo} - {disp.nome} (Gateway: {disp.gateway.codigo})")

# Simular filtros vazios (request.GET vazio)
print("\n" + "=" * 60)
print("SIMULANDO FILTROS VAZIOS (request.GET = {})")
print("=" * 60)

from tds_new.forms.dispositivo import DispositivoFilterForm

form = DispositivoFilterForm({}, conta=conta)
print(f"\nForm válido: {form.is_valid()}")

if form.is_valid():
    print("Filtros aplicados:")
    for field, value in form.cleaned_data.items():
        print(f"  {field}: {value}")
else:
    print(f"❌ Form inválido: {form.errors}")

print("\n" + "=" * 60)
