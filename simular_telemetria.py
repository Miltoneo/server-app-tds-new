#!/usr/bin/env python
"""
Simulador de Telemetria MQTT — TDS New
========================================
Publica mensagens de telemetria simuladas no broker MQTT para o gateway
provisionado em `setup_conta_telemetria.py`.

Uso básico (no servidor):
  python simular_telemetria.py

Opções:
  --broker   HOST         Host do broker MQTT  (padrão: localhost)
  --port     PORT         Porta do broker       (padrão: 1884)
  --user     USER         Usuário MQTT          (padrão: admin)
  --password PASS         Senha MQTT            (padrão: admin)
  --mac      MAC          MAC do gateway        (padrão: 11:22:33:44:55:66)
  --count    N            Número de publicações (padrão: 10)
  --interval SECS         Intervalo em segundos (padrão: 2)
  --batch                 Envia todas de uma vez (sem intervalo)

Exemplos:
  # Enviar 20 leituras, 1 por segundo
  python simular_telemetria.py --count 20 --interval 1

  # Enviar todas de uma vez (modo batch)
  python simular_telemetria.py --count 50 --batch

  # Conectar num broker remoto
  python simular_telemetria.py --broker onkoto.com.br --port 1884
"""

import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone, timedelta


# ---------------------------------------------------------------------------
# Importação opcional do paho-mqtt
# ---------------------------------------------------------------------------
try:
    import paho.mqtt.client as mqtt
    import paho.mqtt.publish as mqtt_publish
except ImportError:
    print('[ERRO] paho-mqtt não instalado. Execute:  pip install paho-mqtt')
    sys.exit(1)


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_BROKER   = 'localhost'
DEFAULT_PORT     = 1884
DEFAULT_USER     = 'admin'
DEFAULT_PASSWORD = 'admin'
DEFAULT_MAC      = '11:22:33:44:55:66'
DEFAULT_COUNT    = 10
DEFAULT_INTERVAL = 2  # segundos

TOPIC_TEMPLATE = 'tds_new/devices/{mac}/telemetry'


# ---------------------------------------------------------------------------
# Gerador de leituras simuladas
# ---------------------------------------------------------------------------

class GeradorLeitura:
    """Simula leituras de sensores com variação realista."""

    def __init__(self):
        # Estado acumulado para simular consumo progressivo
        self._energia    = random.uniform(100.0, 500.0)
        self._agua       = random.uniform(20.0, 100.0)
        self._temperatura_base = random.uniform(18.0, 28.0)

    def proximo(self, timestamp=None):
        """Gera um payload de telemetria com variações aleatórias."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Energia: crescimento cumulativo (+0.1~2.0 kWh por ciclo)
        self._energia += random.uniform(0.1, 2.0)

        # Água: crescimento cumulativo (+0.01~0.5 m³ por ciclo)
        self._agua += random.uniform(0.01, 0.5)

        # Temperatura: oscila em torno do valor base (±3°C)
        temperatura = self._temperatura_base + random.uniform(-3.0, 3.0)

        return {
            'gateway_mac': None,  # preenchido pelo chamador
            'timestamp': timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'leituras': [
                {
                    'dispositivo_codigo': 'D01',
                    'valor': round(self._energia, 3),
                    'unidade': 'kWh',
                },
                {
                    'dispositivo_codigo': 'D02',
                    'valor': round(self._agua, 3),
                    'unidade': 'm³',
                },
                {
                    'dispositivo_codigo': 'D03',
                    'valor': round(temperatura, 2),
                    'unidade': '°C',
                },
            ],
        }


# ---------------------------------------------------------------------------
# Publicação MQTT
# ---------------------------------------------------------------------------

def publicar(broker, port, user, password, topic, payload_dict):
    """Publica uma mensagem no broker e retorna True em caso de sucesso."""
    payload_json = json.dumps(payload_dict, ensure_ascii=False)
    auth = {'username': user, 'password': password} if user else None
    try:
        mqtt_publish.single(
            topic=topic,
            payload=payload_json,
            hostname=broker,
            port=port,
            auth=auth,
            qos=1,
        )
        return True, len(payload_json)
    except Exception as exc:
        return False, str(exc)


# ---------------------------------------------------------------------------
# Relatório final
# ---------------------------------------------------------------------------

def imprimir_relatorio(resultados, mac, broker, port):
    print()
    print('=' * 62)
    print('  RELATÓRIO DE SIMULAÇÃO')
    print('=' * 62)
    sucesso  = sum(1 for r in resultados if r['sucesso'])
    falha    = len(resultados) - sucesso
    bytes_tx = sum(r.get('bytes', 0) for r in resultados if r['sucesso'])

    print(f'  Broker        : {broker}:{port}')
    print(f'  Gateway MAC   : {mac}')
    print(f'  Topic         : {TOPIC_TEMPLATE.format(mac=mac)}')
    print(f'  Total enviado : {len(resultados)}')
    print(f'  Sucesso       : {sucesso}')
    print(f'  Falhas        : {falha}')
    print(f'  Bytes totais  : {bytes_tx} B')

    if resultados:
        primeira = resultados[0]['timestamp']
        ultima   = resultados[-1]['timestamp']
        print(f'  De            : {primeira}')
        print(f'  Até           : {ultima}')

    if falha > 0:
        print()
        print('  ERROS:')
        for r in resultados:
            if not r['sucesso']:
                print(f'    #{r["seq"]:04d}  {r.get("erro", "?")}')

    print('=' * 62)
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description='Simulador de telemetria MQTT para TDS New',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('--broker',   default=DEFAULT_BROKER,   metavar='HOST',
                        help=f'Host do broker MQTT (padrão: {DEFAULT_BROKER})')
    parser.add_argument('--port',     default=DEFAULT_PORT,     type=int, metavar='PORT',
                        help=f'Porta do broker (padrão: {DEFAULT_PORT})')
    parser.add_argument('--user',     default=DEFAULT_USER,     metavar='USER',
                        help=f'Usuário MQTT (padrão: {DEFAULT_USER})')
    parser.add_argument('--password', default=DEFAULT_PASSWORD, metavar='PASS',
                        help=f'Senha MQTT (padrão: {DEFAULT_PASSWORD})')
    parser.add_argument('--mac',      default=DEFAULT_MAC,      metavar='MAC',
                        help=f'MAC do gateway (padrão: {DEFAULT_MAC})')
    parser.add_argument('--count',    default=DEFAULT_COUNT,    type=int, metavar='N',
                        help=f'Número de mensagens a publicar (padrão: {DEFAULT_COUNT})')
    parser.add_argument('--interval', default=DEFAULT_INTERVAL, type=float, metavar='SECS',
                        help=f'Intervalo entre publicações em segundos (padrão: {DEFAULT_INTERVAL})')
    parser.add_argument('--batch',    action='store_true',
                        help='Enviar todas as mensagens de uma vez (sem intervalo)')
    parser.add_argument('--retroativo', type=int, default=0, metavar='HORAS',
                        help='Gerar timestamps retroativos cobrindo N horas no passado')
    return parser.parse_args()


def main():
    args = parse_args()
    topic = TOPIC_TEMPLATE.format(mac=args.mac)

    print()
    print('=' * 62)
    print('  SIMULADOR DE TELEMETRIA — TDS NEW')
    print('=' * 62)
    print(f'  Broker  : {args.broker}:{args.port}')
    print(f'  MAC     : {args.mac}')
    print(f'  Topic   : {topic}')
    print(f'  Mensagens: {args.count}')
    if args.retroativo:
        print(f'  Modo    : retroativo ({args.retroativo}h no passado)')
    elif args.batch:
        print(f'  Modo    : batch (sem intervalo)')
    else:
        print(f'  Intervalo: {args.interval}s')
    print()

    # Calcular timestamps retroativos se solicitado
    if args.retroativo > 0:
        inicio = datetime.now(timezone.utc) - timedelta(hours=args.retroativo)
        intervalo_total = timedelta(hours=args.retroativo)
        delta = intervalo_total / args.count
        timestamps = [inicio + delta * i for i in range(args.count)]
    else:
        timestamps = [None] * args.count  # usa datetime.now()

    gerador   = GeradorLeitura()
    resultados = []

    for i, ts in enumerate(timestamps, start=1):
        payload = gerador.proximo(timestamp=ts)
        payload['gateway_mac'] = args.mac

        ts_display = ts.strftime('%Y-%m-%dT%H:%M:%SZ') if ts else 'now'
        print(f'  [{i:04d}/{args.count:04d}]  ts={ts_display}  ', end='', flush=True)

        ok, info = publicar(
            broker=args.broker,
            port=args.port,
            user=args.user,
            password=args.password,
            topic=topic,
            payload_dict=payload,
        )

        resultado = {
            'seq':       i,
            'sucesso':   ok,
            'timestamp': payload['timestamp'],
        }
        if ok:
            resultado['bytes'] = info
            print(f'OK  ({info}B)')
        else:
            resultado['erro'] = info
            print(f'FALHA  — {info}')

        resultados.append(resultado)

        # Aguardar intervalo (exceto na última mensagem ou modo batch)
        if not args.batch and i < args.count:
            time.sleep(args.interval)

    imprimir_relatorio(resultados, args.mac, args.broker, args.port)

    falhas = sum(1 for r in resultados if not r['sucesso'])
    sys.exit(1 if falhas == args.count else 0)


if __name__ == '__main__':
    main()
