"""
Script para adicionar coluna session_hash na tabela axes_accesslog
Esta coluna é esperada pelo django-axes 6.4.0 mas não foi criada pelas migrations
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

print("\n" + "="*70)
print("ADICIONANDO COLUNA session_hash NA TABELA axes_accesslog")
print("="*70)

try:
    # Verificar se a coluna já existe
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='axes_accesslog' AND column_name='session_hash'
        )
    """)
    exists = cursor.fetchone()[0]
    
    if exists:
        print("⚠️  Coluna session_hash já existe!")
    else:
        # Adicionar a coluna (VARCHAR, NULL permitido)
        cursor.execute("""
            ALTER TABLE axes_accesslog 
            ADD COLUMN session_hash VARCHAR(64) NULL
        """)
        print("✅ Coluna session_hash adicionada com sucesso!")
        
        # Verificar novamente
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name='axes_accesslog' AND column_name='session_hash'
        """)
        result = cursor.fetchone()
        if result:
            print(f"   Nome: {result[0]}")
            print(f"   Tipo: {result[1]}")
            print(f"   NULL: {result[2]}")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("Verificando estrutura completa da tabela...")
print("="*70)

cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name='axes_accesslog'
    ORDER BY ordinal_position
""")

for row in cursor.fetchall():
    print(f"  {row[0]:<30} {row[1]}")

print("\n✅ Processo concluído. Tente fazer login novamente.")
