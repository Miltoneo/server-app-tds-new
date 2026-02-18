"""
Views de Cenários - TDS New
Centraliza a configuração de contexto e roteamento dos diferentes módulos do sistema.

Padrão arquitetural:
- Cada cenário configura variáveis de sessão (menu_nome, cenario_nome, titulo_pagina)
- Redireciona para a tela inicial padrão do módulo
- Garante isolamento multi-tenant via middleware

Criado em: 14/02/2026
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages
from ..constants import Cenarios
import logging

logger = logging.getLogger(__name__)


def _configurar_cenario(request, cenario_config):
    """
    Helper para configurar variáveis de sessão do cenário.
    
    Args:
        request: HttpRequest
        cenario_config: Dict com menu_nome, cenario_nome, titulo_pagina
        
    Uso:
        _configurar_cenario(request, Cenarios.HOME)
    """
    for key, value in cenario_config.items():
        request.session[key] = value
    
    # Log para debug (apenas em desenvolvimento)
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Cenário configurado: {cenario_config.get('cenario_nome')}")
    
    request.session.modified = True


@login_required
def cenario_home(request):
    """
    Cenário inicial/dashboard principal
    """
    _configurar_cenario(request, Cenarios.HOME)
    return redirect('tds_new:dashboard')


@login_required
def cenario_dispositivos(request):
    """
    Cenário de gerenciamento de gateways e dispositivos IoT - Week 6-7 IMPLEMENTADO
    Redireciona para lista de gateways (tela inicial do módulo)
    """
    _configurar_cenario(request, Cenarios.DISPOSITIVOS)
    return redirect('tds_new:gateway_list')


@login_required
def cenario_telemetria(request):
    """
    Cenário de monitoramento de telemetria (dispositivos IoT)
    Redireciona para dashboard de telemetria em tempo real
    """
    _configurar_cenario(request, Cenarios.TELEMETRIA)
    return redirect('tds_new:telemetria_dashboard')


@login_required
def cenario_alertas(request):
    """
    Cenário de central de alertas
    TODO: Implementar na Week 8-9
    """
    _configurar_cenario(request, Cenarios.ALERTAS)
    messages.info(request, 'Módulo de Alertas será implementado na Week 8-9.')
    return redirect('tds_new:dashboard')


@login_required
def cenario_relatorios(request):
    """
    Cenário de relatórios e análises
    TODO: Implementar na Week 10
    """
    _configurar_cenario(request, Cenarios.RELATORIOS)
    messages.info(request, 'Módulo de Relatórios será implementado na Week 10.')
    return redirect('tds_new:dashboard')


@login_required
def cenario_configuracoes(request):
    """
    Cenário de configurações do sistema
    TODO: Implementar na Week 11
    """
    _configurar_cenario(request, Cenarios.CONFIGURACOES)
    messages.info(request, 'Módulo de Configurações será implementado na Week 11.')
    return redirect('tds_new:dashboard')


@login_required
def cenario_conta(request):
    """
    Cenário de gerenciamento da conta (tenant)
    """
    _configurar_cenario(request, Cenarios.CONTA)
    # TODO: Implementar gestão de conta
    messages.info(request, 'Módulo de Conta será implementado na Week 11.')
    return redirect('tds_new:dashboard')


@login_required
def cenario_usuarios(request):
    """
    Cenário de gerenciamento de usuários (admin only)
    """
    _configurar_cenario(request, Cenarios.USUARIOS)
    # TODO: Implementar gestão de usuários
    messages.info(request, 'Módulo de Usuários será implementado na Week 11.')
    return redirect('tds_new:dashboard')
