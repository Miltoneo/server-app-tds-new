"""
Script para corrigir sessão do usuário: adicionar conta_ativa_id
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.utils import timezone
from tds_new.models import CustomUser, ContaMembership
import base64
import pickle

print("=" * 60)
print("CORRIGINDO SESSÃO DO USUÁRIO")
print("=" * 60)

# Buscar usuário
user = CustomUser.objects.get(username='miltoneo@gmail.com')
print(f"\n👤 Usuário: {user.username} (ID: {user.id})")

# Buscar conta do usuário
membership = ContaMembership.objects.filter(user=user, is_active=True).first()
if not membership:
    print("❌ Usuário não tem conta ativa!")
    exit(1)

conta = membership.conta
print(f"📊 Conta: {conta.name} (ID: {conta.id})")

# Buscar sessões ativas do usuário
sessoes_ativas = Session.objects.filter(expire_date__gte=timezone.now())
print(f"\n🔍 Total de sessões ativas no sistema: {sessoes_ativas.count()}")

usuario_sessions = []
for session in sessoes_ativas:
    try:
        data = session.get_decoded()
        user_id = data.get('_auth_user_id')
        if user_id and int(user_id) == user.id:
            usuario_sessions.append(session)
            print(f"\n✅ Sessão do usuário encontrada:")
            print(f"  Session key: {session.session_key[:20]}...")
            print(f"  Expira em: {session.expire_date}")
            print(f"  Dados atuais:")
            
            # Mostrar dados relevantes
            for key in ['_auth_user_id', 'conta_ativa_id', 'conta', 'cenario_nome', 'menu_nome']:
                value = data.get(key)
                if value:
                    print(f"    {key}: {value}")
            
            # Verifica se precisa adicionar conta_ativa_id
            if 'conta_ativa_id' not in data:
                print(f"\n  ⚠️ Falta 'conta_ativa_id' na sessão!")
                print(f"  ➕ Adicionando conta_ativa_id={conta.id}...")
                
                # Adicionar conta_ativa_id
                data['conta_ativa_id'] = conta.id
                
                # Salvar sessão atualizada
                session.session_data = session.encode(data)
                session.save()
                
                print(f"  ✅ Sessão atualizada com sucesso!")
            else:
                print(f"  ✓ conta_ativa_id já existe: {data['conta_ativa_id']}")
    except Exception as e:
        # Sessão inválida ou não decodificável
        pass

if not usuario_sessions:
    print("\n⚠️ Nenhuma sessão ativa encontrada para este usuário.")
    print("   Possíveis causas:")
    print("   1. Usuário não está logado")
    print("   2. Sessão expirou")
    print("   3. Cache de sessão foi limpo")
    print("\n   💡 Solução: Faça logout e login novamente")

print("\n" + "=" * 60)
