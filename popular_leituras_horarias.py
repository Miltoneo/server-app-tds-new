import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_tds_new.settings')
django.setup()

from tds_new.models import LeituraDispositivo, Dispositivo, Gateway, Conta
from datetime import datetime, timedelta
import pytz
from decimal import Decimal

# Configurar timezone
tz_brasilia = pytz.timezone('America/Sao_Paulo')

# Buscar entidades
conta = Conta.objects.get(id=2)
gateway = Gateway.objects.get(conta=conta, codigo='GW-TEST-001')
dispositivos = {
    'D01': Dispositivo.objects.get(conta=conta, codigo='D01'),
    'D02': Dispositivo.objects.get(conta=conta, codigo='D02'),
    'D03': Dispositivo.objects.get(conta=conta, codigo='D03'),
}

# Definir dados base por dispositivo
dados_base = {
    'D01': {'unidade': 'kWh', 'valor_base': 120.0, 'incremento': 5.0},
    'D02': {'unidade': 'm³', 'valor_base': 65.0, 'incremento': 2.5},
    'D03': {'unidade': '°C', 'valor_base': 20.0, 'incremento': 1.5},
}

# Gerar leituras de 09:00 até 15:00 (última hora = agora)
agora = datetime.now(tz_brasilia)
hora_inicial = agora.replace(hour=9, minute=0, second=0, microsecond=0)
hora_final = agora.replace(hour=15, minute=0, second=0, microsecond=0)

print(f"=== POPULAR LEITURAS HORÁRIAS ===\n")
print(f"Período: {hora_inicial.strftime('%d/%m %H:%M')} até {hora_final.strftime('%d/%m %H:%M')}")
print(f"Dispositivos: {list(dados_base.keys())}\n")

# Apagar leituras existentes do período
LeituraDispositivo.objects.filter(
    conta=conta,
    time__gte=hora_inicial,
    time__lte=hora_final
).delete()
print("✓ Leituras antigas removidas\n")

leituras_criadas = 0
hora_atual = hora_inicial

while hora_atual <= hora_final:
    print(f"Criando leituras para {hora_atual.strftime('%d/%m %H:00')}...")
    
    for codigo, dispositivo in dispositivos.items():
        config = dados_base[codigo]
        
        # Calcular valor com variação horária
        horas_decorridas = (hora_atual - hora_inicial).total_seconds() / 3600
        valor = config['valor_base'] + (config['incremento'] * horas_decorridas)
        
        # Adicionar pequena variação aleatória
        import random
        valor += random.uniform(-0.5, 0.5)
        
        # Criar leitura
        leitura = LeituraDispositivo.objects.create(
            conta=conta,
            gateway=gateway,
            dispositivo=dispositivo,
            time=hora_atual,
            unidade=config['unidade'],
            valor=Decimal(str(round(valor, 2))),
            payload_raw={'test': 'data'}
        )
        leituras_criadas += 1
        print(f"  {codigo} | {config['unidade']}: {leitura.valor}")
    
    print()
    hora_atual += timedelta(hours=1)

print(f"=== CONCLUÍDO ===")
print(f"Total de leituras criadas: {leituras_criadas}")
print(f"Horas populadas: {int((hora_final - hora_inicial).total_seconds() / 3600) + 1}")
print(f"\nAgora o gráfico terá grid vertical a cada hora de {hora_inicial.strftime('%H:00')} até {hora_final.strftime('%H:00')}")
