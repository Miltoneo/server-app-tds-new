#!/usr/bin/env python3
"""
Script para criar Conta e vincular usuários via ContaMembership
Sistema multi-tenant TDS New
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.contrib.auth import get_user_model
from tds_new.models.base import Conta, ContaMembership

User = get_user_model()

print("=" * 70)
print("SETUP DE CONTA E MEMBERSHIPS - TDS NEW")
print("=" * 70)
print()

# 1. Criar ou obter conta padrão
conta_name = "Organização Principal"
conta, conta_created = Conta.objects.get_or_create(
    name=conta_name,
    defaults={
        'cnpj': '',
        'is_active': True
    }
)

if conta_created:
    print(f"✓ Conta '{conta_name}' criada com sucesso")
else:
    print(f"ℹ Conta '{conta_name}' já existe (ID: {conta.id})")
print()

# 2. Listar todos os usuários
users = User.objects.all()
print(f"Total de usuários no sistema: {users.count()}")
print()

# 3. Criar memberships para cada usuário
memberships_criados = 0
memberships_existentes = 0

for user in users:
    membership, created = ContaMembership.objects.get_or_create(
        conta=conta,
        user=user,
        defaults={
            'role': 'admin',  # Todos como admin inicialmente
            'is_active': True
        }
    )
    
    if created:
        print(f"✓ Membership criado:")
        print(f"  Usuário: {user.username} ({user.email})")
        print(f"  Conta: {conta.name}")
        print(f"  Role: {membership.role}")
        print(f"  Ativo: {membership.is_active}")
        print()
        memberships_criados += 1
    else:
        # Atualizar se já existe mas estava inativo
        if not membership.is_active:
            membership.is_active = True
            membership.save()
            print(f"✓ Membership REATIVADO: {user.email}")
            print()
            memberships_criados += 1
        else:
            memberships_existentes += 1

print("=" * 70)
print("RESUMO:")
print("=" * 70)
print(f"Conta: {conta.name} (ID: {conta.id})")
print(f"Memberships criados/reativados: {memberships_criados}")
print(f"Memberships já existentes: {memberships_existentes}")
print(f"Total de membros na conta: {conta.get_total_members()}")
print()

# 4. Listar todos os memberships
print("=" * 70)
print("MEMBERSHIPS ATIVOS:")
print("=" * 70)
for membership in ContaMembership.objects.filter(conta=conta, is_active=True):
    print(f"  - {membership.user.email:30} | {membership.role:10} | Ativo: {membership.is_active}")

print()
print("✓ Setup concluído!")
