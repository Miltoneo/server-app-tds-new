"""
Pacote de modelos do TDS New

Estrutura:
- base.py: Modelos base (CustomUser, Conta, ContaMembership, SaaSBaseModel)
- dispositivos.py: Modelos de dispositivos IoT (Gateway, Dispositivo)
- telemetria.py: Modelos de leituras e telemetria (LeituraDispositivo, ConsumoMensal)
- certificados.py: Modelos de certificados X.509 (CertificadoDevice)
"""

# Importa modelos base (Week 2)
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

# Importa modelos de dispositivos IoT (Week 6-7)
from .dispositivos import (
    Gateway,
    Dispositivo,
)

# Importa modelos de telemetria (Week 6-7)
from .telemetria import (
    LeituraDispositivo,
    ConsumoMensal,
)

# Importa modelos de certificados (Week 6-7)
from .certificados import (
    CertificadoDevice,
    BootstrapCertificate,
    RegistroProvisionamento,
)

# Expor modelos no namespace do módulo
__all__ = [
    # Modelos base
    'CustomUser',
    'Conta',
    'ContaMembership',
    'SaaSBaseModel',
    
    # Modelos IoT
    'Gateway',
    'Dispositivo',
    'LeituraDispositivo',
    'ConsumoMensal',
    'CertificadoDevice',
    'BootstrapCertificate',
    'RegistroProvisionamento',
    
    # Mixins
    'BaseTimestampMixin',
    'BaseCreatedByMixin',
    'BaseAuditMixin',
    
    # Managers
    'ContaScopedManager',
]

