"""
Verifica se Bootstrap e ícones estão sendo carregados
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

def verificar_recursos_estaticos():
    print("=" * 80)
    print("🔍 VERIFICAÇÃO: RECURSOS ESTÁTICOS (CSS/JS/ÍCONES)")
    print("=" * 80)
    
    client = Client()
    user = User.objects.filter(is_staff=True).first()
    client.force_login(user)
    
    url = reverse('tds_new:admin_certificados_list')
    response = client.get(url, follow=True)
    
    html = response.content.decode('utf-8')
    
    # Verificar recursos estáticos
    checks = {
        'Bootstrap CSS': 'bootstrap' in html.lower() and '.css' in html,
        'Bootstrap Icons': 'bootstrap-icons' in html or 'bi-' in html,
        'jQuery ou JavaScript': 'jquery' in html.lower() or 'script' in html.lower(),
    }
    
    print("\n📦 Recursos estáticos:")
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}")
    
    # Procurar links de CSS
    import re
    css_links = re.findall(r'<link[^>]*href="([^"]*\.css[^"]*)"', html)
    print(f"\n📄 Arquivos CSS encontrados ({len(css_links)}):")
    for css in css_links[:5]:
        print(f"   - {css}")
    
    # Procurar se há style inline que pode estar ocultando
    if 'display: none' in html or 'visibility: hidden' in html:
        print("\n⚠️  AVISO: Encontrado CSS inline que pode estar ocultando elementos!")
        # Extrair contexto
        for pattern in ['display: none', 'visibility: hidden']:
            matches = re.findall(f'.{{50}}{pattern}.{{50}}', html)
            if matches:
                print(f"\n   Contexto de '{pattern}':")
                for match in matches[:2]:
                    print(f"   >>> {match}")
    
    # Verificar se há erros de template
    if '{% ' in html or '{{ ' in html:
        print("\n❌ ERRO: Tags Django não processadas no HTML!")
        print("   O template não está sendo renderizado corretamente.")
    
    # Salvar HTML completo
    with open('debug_full_page.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n💾 HTML completo salvo em: debug_full_page.html")
    
    # Extrar só a coluna de Ações
    print("\n📋 EXTRATO: Coluna 'Ações' (primeira linha):")
    print("-" * 80)
    pattern = r'<td class="text-end">.*?</td>'
    matches = re.findall(pattern, html, re.DOTALL)
    if matches:
        for i, match in enumerate(matches[:2], 1):
            print(f"\nLinha #{i}:")
            # Limpar e formatar
            cleaned = ' '.join(match.split())
            print(cleaned)
    
    print("\n" + "=" * 80)
    
    # Teste final: verificar se o botão está visível no HTML
    if 'btn btn-sm btn-outline-primary' in html and 'Alocar' in html:
        print("✅ BOTÃO PRESENTE NO HTML")
        print("   Se não aparece no navegador, verifique:")
        print("   1. Console do navegador (F12) para erros de CSS/JS")
        print("   2. Aba Network (F12) se os arquivos .css estão carregando (200 OK)")
        print("   3. Inspecione o elemento (clique direito > Inspecionar)")
    else:
        print("❌ BOTÃO NÃO ENCONTRADO NO HTML")

if __name__ == '__main__':
    verificar_recursos_estaticos()
