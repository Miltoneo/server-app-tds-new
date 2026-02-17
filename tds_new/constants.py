# -*- coding: utf-8 -*-
"""
Constantes do sistema TDS New
Centraliza valores fixos utilizados em múltiplos pontos do código
para facilitar manutenção e garantir consistência.

Criado em: 14/02/2026
"""


class Cenarios:
    """
    Constantes para configuração de cenários do sistema.
    Cada cenário define menu_nome, cenario_nome e titulo_pagina padrão.
    """
    
    HOME = {
        'menu_nome': 'Home',
        'cenario_nome': 'Home',
        'titulo_pagina': 'Dashboard Principal'
    }
    
    DISPOSITIVOS = {
        'menu_nome': 'Gateways',
        'cenario_nome': 'Gateways',
        'titulo_pagina': 'Gerenciamento de Gateways'
    }
    
    TELEMETRIA = {
        'menu_nome': 'Telemetria',
        'cenario_nome': 'Telemetria',
        'titulo_pagina': 'Monitoramento em Tempo Real'
    }
    
    ALERTAS = {
        'menu_nome': 'Alertas',
        'cenario_nome': 'Alertas',
        'titulo_pagina': 'Central de Alertas'
    }
    
    RELATORIOS = {
        'menu_nome': 'Relatórios',
        'cenario_nome': 'Relatórios',
        'titulo_pagina': 'Relatórios e Análises'
    }
    
    CONFIGURACOES = {
        'menu_nome': 'Configurações',
        'cenario_nome': 'Configurações',
        'titulo_pagina': 'Configurações do Sistema'
    }
    
    CONTA = {
        'menu_nome': 'Conta',
        'cenario_nome': 'Conta',
        'titulo_pagina': 'Gerenciamento da Conta'
    }
    
    USUARIOS = {
        'menu_nome': 'Usuários',
        'cenario_nome': 'Usuários',
        'titulo_pagina': 'Gerenciamento de Usuários'
    }
    
    # 🆕 Week 8: Cenário administrativo do sistema
    ADMIN_SISTEMA = {
        'menu_nome': 'Admin Sistema',
        'cenario_nome': 'Admin Sistema',
        'titulo_pagina': 'Administração do Sistema TDS'
    }


class StatusDispositivo:
    """
    Status possíveis para dispositivos IoT
    """
    ATIVO = 'ativo'
    INATIVO = 'inativo'
    MANUTENCAO = 'manutencao'
    ERRO = 'erro'
    
    CHOICES = [
        (ATIVO, 'Ativo'),
        (INATIVO, 'Inativo'),
        (MANUTENCAO, 'Em Manutenção'),
        (ERRO, 'Erro'),
    ]


class TipoAlerta:
    """
    Tipos de alertas do sistema
    """
    INFO = 'info'
    WARNING = 'warning'
    CRITICAL = 'critical'
    
    CHOICES = [
        (INFO, 'Informação'),
        (WARNING, 'Aviso'),
        (CRITICAL, 'Crítico'),
    ]


class Permissoes:
    """
    Níveis de permissão baseados em ContaMembership.role
    """
    ADMIN = 'admin'
    EDITOR = 'editor'
    VIEWER = 'viewer'
    SUPER_ADMIN = 'super_admin'  # 🆕 Week 8: Administrador do sistema
    
    CHOICES = [
        (ADMIN, 'Administrador'),
        (EDITOR, 'Editor'),
        (VIEWER, 'Visualizador'),
        (SUPER_ADMIN, 'Super Admin'),  # 🆕 Week 8
    ]
