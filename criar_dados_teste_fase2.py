#!/usr/bin/env python
"""
Script de preparação para testes da Fase 2 - MQTT Consumer
Cria dados de teste: Gateway + Dispositivos
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from tds_new.models import Conta, Gateway, Dispositivo

User = get_user_model()

def criar_dados_teste():
    """Cria dados de teste para validação do MQTT Consumer"""
    
    print("=" * 80)
    print("CRIANDO DADOS DE TESTE - FASE 2")
    print("=" * 80)
    print()
    
    # 1. Verificar/Criar Superuser
    print("[1/4] Verificando superuser...")
    try:
        user = User.objects.get(username='admin')
        print(f"  ✓ Superuser existe: {user.email}")
    except User.DoesNotExist:
        user = User.objects.create_superuser(
            username='admin',
            email='admin@tds.local',
            password='admin123'
        )
        print(f"  ✓ Superuser criado: {user.email}")
    
    # 2. Verificar/Criar Conta
    print("[2/4] Verificando conta...")
    conta, created = Conta.objects.get_or_create(
        name='Conta Teste Telemetria',
        defaults={
            'is_active': True,
        }
    )
    if created:
        print(f"  ✓ Conta criada: {conta.name}")
    else:
        print(f"  ✓ Conta existe: {conta.name} (ID: {conta.id})")
    
    # 3. Verificar/Criar Gateway
    print("[3/4] Verificando gateway...")
    mac_address = 'aa:bb:cc:dd:ee:ff'
    gateway, created = Gateway.objects.get_or_create(
        mac=mac_address,
        defaults={
            'conta': conta,
            'codigo': 'GW-TEST-001',
            'nome': 'Gateway Teste Fase 2',
            'descricao': 'Gateway de teste para validação do MQTT Consumer',
            'is_online': False
        }
    )
    if created:
        print(f"  ✓ Gateway criado: {gateway.nome}")
        print(f"    MAC: {gateway.mac}")
    else:
        print(f"  ✓ Gateway existe: {gateway.nome}")
        print(f"    MAC: {gateway.mac}")
        print(f"    Status: {'Online' if gateway.is_online else 'Offline'}")
    
    # 4. Verificar/Criar Dispositivos
    print("[4/4] Verificando dispositivos...")
    dispositivos_config = [
        {
            'codigo': 'D01',
            'nome': 'Medidor de Energia',
            'descricao': 'Medidor de consumo elétrico',
            'tipo': 'MEDIDOR',
            'slave_id': 1,
            'register_modbus': 4000
        },
        {
            'codigo': 'D02',
            'nome': 'Medidor de Água',
            'descricao': 'Medidor de consumo de água',
            'tipo': 'MEDIDOR',
            'slave_id': 2,
            'register_modbus': 4000
        },
        {
            'codigo': 'D03',
            'nome': 'Sensor de Temperatura',
            'descricao': 'Sensor de temperatura ambiente',
            'tipo': 'SENSOR',
        }
    ]
    
    dispositivos_criados = []
    for config in dispositivos_config:
        defaults = {
            'conta': conta,
            'nome': config['nome'],
            'descricao': config['descricao'],
            'tipo': config['tipo'],
            'status': 'ATIVO'
        }
        
        # Adicionar campos Modbus se presentes
        if 'slave_id' in config:
            defaults['slave_id'] = config['slave_id']
        if 'register_modbus' in config:
            defaults['register_modbus'] = config['register_modbus']
            
        dispositivo, created = Dispositivo.objects.get_or_create(
            gateway=gateway,
            codigo=config['codigo'],
            defaults=defaults
        )
        if created:
            print(f"  ✓ Dispositivo criado: {dispositivo.codigo} - {dispositivo.nome}")
        else:
            print(f"  ✓ Dispositivo existe: {dispositivo.codigo} - {dispositivo.nome}")
        dispositivos_criados.append(dispositivo)
    
    print()
    print("=" * 80)
    print("DADOS DE TESTE CRIADOS COM SUCESSO!")
    print("=" * 80)
    print()
    print("INFORMAÇÕES PARA TESTE:")
    print(f"  Conta ID: {conta.id}")
    print(f"  Gateway MAC: {gateway.mac}")
    print(f"  Gateway Nome: {gateway.nome}")
    print(f"  Dispositivos: {len(dispositivos_criados)}")
    for disp in dispositivos_criados:
        print(f"    - {disp.codigo}: {disp.nome}")
    print()
    print("MQTT TOPIC:")
    print(f"  tds_new/devices/{gateway.mac}/telemetry")
    print()
    print("=" * 80)
    print()

if __name__ == '__main__':
    try:
        criar_dados_teste()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
