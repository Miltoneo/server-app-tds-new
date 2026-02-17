"""
Teste FINAL - Renderizar template e verificar HTML real
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 80)
print("🔍 TESTE FINAL: VERIFICAÇÃO DE TEMPLATE")
print("=" * 80)

client = Client()
user = User.objects.filter(is_staff=True).first()

if not user:
    print("❌ Nenhum usuário staff encontrado")
    exit(1)

client.force_login(user)

# Testar URL real
url = '/tds_new/admin-sistema/provisionamento/certificados/'
print(f"\n📡 Acessando: {url}")

response = client.get(url, follow=True)
print(f"✅ Status: {response.status_code}")

html = response.content.decode('utf-8')

# Verificações
print("\n🔍 Verificações no HTML renderizado:")
print(f"   - Tamanho do HTML: {len(html)} bytes")
print(f"   - Contém 'VERSÃO ATUALIZADA':{' SIM' if 'VERSÃO ATUALIZADA' in html or 'VERSAO ATUALIZADA' in html else ' NÃO'}")
print(f"   - Contém botão 'Alocar': {'SIM' if 'btn-outline-primary' in html and '>Alocar<' in html or '> Alocar <' in html else 'NÃO'}")
print(f"   - Contém badge 'Sem GW': {'SIM' if 'Sem GW' in html else 'NÃO'}")

# Extrair trecho da coluna Ações
import re
pattern = r'<td class="text-end">.*?</td>'
matches = re.findall(pattern, html, re.DOTALL)

if matches:
    print(f"\n📋 Primeira coluna 'Ações' encontrada:")
    print("-" * 80)
    primeiro_match = ' '.join(matches[0].split())
    print(primeiro_match[:500])
    print("-" * 80)
else:
    print("\n❌ Nenhuma coluna 'Ações' encontrada!")

# Resultado final
if 'btn-outline-primary' in html and 'Alocar' in html and 'Sem GW' not in html:
    print("\n✅ SUCESSO: Template correto está sendo renderizado!")
elif 'Sem GW' in html:
    print("\n❌ FALHA: Template antigo ainda está em cache")
    print("   AÇÃO: Restart COMPLETO do Windows pode ser necessário")
    print("   ALTERNATIva: Deletar pasta venv e recriar ambiente virtual")
else:
    print(f"\n⚠️  Estado desconhecido")

print("\n" + "=" * 80)
