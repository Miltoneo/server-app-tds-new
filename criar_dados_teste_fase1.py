"""
Script para criar Gateways e Dispositivos de teste
Demonstra funcionalidade completa do CRUD implementado na Fase 1
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from tds_new.models.base import Conta
from tds_new.models.dispositivos import Gateway, Dispositivo
from decimal import Decimal

print("\n" + "="*70)
print("CRIANDO DADOS DE TESTE - FASE 1: CRUD DE DISPOSITIVOS")
print("="*70)

# Buscar conta de teste
conta = Conta.objects.first()
if not conta:
    print("❌ Nenhuma conta encontrada! Execute criar_conta_teste.py primeiro.")
    exit(1)

print(f"\n✅ Conta: {conta.name} (ID: {conta.id})")

# Criar Gateways
print("\n" + "="*70)
print("CRIANDO GATEWAYS DE TESTE")
print("="*70)

gateways_data = [
    {
        'codigo': 'GW001',
        'mac': 'aa:bb:cc:dd:ee:01',
        'nome': 'Gateway Sede Principal',
        'descricao': 'Gateway principal instalado na sede da empresa',
        'latitude': Decimal('-23.550520'),
        'longitude': Decimal('-46.633308'),
        'qte_max_dispositivos': 8,
    },
    {
        'codigo': 'GW002',
        'mac': 'aa:bb:cc:dd:ee:02',
        'nome': 'Gateway Filial Norte',
        'descricao': 'Gateway instalado na filial da zona norte',
        'latitude': Decimal('-23.520000'),
        'longitude': Decimal('-46.620000'),
        'qte_max_dispositivos': 6,
    },
]

for gw_data in gateways_data:
    gw, created = Gateway.objects.get_or_create(
        conta=conta,
        codigo=gw_data['codigo'],
        defaults=gw_data
    )
    if created:
        print(f"   ✅ Criado: {gw.codigo} - {gw.nome}")
    else:
        print(f"   ⚠️  Já existe: {gw.codigo} - {gw.nome}")

# Criar Dispositivos
print("\n" + "="*70)
print("CRIANDO DISPOSITIVOS DE TESTE")
print("="*70)

dispositivos_data = [
    # Dispositivos no Gateway 1
    {
        'gateway_codigo': 'GW001',
        'codigo': 'D01',
        'nome': 'Medidor de Água - Entrada',
        'descricao': 'Medidor principal de entrada de água',
        'tipo': 'MEDIDOR',
        'slave_id': 1,
        'register_modbus': 1000,
        'val_alarme_dia': Decimal('500.0000'),
    },
    {
        'gateway_codigo': 'GW001',
        'codigo': 'D02',
        'nome': 'Medidor de Energia - Quadro Geral',
        'descricao': 'Medidor de consumo de energia elétrica',
        'tipo': 'MEDIDOR',
        'slave_id': 2,
        'register_modbus': 2000,
        'val_alarme_dia': Decimal('1000.0000'),
    },
    {
        'gateway_codigo': 'GW001',
        'codigo': 'D03',
        'nome': 'Sensor de Temperatura - Sala Servidores',
        'descricao': 'Sensor de temperatura ambiente',
        'tipo': 'SENSOR',
        'val_alarme_dia': Decimal('30.0000'),  # 30°C
    },
    
    # Dispositivos no Gateway 2
    {
        'gateway_codigo': 'GW002',
        'codigo': 'D01',
        'nome': 'Medidor de Água - Filial Norte',
        'descricao': 'Medidor de água da filial',
        'tipo': 'MEDIDOR',
        'slave_id': 1,
        'register_modbus': 1000,
    },
    {
        'gateway_codigo': 'GW002',
        'codigo': 'D02',
        'nome': 'Sensor de Umidade - Depósito',
        'descricao': 'Sensor de umidade relativa do ar',
        'tipo': 'SENSOR',
    },
]

for disp_data in dispositivos_data:
    gateway_codigo = disp_data.pop('gateway_codigo')
    gateway = Gateway.objects.get(conta=conta, codigo=gateway_codigo)
    
    disp, created = Dispositivo.objects.get_or_create(
        conta=conta,
        gateway=gateway,
        codigo=disp_data['codigo'],
        defaults=disp_data
    )
    if created:
        print(f"   ✅ Criado: {gateway.codigo}/{disp.codigo} - {disp.nome}")
    else:
        print(f"   ⚠️  Já existe: {gateway.codigo}/{disp.codigo} - {disp.nome}")

# Estatísticas finais
print("\n" + "="*70)
print("RESUMO ESTATÍSTICO")
print("="*70)

gateways = Gateway.objects.filter(conta=conta)
dispositivos = Dispositivo.objects.filter(conta=conta)

print(f"\n📊 Total de Gateways: {gateways.count()}")
for gw in gateways:
    print(f"   🔹 {gw.codigo}: {gw.dispositivos_count}/{gw.qte_max_dispositivos} dispositivos ({gw.percentual_uso:.1f}%)")

print(f"\n📊 Total de Dispositivos: {dispositivos.count()}")
medidores = dispositivos.filter(tipo='MEDIDOR').count()
sensores = dispositivos.filter(tipo='SENSOR').count()
print(f"   🔹 Medidores: {medidores}")
print(f"   🔹 Sensores: {sensores}")

print("\n" + "="*70)
print("✅ DADOS DE TESTE CRIADOS COM SUCESSO!")
print("="*70)
print("\nAcesse o sistema:")
print("   🌐 URL: http://127.0.0.1:8000/tds_new/auth/login/")
print("   👤 Email: miltoneo@gmail.com")
print("   🔑 Senha: *Mil031212")
print("\nNavegação:")
print("   1. Faça login")
print("   2. No sidebar, clique em 'Dispositivos'")
print("   3. Você verá a lista de Gateways criados")
print("   4. Clique em um Gateway para ver seus dispositivos")
print("   5. Teste criar, editar e excluir gateways/dispositivos")
print("\n✨ Funcionalidades testáveis:")
print("   ✅ Listagem de Gateways com paginação e filtros")
print("   ✅ Criação de Gateway com validação de MAC único")
print("   ✅ Edição de Gateway")
print("   ✅ Exclusão de Gateway (verifica dispositivos vinculados)")
print("   ✅ Listagem de Dispositivos por Gateway")
print("   ✅ Criação de Dispositivo (valida capacidade do Gateway)")
print("   ✅ Validação condicional (MEDIDOR exige slave_id e register_modbus)")
print("   ✅ Edição e exclusão de Dispositivos")
print("   ✅ Barra de progresso de capacidade do Gateway")
print("="*70)
