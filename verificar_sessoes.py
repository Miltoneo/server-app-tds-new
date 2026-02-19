"""
Verificar estado da sessão após login
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.utils import timezone
from tds_new.models import CustomUser

print("=" * 80)
print("DEBUG: Sessões Ativas")
print("=" * 80)

# Listar sessões ativas
sessoes_ativas = Session.objects.filter(expire_date__gte=timezone.now())

print(f"\n[INFO] Total de sessões ativas: {sessoes_ativas.count()}")

for sessao in sessoes_ativas:
    data = sessao.get_decoded()
    user_id = data.get('_auth_user_id')
    conta_id = data.get('conta_id')
    conta_nome = data.get('conta_nome', 'Não definido')
    
    user = None
    if user_id:
        try:
            user = CustomUser.objects.get(id=user_id)
        except:
            pass
    
    print(f"\n[SESSÃO] {sessao.session_key[:10]}...")
    print(f"  User ID: {user_id} ({user.email if user else 'Desconhecido'})")
    print(f"  Conta ID: {conta_id}")
    print(f"  Conta Nome: {conta_nome}")
    print(f"  Expira: {sessao.expire_date}")
    print(f"  Dados completos: {list(data.keys())}")

print("\n" + "=" * 80)
print("\nPASSOS PARA CORRIGIR:")
print("1. Acesse: http://localhost:8000/tds_new/auth/select-account/")
print("2. Selecione a conta: 'Conta Teste Telemetria'")
print("3. Volte para: http://localhost:8000/tds_new/telemetria/")
print("=" * 80)
