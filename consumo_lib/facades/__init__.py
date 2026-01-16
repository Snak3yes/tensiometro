"""
Facades - Interfaces simplificadas para subsistemas complexos

Este pacote contém facades que proporcionam interfaces simplificadas
para subsistemas complexos da aplicação.

Objetivos:
- Facade Pattern para interfaces simplificadas
- Reduzir acoplamento entre componentes
- Encapsular complexidade de subsistemas

Facades da Fase 4 (Hardware):
- HardwareConnectionFacade: Simplifica conexões de hardware
- PositionManagerFacade: Simplifica gerenciamento de posições
- AuthenticationManager: Simplifica autenticação e permissões

Facades da Fase 8 (Configuration):
- ConfigurationFacade: Abstrai acesso a configurações
"""

# Facades da Fase 4
from consumo_lib.facades.hardware_connection_facade import HardwareConnectionFacade
from consumo_lib.facades.position_manager_facade import PositionManagerFacade
from consumo_lib.facades.authentication_manager import AuthenticationManager

# Facade da Fase 8
from consumo_lib.facades.configuration_facade import ConfigurationFacade

__all__ = [
    # Fase 4
    'HardwareConnectionFacade',
    'PositionManagerFacade',
    'AuthenticationManager',
    # Fase 8
    'ConfigurationFacade',
]
