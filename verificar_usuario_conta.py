"""
Script para verificar conta do usuário e leituras de telemetria
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from tds_new.models import CustomUser, Conta, ContaMembership, LeituraDispositivo, Gateway, Dispositivo

print("=" * 80)
print("DIAGNÓSTICO: Usuário vs Leituras de Telemetria")
print("=" * 80)

# 1. Verificar usuário
usuario = CustomUser.objects.filter(email='miltoneo@gmail.com').first()
if not usuario:
    print("[ERRO] Usuário miltoneo@gmail.com não encontrado!")
    sys.exit(1)

print(f"\n[✓] Usuário: {usuario.email}")
print(f"    - Nome: {usuario.first_name} {usuario.last_name}")
print(f"    - ID: {usuario.id}")
print(f"    - Superuser: {usuario.is_superuser}")

# 2. Verificar memberships (contas do usuário)
memberships = ContaMembership.objects.filter(user=usuario).select_related('conta')
print(f"\n[INFO] Contas vinculadas ao usuário: {memberships.count()}")
for membership in memberships:
    print(f"    - {membership.conta.name} (ID: {membership.conta.id}, Papel: {membership.role})")

# 3. Verificar conta das leituras
leituras = LeituraDispositivo.objects.select_related(
    'dispositivo__gateway__conta'
).all()

if leituras.exists():
    primeira_leitura = leituras.first()
    conta_leituras = primeira_leitura.dispositivo.gateway.conta
    
    print(f"\n[INFO] Leituras de telemetria existentes: {leituras.count()}")
    print(f"    - Conta: {conta_leituras.name} (ID: {conta_leituras.id})")
    
    # Verificar se o usuário tem acesso a esta conta
    tem_acesso = memberships.filter(conta_id=conta_leituras.id).exists()
    
    if tem_acesso:
        print(f"\n[✓] USUÁRIO TEM ACESSO à conta das leituras!")
    else:
        print(f"\n[✗] PROBLEMA: Usuário NÃO tem acesso à conta das leituras!")
        print(f"\nSOLUÇÃO: Vincular usuário à conta ou criar dados na conta correta")
        
        # Opção 1: Vincular à conta existente
        print(f"\nOpção 1 - Vincular usuário à conta '{conta_leituras.name}':")
        print(f"  ContaMembership.objects.create(")
        print(f"      user=CustomUser.objects.get(email='miltoneo@gmail.com'),")
        print(f"      conta=Conta.objects.get(id={conta_leituras.id}),")
        print(f"      role='admin'")
        print(f"  )")
        
        # Opção 2: Criar dados na conta do usuário
        if memberships.exists():
            conta_usuario = memberships.first().conta
            print(f"\nOpção 2 - Criar dados de teste na conta '{conta_usuario.name}' (ID: {conta_usuario.id})")
    
    # Listar dispositivos e gateway
    print(f"\n[INFO] Dispositivos e Gateways:")
    gateways = Gateway.objects.filter(conta=conta_leituras)
    for gateway in gateways:
        print(f"    - Gateway: {gateway.codigo} ({gateway.mac_address})")
        dispositivos = Dispositivo.objects.filter(gateway=gateway)
        for disp in dispositivos:
            print(f"      └─ {disp.codigo}: {disp.nome} ({disp.tipo_dispositivo})")
else:
    print(f"\n[INFO] Nenhuma leitura de telemetria encontrada no banco")

# 4. Resumo de todas as contas
print(f"\n[INFO] Todas as contas no sistema:")
todas_contas = Conta.objects.all()
for conta in todas_contas:
    membros = ContaMembership.objects.filter(conta=conta).count()
    gws = Gateway.objects.filter(conta=conta).count()
    print(f"    - {conta.name} (ID: {conta.id})")
    print(f"      └─ Membros: {membros}, Gateways: {gws}")

print("\n" + "=" * 80)
