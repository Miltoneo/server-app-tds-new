"""
Views de Telemetria - TDS New
Dashboard em tempo real para visualização de telemetria IoT.

Fase 4 - MVP Mínimo
Criado em: 18/02/2026
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Max, Avg, Count
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json

from ..models import LeituraDispositivo, Dispositivo, Gateway
from ..constants import Cenarios

import logging
logger = logging.getLogger(__name__)


@login_required
def telemetria_dashboard(request):
    """
    Dashboard principal de telemetria em tempo real
    
    Exibe:
    - Widgets de resumo (total de leituras, dispositivos ativos, última atualização)
    - Gráfico de linha: Consumo ao longo do tempo (últimas 24h)
    - Gráfico de barras: Consumo por dispositivo (hoje)
    - Tabela: Últimas 10 leituras
    
    Filtros:
    - Data (hoje, últimos 7 dias, últimos 30 dias, personalizado)
    - Dispositivo (dropdown multi-select)
    - Tipo de grandeza (kWh, m³, °C, etc.)
    
    Integração:
    - AJAX polling a cada 30s para atualização automática
    - Chart.js para gráficos interativos
    """
    # Configurar título via sessão
    request.session['titulo_pagina'] = Cenarios.TELEMETRIA['titulo_pagina']
    request.session.modified = True
    
    # Obter conta_id da sessão (multi-tenant enforcement via middleware)
    conta_id = request.session.get('conta_ativa_id')  # Nome correto do campo de sessão
    
    if not conta_id:
        logger.error("conta_ativa_id não encontrado na sessão")
        return render(request, 'tds_new/telemetria_dashboard.html', {
            'error': 'Conta não selecionada. Por favor, selecione uma conta antes de continuar.',
            'redirect_url': '/tds_new/auth/select-account/'
        })
    
    # Filtros da request
    periodo = request.GET.get('periodo', '24h')  # '24h', '7d', '30d', 'custom'
    dispositivo_ids = request.GET.getlist('dispositivos')  # Lista de IDs
    
    # Calcular range de datas baseado no período
    now = timezone.now()
    if periodo == '24h':
        data_inicio = now - timedelta(hours=24)
    elif periodo == '7d':
        data_inicio = now - timedelta(days=7)
    elif periodo == '30d':
        data_inicio = now - timedelta(days=30)
    else:
        # Custom - usar parâmetros de data
        data_inicio_str = request.GET.get('data_inicio')
        if data_inicio_str:
            from datetime import datetime
            data_inicio = timezone.make_aware(datetime.fromisoformat(data_inicio_str))
        else:
            data_inicio = now - timedelta(hours=24)
    
    # Query base: leituras da conta no período
    leituras_queryset = LeituraDispositivo.objects.filter(
        conta_id=conta_id,
        time__gte=data_inicio
    ).select_related('dispositivo')
    
    # Filtro por dispositivos (se selecionado)
    if dispositivo_ids:
        leituras_queryset = leituras_queryset.filter(dispositivo_id__in=dispositivo_ids)
    
    # Métricas de resumo
    total_leituras = leituras_queryset.count()
    
    # Dispositivos com leituras no período (ativos)
    dispositivos_ativos = leituras_queryset.values('dispositivo_id').distinct().count()
    
    # Última leitura (timestamp)
    ultima_leitura_obj = leituras_queryset.order_by('-time').first()
    ultima_atualizacao = ultima_leitura_obj.time if ultima_leitura_obj else None
    
    # Gateway online count
    gateways_online = Gateway.objects.filter(
        conta_id=conta_id,
        is_online=True
    ).count()
    
    # Últimas 10 leituras para tabela
    ultimas_leituras = leituras_queryset.order_by('-time')[:10].values(
        'time',
        'dispositivo__codigo',
        'dispositivo__nome',
        'valor',
        'unidade'
    )
    
    # Converter para lista para template
    ultimas_leituras_list = list(ultimas_leituras)
    
    # Todos os dispositivos da conta (para dropdown de filtro)
    todos_dispositivos = Dispositivo.objects.filter(
        conta_id=conta_id
    ).values('id', 'codigo', 'nome', 'tipo')
    
    context = {
        'total_leituras': total_leituras,
        'dispositivos_ativos': dispositivos_ativos,
        'ultima_atualizacao': ultima_atualizacao,
        'gateways_online': gateways_online,
        'ultimas_leituras': ultimas_leituras_list,
        'todos_dispositivos': list(todos_dispositivos),
        'periodo_selecionado': periodo,
        'dispositivos_selecionados': dispositivo_ids,
    }
    
    return render(request, 'tds_new/telemetria_dashboard.html', context)


@login_required
def telemetria_api_grafico_timeline(request):
    """
    API AJAX: Dados para gráfico de linha (timeline)
    
    Retorna JSON com série temporal de consumo agrupado por hora.
    
    Formato:
    {
        "labels": ["2026-02-18 00:00", "2026-02-18 01:00", ...],
        "datasets": [
            {
                "label": "D01 - Medidor de Energia",
                "data": [123.45, 130.20, ...],
                "borderColor": "#FF6384",
                "fill": false
            },
            ...
        ]
    }
    """
    conta_id = request.session.get('conta_ativa_id')
    if not conta_id:
        return JsonResponse({'error': 'Sessão inválida'}, status=401)
    
    # Filtros
    periodo = request.GET.get('periodo', '24h')
    dispositivo_ids = request.GET.getlist('dispositivos')
    
    # Calcular range de datas
    now = timezone.now()
    if periodo == '24h':
        data_inicio = now - timedelta(hours=24)
        intervalo_horas = 1
    elif periodo == '7d':
        data_inicio = now - timedelta(days=7)
        intervalo_horas = 6  # Agrupar por 6 horas
    elif periodo == '30d':
        data_inicio = now - timedelta(days=30)
        intervalo_horas = 24  # Agrupar por dia
    else:
        data_inicio = now - timedelta(hours=24)
        intervalo_horas = 1
    
    # Query base
    leituras_queryset = LeituraDispositivo.objects.filter(
        conta_id=conta_id,
        time__gte=data_inicio
    ).select_related('dispositivo')
    
    if dispositivo_ids:
        leituras_queryset = leituras_queryset.filter(dispositivo_id__in=dispositivo_ids)
    
    # Agrupar por dispositivo e hora
    from django.db.models.functions import TruncHour
    from collections import defaultdict
    
    # Truncar timestamp para hora
    leituras_agrupadas = leituras_queryset.annotate(
        hora=TruncHour('time')
    ).values('hora', 'dispositivo__codigo', 'dispositivo__nome').annotate(
        valor_medio=Avg('valor')
    ).order_by('hora', 'dispositivo__codigo')
    
    # Estruturar dados para Chart.js
    series_por_dispositivo = defaultdict(lambda: {'label': '', 'data': [], 'horas': []})
    
    for registro in leituras_agrupadas:
        codigo = registro['dispositivo__codigo']
        nome = registro['dispositivo__nome']
        hora = registro['hora']
        valor = float(registro['valor_medio'])
        
        if not series_por_dispositivo[codigo]['label']:
            series_por_dispositivo[codigo]['label'] = f"{codigo} - {nome}"
        
        series_por_dispositivo[codigo]['horas'].append(hora.isoformat())
        series_por_dispositivo[codigo]['data'].append(round(valor, 2))
    
    # Gerar labels únicos (todas as horas)
    todas_horas = sorted(set(
        h for serie in series_por_dispositivo.values() for h in serie['horas']
    ))
    
    # Datasets formatados para Chart.js
    cores = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
    datasets = []
    
    for idx, (codigo, serie) in enumerate(series_por_dispositivo.items()):
        # Preencher valores ausentes com None (para gaps no gráfico)
        data_completa = []
        for hora in todas_horas:
            try:
                pos = serie['horas'].index(hora)
                data_completa.append(serie['data'][pos])
            except ValueError:
                data_completa.append(None)  # Gap
        
        datasets.append({
            'label': serie['label'],
            'data': data_completa,
            'borderColor': cores[idx % len(cores)],
            'backgroundColor': cores[idx % len(cores)] + '33',  # 20% opacity
            'fill': False,
            'tension': 0.4  # Curva suave
        })
    
    return JsonResponse({
        'labels': todas_horas,
        'datasets': datasets
    })


@login_required
def telemetria_api_grafico_barras(request):
    """
    API AJAX: Dados para gráfico de barras (consumo por dispositivo)
    
    Agrupa consumo total por dispositivo no período selecionado.
    
    Formato:
    {
        "labels": ["D01", "D02", "D03"],
        "datasets": [{
            "label": "Consumo Total",
            "data": [617.25, 339.45, 112.50],
            "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56"]
        }]
    }
    """
    conta_id = request.session.get('conta_ativa_id')
    if not conta_id:
        return JsonResponse({'error': 'Sessão inválida'}, status=401)
    
    # Filtros
    periodo = request.GET.get('periodo', '24h')
    dispositivo_ids = request.GET.getlist('dispositivos')
    
    # Calcular range de datas
    now = timezone.now()
    if periodo == '24h':
        data_inicio = now - timedelta(hours=24)
    elif periodo == '7d':
        data_inicio = now - timedelta(days=7)
    elif periodo == '30d':
        data_inicio = now - timedelta(days=30)
    else:
        data_inicio = now - timedelta(hours=24)
    
    # Query
    from django.db.models import Sum
    consumo_por_dispositivo = LeituraDispositivo.objects.filter(
        conta_id=conta_id,
        time__gte=data_inicio
    ).values(
        'dispositivo__codigo',
        'dispositivo__nome',
        'unidade'
    ).annotate(
        total=Sum('valor')
    ).order_by('-total')
    
    if dispositivo_ids:
        consumo_por_dispositivo = consumo_por_dispositivo.filter(dispositivo_id__in=dispositivo_ids)
    
    # Estruturar dados
    labels = []
    data = []
    cores = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
    backgrounds = []
    
    for idx, registro in enumerate(consumo_por_dispositivo):
        codigo = registro['dispositivo__codigo']
        nome = registro['dispositivo__nome']
        total = float(registro['total'])
        unidade = registro['unidade']
        
        labels.append(f"{codigo}")
        data.append(round(total, 2))
        backgrounds.append(cores[idx % len(cores)])
    
    return JsonResponse({
        'labels': labels,
        'datasets': [{
            'label': 'Consumo Total',
            'data': data,
            'backgroundColor': backgrounds
        }]
    })


@login_required
def telemetria_api_ultimas_leituras(request):
    """
    API AJAX: Últimas 10 leituras (para atualização da tabela)
    
    Formato:
    {
        "leituras": [
            {
                "time": "2026-02-18T12:47:08+00:00",
                "dispositivo": "D01",
                "nome": "Medidor de Energia",
                "valor": 123.45,
                "unidade": "kWh"
            },
            ...
        ],
        "timestamp": "2026-02-18T12:50:00+00:00"
    }
    """
    conta_id = request.session.get('conta_ativa_id')
    if not conta_id:
        return JsonResponse({'error': 'Sessão inválida'}, status=401)
    
    # Filtros
    dispositivo_ids = request.GET.getlist('dispositivos')
    
    # Query
    queryset = LeituraDispositivo.objects.filter(conta_id=conta_id)
    
    if dispositivo_ids:
        queryset = queryset.filter(dispositivo_id__in=dispositivo_ids)
    
    ultimas = queryset.order_by('-time')[:10].values(
        'time',
        'dispositivo__codigo',
        'dispositivo__nome',
        'valor',
        'unidade'
    )
    
    leituras_list = []
    for leitura in ultimas:
        leituras_list.append({
            'time': leitura['time'].isoformat(),
            'dispositivo': leitura['dispositivo__codigo'],
            'nome': leitura['dispositivo__nome'],
            'valor': float(leitura['valor']),
            'unidade': leitura['unidade']
        })
    
    return JsonResponse({
        'leituras': leituras_list,
        'timestamp': timezone.now().isoformat()
    })
