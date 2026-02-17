"""
Script para dropar tabelas do django-axes e recriar
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

print("\n" + "="*70)
print("DROPANDO TABELAS DO DJANGO-AXES")
print("="*70)

tables = [
    'axes_accessfailurelog',
    'axes_accesslog',
    'axes_accessattempt'
]

for table in tables:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        print(f"✅ Tabela {table} dropada com sucesso")
    except Exception as e:
        print(f"❌ Erro ao dropar {table}: {e}")

print("\n✅ Tabelas dropadas. Execute agora: python manage.py migrate axes")
