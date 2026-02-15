"""
Script para criar superusuário automaticamente
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Dados do superusuário
USERNAME = "admin"
EMAIL = "admin@tds-new.local"
PASSWORD = "Admin@2026"

# Verificar se já existe
if User.objects.filter(username=USERNAME).exists():
    print(f"⚠️  Usuário '{USERNAME}' já existe!")
    user = User.objects.get(username=USERNAME)
    print(f"   Email: {user.email}")
    print(f"   Superuser: {user.is_superuser}")
    print(f"   Staff: {user.is_staff}")
    print(f"   Ativo: {user.is_active}")
else:
    # Criar superusuário
    user = User.objects.create_superuser(
        username=USERNAME,
        email=EMAIL,
        password=PASSWORD
    )
    print(f"✅ Superusuário criado com sucesso!")
    print(f"   Username: {USERNAME}")
    print(f"   Email: {EMAIL}")
    print(f"   Password: {PASSWORD}")
    print(f"\n⚠️  IMPORTANTE: Altere a senha após o primeiro login!")
