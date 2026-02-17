"""
Debug: Verificar se ContaMembership do usuário está correto
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from tds_new.models import CustomUser, Conta, ContaMembership

print("=" * 60)
print("VERIFICANDO CONTAM EMBERSHIP")
print("=" * 60)

# Buscar usuário
user = CustomUser.objects.get(username='miltoneo@gmail.com')
print(f"\n👤 Usuário: {user.username} (ID: {user.id})")

# Buscar conta_ativa_id da sessão (simulado)
conta_id = 1
print(f"📊 conta_ativa_id da sessão: {conta_id}")

# Simular o que o middleware faz
try:
    conta = Conta.objects.get(id=conta_id)
    print(f"  ✅ Conta encontrada: {conta.name} (ID: {conta.id})")
    
    usuario_conta = ContaMembership.objects.get(
        user=user,
        conta=conta,
        is_active=True
    )
    print(f"  ✅ ContaMembership encontrado:")
    print(f"     ID: {usuario_conta.id}")
    print(f"     Role: {usuario_conta.role}")
    print(f"     Is Active: {usuario_conta.is_active}")
    
    print("\n✅ MIDDLEWARE DEVERIA FUNCIONAR!")
    
except Conta.DoesNotExist:
    print(f"  ❌ Conta ID {conta_id} não existe!")
    
except ContaMembership.DoesNotExist:
    print(f"  ❌ ContaMembership não existe para:")
    print(f"     User: {user.id}")
    print(f"     Conta: {conta.id}")
    print(f"     is_active: True")
    
    # Buscar se existe mas inativo
    membership_inativo = ContaMembership.objects.filter(
        user=user,
        conta=conta
    ).first()
    
    if membership_inativo:
        print(f"\n  ⚠️ Membership existe mas is_active={membership_inativo.is_active}")
    else:
        print(f"\n  ⚠️ Nenhum membership encontrado (nem inativo)")

print("\n" + "=" * 60)
