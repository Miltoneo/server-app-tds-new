#!/usr/bin/env python
"""
Setup Conta Telemetria - Script de Provisionamento de Dados de Teste
======================================================================
Responsabilidades:
  1. Cria a conta "Conta Teste Telemetria" (se não existir)
  2. Associa miltoneo@gmail.com à conta com role 'admin'
  3. Cria gateway GW-TESTE-01 com MAC 11:22:33:44:55:66
  4. Cria 3 dispositivos vinculados ao gateway

Executar no servidor:
  cd /var/server-app/apps/prj_tds_new
  venv/bin/python setup_conta_telemetria.py
"""

import os
import sys
import django

# ---------------------------------------------------------------------------
# Django setup
# ---------------------------------------------------------------------------
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from tds_new.models import Conta, ContaMembership, Gateway, Dispositivo

User = get_user_model()

# ---------------------------------------------------------------------------
# Constantes de configuração
# ---------------------------------------------------------------------------
CONTA_NOME         = 'Conta Teste Telemetria'
USUARIO_EMAIL      = 'miltoneo@gmail.com'
GATEWAY_MAC        = '11:22:33:44:55:66'
GATEWAY_CODIGO     = 'GW-TESTE-01'
GATEWAY_NOME       = 'Gateway Teste Telemetria'
GATEWAY_DESCRICAO  = 'Gateway criado para testes de envio de telemetria simulada'

DISPOSITIVOS_CONFIG = [
    {
        'codigo':   'D01',
        'nome':     'Medidor de Energia',
        'descricao': 'Medidor de consumo elétrico (kWh)',
        'tipo':     'MEDIDOR',
        'slave_id': 1,
        'register_modbus': 4000,
    },
    {
        'codigo':   'D02',
        'nome':     'Medidor de Água',
        'descricao': 'Medidor de consumo de água (m³)',
        'tipo':     'MEDIDOR',
        'slave_id': 2,
        'register_modbus': 4000,
    },
    {
        'codigo':   'D03',
        'nome':     'Sensor de Temperatura',
        'descricao': 'Sensor de temperatura ambiente (°C)',
        'tipo':     'SENSOR',
    },
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def secao(titulo):
    print()
    print('─' * 60)
    print(f'  {titulo}')
    print('─' * 60)


def ok(msg):
    print(f'  [✓] {msg}')


def info(msg):
    print(f'  [i] {msg}')


def erro(msg):
    print(f'  [✗] {msg}')


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

def passo_1_conta():
    secao('1/4  CONTA')
    conta, criada = Conta.objects.get_or_create(
        name=CONTA_NOME,
        defaults={'is_active': True},
    )
    if criada:
        ok(f'Conta criada: "{conta.name}"  (ID={conta.id})')
    else:
        ok(f'Conta já existente: "{conta.name}"  (ID={conta.id})')
    return conta


def passo_2_usuario(conta):
    secao('2/4  USUÁRIO + MEMBERSHIP')
    try:
        usuario = User.objects.get(email=USUARIO_EMAIL)
        ok(f'Usuário encontrado: {usuario.email}  (ID={usuario.id})')
    except User.DoesNotExist:
        erro(f'Usuário {USUARIO_EMAIL} NÃO ENCONTRADO no banco.')
        erro('Cadastre o usuário pelo painel administrativo antes de executar este script.')
        sys.exit(1)

    if not usuario.is_active:
        erro(f'Usuário {USUARIO_EMAIL} está inativo. Ative-o antes de prosseguir.')
        sys.exit(1)

    membership, criada = ContaMembership.objects.get_or_create(
        conta=conta,
        user=usuario,
        defaults={'role': 'admin', 'is_active': True},
    )
    if criada:
        ok(f'Membership criado: {usuario.email} → "{conta.name}"  (role=admin)')
    else:
        if membership.role != 'admin':
            membership.role = 'admin'
            membership.save(update_fields=['role'])
            info(f'Role atualizado para "admin": {usuario.email} → "{conta.name}"')
        else:
            ok(f'Membership já existente: {usuario.email} → "{conta.name}"  (role={membership.role})')
    return usuario


def passo_3_gateway(conta, usuario):
    secao('3/4  GATEWAY')
    gateway, criado = Gateway.objects.get_or_create(
        mac=GATEWAY_MAC,
        defaults={
            'conta':        conta,
            'codigo':       GATEWAY_CODIGO,
            'nome':         GATEWAY_NOME,
            'descricao':    GATEWAY_DESCRICAO,
            'is_online':    False,
            'created_by':   usuario,
        },
    )
    if criado:
        ok(f'Gateway criado:')
        info(f'  Código  : {gateway.codigo}')
        info(f'  Nome    : {gateway.nome}')
        info(f'  MAC     : {gateway.mac}')
        info(f'  Conta   : {gateway.conta.name}')
    else:
        ok(f'Gateway já existente: {gateway.codigo}  (MAC={gateway.mac})')
        if gateway.conta_id != conta.id:
            gateway.conta = conta
            gateway.save(update_fields=['conta'])
            info(f'  Conta atualizada para: {conta.name}')
    return gateway


def passo_4_dispositivos(gateway, conta, usuario):
    secao('4/4  DISPOSITIVOS')
    dispositivos = []
    for cfg in DISPOSITIVOS_CONFIG:
        defaults = {
            'conta':     conta,
            'nome':      cfg['nome'],
            'descricao': cfg['descricao'],
            'tipo':      cfg['tipo'],
            'status':    'ATIVO',
            'created_by': usuario,
        }
        if 'slave_id' in cfg:
            defaults['slave_id'] = cfg['slave_id']
        if 'register_modbus' in cfg:
            defaults['register_modbus'] = cfg['register_modbus']

        disp, criado = Dispositivo.objects.get_or_create(
            gateway=gateway,
            codigo=cfg['codigo'],
            defaults=defaults,
        )
        if criado:
            ok(f'Dispositivo criado  : {disp.codigo} — {disp.nome}')
        else:
            ok(f'Dispositivo existente: {disp.codigo} — {disp.nome}')
        dispositivos.append(disp)
    return dispositivos


def resumo(conta, usuario, gateway, dispositivos):
    print()
    print('=' * 60)
    print('  PROVISIONAMENTO CONCLUÍDO')
    print('=' * 60)
    print(f'  Conta ID   : {conta.id}')
    print(f'  Conta Nome : {conta.name}')
    print(f'  Usuário    : {usuario.email}')
    print(f'  Gateway ID : {gateway.id}')
    print(f'  Gateway MAC: {gateway.mac}')
    print(f'  Dispositivos ({len(dispositivos)}):')
    for d in dispositivos:
        print(f'    - {d.codigo}: {d.nome}')
    print()
    print('  MQTT TOPIC PARA TELEMETRIA:')
    print(f'    tds_new/devices/{gateway.mac}/telemetry')
    print()
    print('  PAYLOAD DE EXEMPLO:')
    import json
    from datetime import datetime, timezone
    payload = {
        'gateway_mac': gateway.mac,
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'leituras': [
            {'dispositivo_codigo': 'D01', 'valor': 123.45, 'unidade': 'kWh'},
            {'dispositivo_codigo': 'D02', 'valor': 67.89,  'unidade': 'm³'},
            {'dispositivo_codigo': 'D03', 'valor': 22.5,   'unidade': '°C'},
        ],
    }
    print(f'    {json.dumps(payload, indent=6, ensure_ascii=False)}')
    print('=' * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print()
    print('=' * 60)
    print('  SETUP CONTA TELEMETRIA — TDS NEW')
    print('=' * 60)

    try:
        conta      = passo_1_conta()
        usuario    = passo_2_usuario(conta)
        gateway    = passo_3_gateway(conta, usuario)
        dispositivos = passo_4_dispositivos(gateway, conta, usuario)
        resumo(conta, usuario, gateway, dispositivos)
    except SystemExit:
        raise
    except Exception as exc:
        erro(f'Erro inesperado: {exc}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
