"""
Facades - Interfaces simplificadas para subsistemas complexos

Este pacote contém facades que proporcionam interfaces simplificadas
para subsistemas complexos da aplicação.

Objetivos:
- Facade Pattern para interfaces simplificadas
- Reduzir acoplamento entre componentes
- Encapsular complexidade de subsistemas
"""

from consumo_lib.facades.hardware_connection_facade import HardwareConnectionFacade
from consumo_lib.facades.position_manager_facade import PositionManagerFacade
from consumo_lib.facades.authentication_manager import AuthenticationManager

__all__ = [
    'HardwareConnectionFacade',
    'PositionManagerFacade',
    'AuthenticationManager',
]
