#!/usr/bin/env python3
"""
Script para criar usuários no ambiente de produção do TDS New
Servidor: onkoto.com.br
Database: db_tds_new (porta 5442)
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Definir usuários a serem criados
usuarios = [
    {
        'username': 'admin',
        'email': 'admin@tds-new.local',
        'password': 'admin',  # TROCAR EM PRODUÇÃO!
        'is_superuser': True,
        'is_staff': True,
        'is_active': True,
        'first_name': '',
        'last_name': ''
    },
    {
        'username': 'miltoneo@gmail.com',
        'email': 'miltoneo@gmail.com',
        'password': '*Mil031212',  # Senha padrão
        'is_superuser': True,
        'is_staff': True,
        'is_active': True,
        'first_name': '',
        'last_name': ''
    }
]

print("=" * 70)
print("Criando usuários no ambiente de PRODUÇÃO")
print("Servidor: onkoto.com.br")
print("Database: db_tds_new (porta 5442)")
print("=" * 70)
print()

for user_data in usuarios:
    username = user_data['username']
    
    # Verificar se usuário já existe
    if User.objects.filter(username=username).exists():
        print(f"⚠️  Usuário '{username}' já existe - PULANDO")
        continue
    
    # Criar usuário
    password = user_data.pop('password')
    user = User.objects.create_user(**user_data)
    user.set_password(password)
    user.save()
    
    print(f"✓ Usuário '{username}' criado com sucesso")
    print(f"  Email: {user.email}")
    print(f"  Superuser: {user.is_superuser}")
    print(f"  Staff: {user.is_staff}")
    print(f"  Ativo: {user.is_active}")
    print()

print("=" * 70)
print("Total de usuários no sistema:")
print("=" * 70)
for user in User.objects.all():
    print(f"  - {user.username:30} | {user.email:30} | super={user.is_superuser}")

print()
print("✓ Script concluído!")
