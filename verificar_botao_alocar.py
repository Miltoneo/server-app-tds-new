"""
Teste visual do HTML - Extrai apenas a coluna de Ações
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
import re

User = get_user_model()

def verificar_botao_alocar():
    print("=" * 80)
    print("🔍 VERIFICAÇÃO: BOTÃO ALOCAR NA INTERFACE")
    print("=" * 80)
    
    client = Client()
    user = User.objects.filter(is_staff=True).first()
    
    if not user:
        print("❌ Nenhum usuário staff encontrado")
        return
    
    client.force_login(user)
    url = reverse('tds_new:admin_certificados_list')
    response = client.get(url, follow=True)
    
    print(f"\n📡 Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Erro: Status code {response.status_code}")
        return
    
    html = response.content.decode('utf-8')
    
    # Extrair linha completa da tabela com MAC address
    pattern = r'<tr>.*?aa:bb:cc:dd:ee:01.*?</tr>'
    match = re.search(pattern, html, re.DOTALL)
    
    if match:
        row_html = match.group(0)
        print("\n📋 HTML da linha do certificado (aa:bb:cc:dd:ee:01):")
        print("-" * 80)
        # Formatar para melhor visualização
        formatted = row_html.replace('><', '>\n<')
        print(formatted[:2000])
        print("-" * 80)
        
        # Verificações específicas
        checks = {
            'Contém "Alocar"': 'Alocar' in row_html,
            'Contém "bi-arrow-left-right"': 'bi-arrow-left-right' in row_html,
            'Contém URL alocação': 'admin_alocar_gateway_por_certificado' in row_html,
            'Contém "Sem GW"': 'Sem GW' in row_html,
            'Contém btn-outline-primary': 'btn-outline-primary' in row_html,
        }
        
        print("\n🔍 Verificações:")
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"{status} {check}")
        
        # Contar elementos
        alocar_count = row_html.count('Alocar')
        sem_gw_count = row_html.count('Sem GW')
        
        print(f"\n📊 Contadores:")
        print(f"   Botões 'Alocar': {alocar_count}")
        print(f"   Badges 'Sem GW': {sem_gw_count}")
        
        if alocar_count > 0 and sem_gw_count == 0:
            print("\n✅ TEMPLATE CORRETO: Botão Alocar presente, sem badge 'Sem GW'")
        elif alocar_count == 0 and sem_gw_count > 0:
            print("\n❌ TEMPLATE ANTIGO: Badge 'Sem GW' presente, sem botão Alocar")
            print("   → SOLUÇÃO: Limpar cache do navegador (Ctrl+Shift+R) ou reiniciar servidor")
        else:
            print(f"\n⚠️  ESTADO MISTO: Alocar={alocar_count}, Sem GW={sem_gw_count}")
    else:
        print("❌ Não foi possível encontrar linha com MAC aa:bb:cc:dd:ee:01")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    verificar_botao_alocar()
