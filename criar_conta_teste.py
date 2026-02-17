"""
Script para criar Conta de teste e vincular usuário miltoneo@gmail.com
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from tds_new.models.base import CustomUser, Conta, ContaMembership

print("\n" + "="*70)
print("CRIANDO CONTA DE TESTE E VINCULANDO USUÁRIO")
print("="*70)

# Buscar o usuário
try:
    user = CustomUser.objects.get(email='miltoneo@gmail.com')
    print(f"\n✅ Usuário encontrado:")
    print(f"   Email: {user.email}")
    print(f"   ID: {user.id}")
    print(f"   Superuser: {user.is_superuser}")
except CustomUser.DoesNotExist:
    print("❌ Usuário miltoneo@gmail.com não encontrado!")
    exit(1)

# Verificar se já existe alguma conta
contas_existentes = Conta.objects.all()
print(f"\n📊 Contas existentes: {contas_existentes.count()}")
for conta in contas_existentes:
    print(f"   - {conta.name} (ID: {conta.id}, Ativa: {conta.is_active})")

# Criar conta de teste se não existir
conta, created = Conta.objects.get_or_create(
    name='Conta Teste - Desenvolvimento',
    defaults={
        'cnpj': None,
        'is_active': True
    }
)

if created:
    print(f"\n✅ Conta criada:")
else:
    print(f"\n✅ Conta já existia:")

print(f"   Nome: {conta.name}")
print(f"   ID: {conta.id}")
print(f"   Ativa: {conta.is_active}")

# Verificar se já existe membership
existing_membership = ContaMembership.objects.filter(
    user=user,
    conta=conta
).first()

if existing_membership:
    print(f"\n⚠️  Membership já existe:")
    print(f"   Role: {existing_membership.role}")
    print(f"   Ativo: {existing_membership.is_active}")
    
    # Atualizar se necessário
    if not existing_membership.is_active or existing_membership.role != 'admin':
        existing_membership.is_active = True
        existing_membership.role = 'admin'
        existing_membership.save()
        print(f"   ✅ Membership atualizado para admin ativo")
else:
    # Criar novo membership como admin
    membership = ContaMembership.objects.create(
        user=user,
        conta=conta,
        role='admin',
        is_active=True
    )
    print(f"\n✅ Membership criado:")
    print(f"   Usuário: {user.email}")
    print(f"   Conta: {conta.name}")
    print(f"   Role: {membership.role}")
    print(f"   Ativo: {membership.is_active}")

# Verificar memberships do usuário
print(f"\n📊 Memberships do usuário {user.email}:")
memberships = ContaMembership.objects.filter(user=user, is_active=True)
for m in memberships:
    print(f"   - {m.conta.name} ({m.role})")

print("\n" + "="*70)
print("✅ PROCESSO CONCLUÍDO!")
print("="*70)
print("\nAgora você pode fazer login com:")
print(f"   Email: {user.email}")
print(f"   Senha: *Mil031212")
print(f"\nVocê terá acesso à conta: {conta.name}")
print("="*70)
