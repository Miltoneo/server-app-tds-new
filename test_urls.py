"""
Script para testar URLs principais do sistema
"""
import requests
from urllib.parse import urljoin

BASE_URL = "http://127.0.0.1:8000"

def test_url(path, expected_status=200, should_redirect=False):
    """Testa uma URL e retorna resultado"""
    url = urljoin(BASE_URL, path)
    try:
        response = requests.get(url, allow_redirects=not should_redirect, timeout=5)
        status = response.status_code
        
        if should_redirect and status in [301, 302]:
            location = response.headers.get('Location', 'N/A')
            print(f"✅ {path:40} → {status} REDIRECT → {location}")
            return True
        elif status == expected_status:
            print(f"✅ {path:40} → {status} OK")
            return True
        else:
            print(f"❌ {path:40} → {status} (esperado: {expected_status})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {path:40} → ERRO: {e}")
        return False

print("="*80)
print("TESTANDO URLs DO SISTEMA TDS NEW")
print("="*80)
print()

# URLs básicas
print("📋 URLs Básicas:")
test_url("/", expected_status=302, should_redirect=True)  # Redirect para dashboard
test_url("/admin/", expected_status=302, should_redirect=True)  # Redirect para login do admin

print("\n📋 App TDS New - Autenticação:")
test_url("/tds_new/auth/login/", expected_status=200)
test_url("/tds_new/", expected_status=302, should_redirect=True)  # Dashboard (requer login)
test_url("/tds_new/dashboard/", expected_status=302, should_redirect=True)  # Dashboard (requer login)

print("\n📋 Cenários (requerem login):")
test_url("/tds_new/cenario/home/", expected_status=302, should_redirect=True)
test_url("/tds_new/cenario/dispositivos/", expected_status=302, should_redirect=True)
test_url("/tds_new/cenario/telemetria/", expected_status=302, should_redirect=True)

print("\n📋 Gateways (CRUD - requerem login):")
test_url("/tds_new/gateways/", expected_status=302, should_redirect=True)
test_url("/tds_new/gateways/novo/", expected_status=302, should_redirect=True)

print("\n📋 Dispositivos (CRUD - requerem login):")
test_url("/tds_new/dispositivos/", expected_status=302, should_redirect=True)
test_url("/tds_new/dispositivos/novo/", expected_status=302, should_redirect=True)

print("\n" + "="*80)
print("✅ TESTE CONCLUÍDO")
print("="*80)
print("\n📝 Notas:")
print("  - Status 302 (redirect) é esperado para URLs que exigem autenticação")
print("  - /tds_new/auth/login/ deve retornar 200 (página visível)")
print("  - /admin/ redireciona para /admin/login/ (padrão Django)")
print()
print("🔗 URLs de Acesso:")
print(f"  Login: {BASE_URL}/tds_new/auth/login/")
print(f"  Admin: {BASE_URL}/admin/")
print(f"  Dashboard (após login): {BASE_URL}/tds_new/dashboard/")
