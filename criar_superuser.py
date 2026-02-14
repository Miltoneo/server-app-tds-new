"""
Script para criar superusuário do TDS New de forma automatizada
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

email = 'admin@tds.com'
password = 'admin123'

if User.objects.filter(email=email).exists():
    print(f'✅ Superusuário {email} já existe')
else:
    user = User.objects.create_superuser(
        email=email,
        password=password
    )
    print(f'✅ Superusuário criado com sucesso!')
    print(f'   Email: {email}')
    print(f'   Senha: {password}')
