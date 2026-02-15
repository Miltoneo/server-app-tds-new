"""
Views do Dashboard - TDS New
Dashboard principal do sistema.

Criado em: 14/02/2026
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..constants import Cenarios


@login_required
def dashboard_view(request):
    """
    Dashboard principal do sistema TDS New
    
    Exibe:
    - Resumo de dispositivos IoT
    - Últimas leituras de telemetria
    - Alertas pendentes
    - Gráficos de monitoramento
    
    TODO (Week 6-7):
    - Implementar estatísticas reais de dispositivos
    - Adicionar widgets de telemetria
    - Gráficos com Chart.js ou ApexCharts
    """
    # Configura título da página
    request.session['titulo_pagina'] = Cenarios.HOME['titulo_pagina']
    request.session.modified = True
    
    # Dados mockados para Week 4-5
    context = {
        'total_dispositivos': 0,
        'dispositivos_ativos': 0,
        'alertas_pendentes': 0,
        'ultima_leitura': None,
    }
    
    return render(request, 'tds_new/dashboard.html', context)
