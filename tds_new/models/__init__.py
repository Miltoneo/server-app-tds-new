"""
Pacote de modelos do TDS New

Estrutura:
- base.py: Modelos base (CustomUser, Conta, ContaMembership)
- dispositivos.py: Modelos de dispositivos IoT (TipoDispositivo, Coletor, Device)
- leituras.py: Modelos de leituras e telemetria (Leitura, LeituraAgregada)
"""

# Importa modelos base (Semana 2)
from .base import (
    CustomUser,
    Conta,
    ContaMembership,
    SaaSBaseModel,
    BaseTimestampMixin,
    BaseCreatedByMixin,
    BaseAuditMixin,
    ContaScopedManager,
)

# Expor modelos no namespace do módulo
__all__ = [
    # Modelos principais
    'CustomUser',
    'Conta',
    'ContaMembership',
    
    # Modelos base abstratos
    'SaaSBaseModel',
    
    # Mixins
    'BaseTimestampMixin',
    'BaseCreatedByMixin',
    'BaseAuditMixin',
    
    # Managers
    'ContaScopedManager',
]

# TODO: Implementar dispositivos e leituras (Semanas 4-6)
# from .dispositivos import TipoDispositivo, Coletor, Device
# from .leituras import Leitura, LeituraAgregada

