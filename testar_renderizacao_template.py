"""
Teste de renderização do template de lista de certificados
Verifica se o HTML está sendo gerado com o botão 'Alocar'
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

def testar_renderizacao_template():
    print("=" * 80)
    print("🧪 TESTE: RENDERIZAÇÃO DO TEMPLATE")
    print("=" * 80)
    
    # Criar cliente de teste
    client = Client()
    
    # Obter usuário staff
    user = User.objects.filter(is_staff=True).first()
    if not user:
        print("❌ ERRO: Nenhum usuário staff encontrado")
        return
    
    print(f"\n✅ Usuário de teste: {user.email} (staff={user.is_staff})")
    
    # Fazer login
    client.force_login(user)
    print("✅ Login realizado")
    
    # Obter URL
    url = reverse('tds_new:admin_certificados_list')
    print(f"\n🔗 URL: {url}")
    
    # Fazer requisição
    response = client.get(url, follow=True)  # Seguir redirects
    print(f"📡 Status code final: {response.status_code}")
    
    # Mostrar chain de redirects
    if response.redirect_chain:
        print(f"🔄 Redirects:")
        for redirect_url, status_code in response.redirect_chain:
            print(f"   {status_code} → {redirect_url}")
    
    if response.status_code != 200:
        print(f"❌ ERRO: Esperado 200, recebido {response.status_code}")
        # Mostrar conteúdo da resposta para debug
        print(f"\n📄 Conteúdo da resposta:")
        print(response.content.decode('utf-8')[:500])
        return
    
    # Verificar conteúdo HTML
    html = response.content.decode('utf-8')
    
    print(f"\n📄 Tamanho do HTML: {len(html)} bytes")
    
    # Procurar elementos importantes
    checks = {
        'Título da página': 'Certificados do Sistema - Visão Global' in html,
        'Table element': '<table' in html,
        'Botão Alocar (texto)': 'Alocar' in html,
        'Botão Alocar (ícone)': 'bi-arrow-left-right' in html,
        'URL de alocação': 'admin_alocar_gateway_por_certificado' in html or 'provisionamento/certificado' in html,
        'Bootstrap CSS': 'bootstrap' in html.lower(),
        'MAC address aa:bb:cc:dd:ee:01': 'aa:bb:cc:dd:ee:01' in html,
        'MAC address aa:bb:cc:dd:ee:02': 'aa:bb:cc:dd:ee:02' in html,
    }
    
    print("\n🔍 Verificações no HTML:")
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check_name}")
    
    # Contar botões "Alocar"
    alocar_count = html.count('Alocar')
    print(f"\n📊 Ocorrências de 'Alocar' no HTML: {alocar_count}")
    
    # Extrair trecho com botão Alocar
    if 'Alocar' in html:
        print("\n📝 Trechos encontrados com 'Alocar':")
        import re
        pattern = r'.{100}Alocar.{100}'
        matches = re.findall(pattern, html, re.DOTALL)
        for i, match in enumerate(matches[:3], 1):
            clean_match = ' '.join(match.split())
            print(f"\n   Trecho #{i}:")
            print(f"   {clean_match[:200]}...")
    
    # Procurar por erros ou warnings
    if 'Nenhum certificado encontrado' in html:
        print("\n⚠️  AVISO: Template mostra mensagem 'Nenhum certificado encontrado'")
        print("   Verificar se o loop {% for cert in certificados %} está correto")
    
    # Verificar script de paginação
    page_info = f"Página 1 de" in html if alocar_count > 0 else False
    print(f"\n📄 Paginação encontrada: {'✅' if page_info else '❌'}")
    
    # Salvar HTML para inspeção
    output_file = 'teste_certificados_list.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n💾 HTML salvo em: {output_file}")
    print("   Abra este arquivo no navegador para inspecionar visualmente")
    
    print("\n" + "=" * 80)
    print("✅ Teste concluído")
    print("=" * 80)

if __name__ == '__main__':
    testar_renderizacao_template()
