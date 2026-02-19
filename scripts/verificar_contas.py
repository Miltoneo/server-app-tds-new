#!/usr/bin/env python3
"""
Verificação completa de contas e memberships
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.contrib.auth import get_user_model
from tds_new.models.base import Conta, ContaMembership

User = get_user_model()

print("=" * 80)
print("VERIFICAÇÃO COMPLETA - CONTAS E MEMBERSHIPS")
print("=" * 80)
print()

# Contas
contas = Conta.objects.all()
print(f"📊 Total de Contas: {contas.count()}")
print()

for conta in contas:
    print(f"Conta: {conta.name}")
    print(f"  ID: {conta.id}")
    print(f"  CNPJ: {conta.cnpj or 'N/A'}")
    print(f"  Ativa: {conta.is_active}")
    print(f"  Membros: {conta.get_total_members()}")
    print(f"  Admins: {conta.get_admins().count()}")
    print()

# Usuários
users = User.objects.all()
print(f"👥 Total de Usuários: {users.count()}")
print()

for user in users:
    memberships = user.conta_memberships.filter(is_active=True)
    print(f"Usuário: {user.email}")
    print(f"  Username: {user.username}")
    print(f"  Superuser: {user.is_superuser}")
    print(f"  Staff: {user.is_staff}")
    print(f"  Ativo: {user.is_active}")
    print(f"  Contas vinculadas: {memberships.count()}")
    
    for membership in memberships:
        print(f"    → {membership.conta.name} (Role: {membership.role})")
    print()

# Memberships
memberships = ContaMembership.objects.all()
print(f"🔗 Total de Memberships: {memberships.count()}")
print()

for m in memberships:
    print(f"  {m.user.email:30} → {m.conta.name:25} | {m.role:10} | Ativo: {m.is_active}")

print()
print("=" * 80)
print("✓ Verificação concluída!")
print("=" * 80)
