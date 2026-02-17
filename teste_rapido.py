import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
client = Client()
user = User.objects.filter(is_staff=True).first()
client.force_login(user)

response = client.get('/tds_new/admin-sistema/provisionamento/certificados/', follow=True)
html = response.content.decode('utf-8')

print("=" * 80)
print("VERIFICACAO RAPIDA - Versao do Template")
print("=" * 80)
print(f"Status: {response.status_code}")
print(f"Contem 'DEBUG ATIVO': {'SIM' if 'DEBUG ATIVO' in html else 'NAO'}")
print(f"Contem 'v15:45': {'SIM' if 'v15:45' in html else 'NAO'}")
print(f"Contem 'ALOCAR [v15:45]': {'SIM' if 'ALOCAR [v15:45]' in html else 'NAO'}")
print(f"Contem 'Sem GW': {'SIM' if 'Sem GW' in html else 'NAO'}")

if 'DEBUG ATIVO' in html and 'v15:45' in html:
    print("\n✅ NOVO TEMPLATE CARREGADO!")
else:
    print("\n❌ TEMPLATE ANTIGO AINDA EM CACHE")

print("=" * 80)
