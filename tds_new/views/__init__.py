"""
Views do aplicativo TDS New
Exporta todas as views para facilitar imports
"""

from .cenario import (
    cenario_home,
    cenario_dispositivos,
    cenario_telemetria,
    cenario_alertas,
    cenario_relatorios,
    cenario_configuracoes,
    cenario_conta,
    cenario_usuarios,
)

from .auth import (
    login_view,
    logout_view,
    select_account_view,
    license_expired_view,
)

from .dashboard import (
    dashboard_view,
)

__all__ = [
    # Cenários
    'cenario_home',
    'cenario_dispositivos',
    'cenario_telemetria',
    'cenario_alertas',
    'cenario_relatorios',
    'cenario_configuracoes',
    'cenario_conta',
    'cenario_usuarios',
    
    # Autenticação
    'login_view',
    'logout_view',
    'select_account_view',
    'license_expired_view',
    
    # Dashboard
    'dashboard_view',
]
