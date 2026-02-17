"""
Script de diagnóstico: Verificar dados de teste e sessão do usuário
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from tds_new.models import Gateway, Dispositivo, Conta, CustomUser, ContaMembership

print("=" * 60)
print("DIAGNÓSTICO DE DADOS DE TESTE")
print("=" * 60)

# 1. Verificar contas
print("\n📊 CONTAS NO SISTEMA:")
contas = Conta.objects.all()
for conta in contas:
    print(f"  ID: {conta.id} | Nome: {conta.name} | Ativa: {conta.is_active}")

# 2. Verificar usuários e memberships
print("\n👤 USUÁRIOS E VÍNCULOS:")
usuarios = CustomUser.objects.all()
for user in usuarios:
    print(f"\n  Usuario: {user.username} (ID: {user.id})")
    memberships = ContaMembership.objects.filter(user=user)
    for m in memberships:
        print(f"    → Conta: {m.conta.name} (ID: {m.conta.id}) | Role: {m.role} | Ativa: {m.is_active}")

# 3. Verificar gateways por conta
print("\n🌐 GATEWAYS POR CONTA:")
for conta in contas:
    gateways = Gateway.objects.filter(conta=conta)
    print(f"\n  Conta: {conta.name} (ID: {conta.id}) - {gateways.count()} gateways")
    for gw in gateways:
        print(f"    • {gw.codigo} | {gw.nome} | MAC: {gw.mac}")

# 4. Verificar dispositivos por conta (via gateway)
print("\n📱 DISPOSITIVOS POR CONTA:")
for conta in contas:
    dispositivos = Dispositivo.objects.filter(gateway__conta=conta)
    print(f"\n  Conta: {conta.name} (ID: {conta.id}) - {dispositivos.count()} dispositivos")
    for disp in dispositivos:
        print(f"    • {disp.codigo} | {disp.nome} | Gateway: {disp.gateway.codigo} | Tipo: {disp.tipo}")

# 5. Verificar dados SEM filtro de conta (total no banco)
print("\n" + "=" * 60)
print("TOTAIS NO BANCO (SEM FILTRO):")
print(f"  Total Contas: {Conta.objects.count()}")
print(f"  Total Gateways: {Gateway.objects.count()}")
print(f"  Total Dispositivos: {Dispositivo.objects.count()}")
print("=" * 60)

# 6. Verificar qual conta o usuário miltoneo@gmail.com está vendo
print("\n🔍 SIMULAÇÃO DE LOGIN (miltoneo@gmail.com):")
try:
    user = CustomUser.objects.get(username='miltoneo@gmail.com')
    memberships = ContaMembership.objects.filter(user=user, is_active=True)
    print(f"  Usuário: {user.username}")
    print(f"  Memberships ativas: {memberships.count()}")
    
    if memberships.exists():
        primeira_conta = memberships.first().conta
        print(f"  Primeira conta (padrão): {primeira_conta.name} (ID: {primeira_conta.id})")
        
        # Simular o que a view veria
        gateways_visiveis = Gateway.objects.filter(conta=primeira_conta)
        dispositivos_visiveis = Dispositivo.objects.filter(gateway__conta=primeira_conta)
        
        print(f"\n  ✅ O que o usuário DEVERIA VER:")
        print(f"     Gateways: {gateways_visiveis.count()}")
        for gw in gateways_visiveis:
            print(f"       • {gw.codigo} - {gw.nome}")
        
        print(f"     Dispositivos: {dispositivos_visiveis.count()}")
        for disp in dispositivos_visiveis:
            print(f"       • {disp.codigo} - {disp.nome} (Gateway: {disp.gateway.codigo})")
    else:
        print("  ⚠️ PROBLEMA: Usuário não tem contas ativas vinculadas!")
        
except CustomUser.DoesNotExist:
    print("  ❌ Usuário miltoneo@gmail.com não encontrado!")

print("\n" + "=" * 60)
