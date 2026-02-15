"""
Forms do aplicativo TDS New
Exporta todos os formulários para facilitar imports
"""

from .gateway import (
    GatewayForm,
    GatewayFilterForm,
)

from .dispositivo import (
    DispositivoForm,
    DispositivoFilterForm,
)

__all__ = [
    # Gateway
    'GatewayForm',
    'GatewayFilterForm',
    
    # Dispositivo
    'DispositivoForm',
    'DispositivoFilterForm',
]
