#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
users = User.objects.all()

print("=" * 70)
print(f"Total de usuários: {users.count()}")
print("=" * 70)
for u in users:
    print(f"  - {u.username:30} | {u.email:30} | super={u.is_superuser}")
print("=" * 70)
