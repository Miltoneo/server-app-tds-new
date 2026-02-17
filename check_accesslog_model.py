"""
Script para verificar campos esperados pelo modelo AccessLog do django-axes
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from axes.models import AccessLog

print("\n" + "="*70)
print("CAMPOS DO MODELO AccessLog (django-axes 6.4.0)")
print("="*70)

for field in AccessLog._meta.get_fields():
    field_type = type(field).__name__
    print(f"  {field.name:<30} ({field_type})")

print("\n" + "="*70)
print("Tentando salvar um registro de teste...")
print("="*70)

try:
    log = AccessLog(
        user_agent="Test",
        ip_address="127.0.0.1",
        username="test",
        http_accept="*/*",
        path_info="/test/"
    )
    log.save()
    print("✅ Registro de teste salvo com sucesso!")
    log.delete()
    print("✅ Registro de teste deletado")
except Exception as e:
    print(f"❌ Erro ao salvar: {e}")
    print(f"\nTipo de erro: {type(e).__name__}")
    import traceback
    traceback.print_exc()
