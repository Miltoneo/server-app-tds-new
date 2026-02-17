"""
Script para verificar estrutura da tabela axes_accesslog
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name='axes_accesslog'
    ORDER BY ordinal_position
""")

print("\n" + "="*70)
print("ESTRUTURA DA TABELA axes_accesslog")
print("="*70)
for row in cursor.fetchall():
    print(f"{row[0]:<30} {row[1]:<20} NULL: {row[2]}")

print("\n" + "="*70)
print("Verificando se coluna session_hash existe...")
print("="*70)

cursor.execute("""
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='axes_accesslog' AND column_name='session_hash'
    )
""")
exists = cursor.fetchone()[0]
print(f"session_hash existe: {exists}")

if not exists:
    print("\n⚠️  PROBLEMA: Coluna session_hash NÃO existe!")
    print("✅ SOLUÇÃO: Aplicar migrate do django-axes ou recriar tabelas")
